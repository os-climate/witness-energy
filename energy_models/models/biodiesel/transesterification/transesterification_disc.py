'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import logging

import numpy as np

from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.techno_type.disciplines.biodiesel_techno_disc import (
    BioDieselTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.biodiesel.transesterification.transesterification import (
    Transesterification,
)


class TransesterificationDiscipline(BioDieselTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Transesterification Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.Transesterification
    energy_name = BioDiesel.name

    # use biodiesel calorific value to compute co2 from production

    # Beer, T., Grant, T., Morgan, G., Lapszewicz, J., Anyon, P., Edwards, J., Nelson, P., Watson, H. and Williams, D., 2001.
    # Comparison of transport fuels. FINAL REPORT (EV45A/2/F3C) to the Australian Greenhouse Office on the stage, 2.
    # Pre-combustion CO2 emissions for soybean = 0.03 kgCO2/MJ * 3.6 MJ/kWh =
    # 0.11 kgCO2/kWh
    co2_from_production = (6.7 / 1000) * BioDiesel.data_energy_dict['calorific_value']
    techno_infos_dict_default = {'Opex_percentage': 0.04,
                                 'Capex_init': 22359405 / 40798942,  # Capex initial at year 2020
                                 'Capex_init_unit': '$/kg',
                                 'efficiency': 0.99,
                                 'CO2_from_production': co2_from_production,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'maturity': 5,
                                 'learning_rate': 0.1,
                                 'full_load_hours': 7920.0,
                                 'WACC': 0.0878,
                                     'techno_evo_eff': 'no',
                                 }
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               }
    DESC_IN.update(BioDieselTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = BioDieselTechnoDiscipline.DESC_OUT

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.dprices_demissions = None
        self.grad_total = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Transesterification(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        '''
        Compute techno_infos_dict with updated data_fuel_dict
        '''
        super().setup_sos_disciplines()
        dynamic_inputs = self.get_inst_desc_in()
        if self.get_data_in() is not None:
            if 'data_fuel_dict' in self.get_data_in():
                biodiesel_calorific_value = self.get_sosdisc_inputs('data_fuel_dict')[
                    'calorific_value']
                biodiesel_density = self.get_sosdisc_inputs('data_fuel_dict')[
                    'density']

                # Source for initial production: IEA 2022, Renewables 2021, https://www.iea.org/reports/renewables-2021, License: CC BY 4.0.
                # 43 billion liters from IEA in 2020
                initial_production = 37 * biodiesel_density / 1000 * biodiesel_calorific_value

                dynamic_inputs['techno_infos_dict'] = {
                    'type': 'dict', 'default': self.techno_infos_dict_default, 'unit': 'defined in dict'}
                dynamic_inputs['initial_production'] = {
                    'type': 'float', 'unit': 'TWh', 'default': initial_production}
        self.add_inputs(dynamic_inputs)

    def set_partial_derivatives_techno(self, grad_dict, carbon_emissions, grad_dict_resources={},
                                       grad_dict_resources_co2={}):
        """
        Generic method to set partial derivatives of techno_prices / energy_prices, energy_CO2_emissions and dco2_emissions/denergy_co2_emissions
        """
        self.dprices_demissions = {}
        self.grad_total = {}
        for energy, value in grad_dict.items():
            self.grad_total[energy] = value * \
                                      self.techno_model.margin[GlossaryEnergy.MarginValue].values / 100.0
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name), (GlossaryEnergy.StreamPricesValue, energy),
                self.grad_total[energy])
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                (GlossaryEnergy.StreamPricesValue, energy), self.grad_total[energy])
            # Means it has no sense to compute carbon emissions as for CC and
            # CS
            if carbon_emissions is not None:
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.CO2EmissionsValue, self.techno_name),
                    (GlossaryEnergy.StreamsCO2EmissionsValue, energy), value)

                # to manage gradient when carbon_emissions is null:
                # sign_carbon_emissions = 1 if carbon_emissions >=0, -1 if
                # carbon_emissions < 0
                sign_carbon_emissions = np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <= self.techno_model.year_end][
                        self.techno_name]) + 1 - np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <= self.techno_model.year_end][
                        self.techno_name]) ** 2
                grad_on_co2_tax = value * \
                                  self.techno_model.CO2_taxes.loc[
                                      self.techno_model.CO2_taxes[GlossaryEnergy.Years] <= self.techno_model.year_end][
                                      GlossaryEnergy.CO2Tax].values[:, np.newaxis] * np.maximum(
                    0, sign_carbon_emissions).values

                self.dprices_demissions[energy] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                    (GlossaryEnergy.StreamsCO2EmissionsValue, energy), self.dprices_demissions[energy])
        if carbon_emissions is not None:
            dCO2_taxes_factory = (self.techno_model.CO2_taxes[GlossaryEnergy.Years] <=
                                  self.techno_model.carbon_intensity[GlossaryEnergy.Years].max(
                                  )) * self.techno_model.carbon_intensity[self.techno_name].clip(0).values
            dtechno_prices_dCO2_taxes = dCO2_taxes_factory

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
                dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

        for resource, value in grad_dict_resources.items():
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name), (GlossaryEnergy.ResourcesPriceValue, resource),
                value *
                self.techno_model.margin[GlossaryEnergy.MarginValue].values / 100.0)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                (GlossaryEnergy.ResourcesPriceValue, resource), value *
                                                                self.techno_model.margin[
                                                                    GlossaryEnergy.MarginValue].values / 100.0)

        for resource, value in grad_dict_resources_co2.items():
            if carbon_emissions is not None:
                # resources carbon emissions
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.CO2EmissionsValue, self.techno_name),
                    (GlossaryEnergy.RessourcesCO2EmissionsValue, resource), value)

                sign_carbon_emissions = np.sign(carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <=
                                                                     self.techno_model.year_end][
                                                    self.techno_name]) + 1 - np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <=
                                         self.techno_model.year_end][self.techno_name]) ** 2
                grad_on_co2_tax = value * \
                                  self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes[GlossaryEnergy.Years] <=
                                                                  self.techno_model.year_end][
                                      GlossaryEnergy.CO2Tax].values[:, np.newaxis] * np.maximum(0,
                                                                                                sign_carbon_emissions).values

                self.dprices_demissions[resource] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                    (GlossaryEnergy.RessourcesCO2EmissionsValue, resource), self.dprices_demissions[resource])

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        BioDieselTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_stream_price()
        carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()
        grad_dict_resources_co2 = self.techno_model.grad_co2_emissions_vs_resources_co2_emissions()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources, grad_dict_resources_co2)

        # for resource, value in grad_dict_resources_co2.items():
        #     self.set_partial_derivative_for_other_types(
        #         (GlossaryEnergy.CO2EmissionsValue, self.techno_name), (GlossaryEnergy.RessourcesCO2EmissionsValue, resource), value)
