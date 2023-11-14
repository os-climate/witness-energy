'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/03 Copyright 2023 Capgemini

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

import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.disciplines.biodiesel_techno_disc import BioDieselTechnoDiscipline
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.models.biodiesel.transesterification.transesterification import Transesterification


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
    techno_name = 'Transesterification'
    energy_name = BioDiesel.name
    lifetime = 15
    construction_delay = 3  # years

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.0, 4.085787594423131, 11.083221775965836, 9.906291833479699,
                                                         11.264502455357881, 15.372601517593951, 10.940986166952394,
                                                         6.682284695273031, 3.1012940652355083, 7.711401160086531,
                                                         5.848393573822739, 2.2088353407762535, 3.162650601721087,
                                                         8.631749219311956]})  # to review

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [0.0, 3.0, 2.0]})
    DESC_IN = {'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(BioDieselTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = BioDieselTechnoDiscipline.DESC_OUT

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

                # Beer, T., Grant, T., Morgan, G., Lapszewicz, J., Anyon, P., Edwards, J., Nelson, P., Watson, H. and Williams, D., 2001.
                # Comparison of transport fuels. FINAL REPORT (EV45A/2/F3C) to the Australian Greenhouse Office on the stage, 2.
                # Pre-combustion CO2 emissions for soybean = 0.03 kgCO2/MJ * 3.6 MJ/kWh =
                # 0.11 kgCO2/kWh
                co2_from_production = (6.7 / 1000) * biodiesel_calorific_value
                techno_infos_dict_default = {'Opex_percentage': 0.04,
                                             'lifetime': self.lifetime,  # for now constant in time but should increase with time
                                             'lifetime_unit': GlossaryCore.Years,
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

                                             GlossaryCore.ConstructionDelay: self.construction_delay
                                             }

                # Source for initial production: IEA 2022, Renewables 2021, https://www.iea.org/reports/renewables-2021, License: CC BY 4.0.
                # 43 billion liters from IEA in 2020
                initial_production = 37 * biodiesel_density / 1000 * biodiesel_calorific_value

                dynamic_inputs['techno_infos_dict'] = {
                    'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'}
                dynamic_inputs['initial_production'] = {
                    'type': 'float', 'unit': 'TWh', 'default': initial_production}
        self.add_inputs(dynamic_inputs)

    def set_partial_derivatives_techno(self, grad_dict, carbon_emissions, grad_dict_resources={}, grad_dict_resources_co2={}):
        """
        Generic method to set partial derivatives of techno_prices / energy_prices, energy_CO2_emissions and dco2_emissions/denergy_co2_emissions
        """
        self.dprices_demissions = {}
        self.grad_total = {}
        for energy, value in grad_dict.items():
            self.grad_total[energy] = value * \
                self.techno_model.margin[GlossaryCore.MarginValue].values / 100.0
            self.set_partial_derivative_for_other_types(
                (GlossaryCore.TechnoPricesValue, self.techno_name), (GlossaryCore.EnergyPricesValue, energy), self.grad_total[energy])
            self.set_partial_derivative_for_other_types(
                (GlossaryCore.TechnoPricesValue, f'{self.techno_name}_wotaxes'), (GlossaryCore.EnergyPricesValue, energy), self.grad_total[energy])
            # Means it has no sense to compute carbon emissions as for CC and
            # CS
            if carbon_emissions is not None:
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.CO2EmissionsValue, self.techno_name), (GlossaryCore.EnergyCO2EmissionsValue, energy), value)

                # to manage gradient when carbon_emissions is null:
                # sign_carbon_emissions = 1 if carbon_emissions >=0, -1 if
                # carbon_emissions < 0
                sign_carbon_emissions = np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryCore.Years] <= self.techno_model.year_end][self.techno_name]) + 1 - np.sign(carbon_emissions.loc[carbon_emissions[GlossaryCore.Years] <= self.techno_model.year_end][self.techno_name])**2
                grad_on_co2_tax = value * \
                    self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes[GlossaryCore.Years] <= self.techno_model.year_end][GlossaryCore.CO2Tax].values[:, np.newaxis] * np.maximum(
                        0, sign_carbon_emissions).values

                self.dprices_demissions[energy] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.TechnoPricesValue, self.techno_name), (GlossaryCore.EnergyCO2EmissionsValue, energy), self.dprices_demissions[energy])
        if carbon_emissions is not None:
            dCO2_taxes_factory = (self.techno_model.CO2_taxes[GlossaryCore.Years] <= self.techno_model.carbon_emissions[GlossaryCore.Years].max(
            )) * self.techno_model.carbon_emissions[self.techno_name].clip(0).values
            dtechno_prices_dCO2_taxes = dCO2_taxes_factory

            self.set_partial_derivative_for_other_types(
                (GlossaryCore.TechnoPricesValue, self.techno_name), (GlossaryCore.CO2TaxesValue, GlossaryCore.CO2Tax), dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

        for resource, value in grad_dict_resources.items():
            self.set_partial_derivative_for_other_types(
                (GlossaryCore.TechnoPricesValue, self.techno_name), (GlossaryCore.ResourcesPriceValue, resource), value *
                self.techno_model.margin[GlossaryCore.MarginValue].values / 100.0)
            self.set_partial_derivative_for_other_types(
                (GlossaryCore.TechnoPricesValue, f'{self.techno_name}_wotaxes'), (GlossaryCore.ResourcesPriceValue, resource), value *
                self.techno_model.margin[GlossaryCore.MarginValue].values / 100.0)

        for resource, value in grad_dict_resources_co2.items():
            if carbon_emissions is not None:
                # resources carbon emissions
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.CO2EmissionsValue, self.techno_name), (GlossaryCore.RessourcesCO2EmissionsValue, resource), value)

                sign_carbon_emissions = np.sign(carbon_emissions.loc[carbon_emissions[GlossaryCore.Years] <=
                                                                     self.techno_model.year_end][self.techno_name]) + 1 - np.sign(carbon_emissions.loc[carbon_emissions[GlossaryCore.Years] <=
                                                                                                                                                       self.techno_model.year_end][self.techno_name]) ** 2
                grad_on_co2_tax = value * self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes[GlossaryCore.Years] <=
                                                                          self.techno_model.year_end][GlossaryCore.CO2Tax].values[:, np.newaxis] * np.maximum(0, sign_carbon_emissions).values

                self.dprices_demissions[resource] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.TechnoPricesValue, self.techno_name), (GlossaryCore.RessourcesCO2EmissionsValue, resource), self.dprices_demissions[resource])

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        BioDieselTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        carbon_emissions = self.get_sosdisc_outputs(GlossaryCore.CO2EmissionsValue)
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()
        grad_dict_resources_co2 = self.techno_model.grad_co2_emissions_vs_resources_co2_emissions()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources, grad_dict_resources_co2)

        # for resource, value in grad_dict_resources_co2.items():
        #     self.set_partial_derivative_for_other_types(
        #         (GlossaryCore.CO2EmissionsValue, self.techno_name), (GlossaryCore.RessourcesCO2EmissionsValue, resource), value)
