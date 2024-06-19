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

import numpy as np
import pandas as pd

from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import (
    GaseousHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking import (
    PlasmaCracking,
)


class PlasmaCrackingDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    PLasmacracking discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Plasma Cracking Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-hospital-symbol fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.PlasmaCracking
    lifetime = 25
    construction_delay = 2
    techno_infos_dict_default = {'reaction': 'CH4 = C + 2H2',
                                 'maturity': 5,
                                 'Opex_percentage': 0.2,
                                 'CO2_from_production': 0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 8.325,
                                 'elec_demand_unit': 'kWh/kg',
                                 'WACC': 0.1,
                                 'learning_rate': 0.25,
                                 'maximum_learning_capex_ratio': 0.33,
                                 'lifetime': lifetime,
                                 'Capex_init': 12440000.0,
                                 'Capex_init_unit': 'pounds',
                                 'pounds_dollar': 1.32,
                                 'full_load_hours': 8410.0,
                                 'available_power': 150,
                                 'available_power_unit': 'kg/h',
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 4,
                                 'efficiency': 0.15,
                                 'efficiency_max': 0.6,
                                 'nb_years_amort_capex': 10.,
                                 GlossaryEnergy.ConstructionDelay: construction_delay}

    initial_production = 1e-12
    initial_age_distribution = pd.DataFrame({'age': np.arange(0, lifetime),
                                             'distrib': [3.317804973859207,
                                                         6.975128305927281, 4.333201737255864,
                                                         3.2499013031833868, 1.5096723255070685,
                                                         1.7575996841282722,
                                                         4.208448479896288, 2.7398341887870643,
                                                         5.228582707722979,
                                                         10.057639166085064, 0.0, 2.313462297352473,
                                                         6.2755625737595535,
                                                         5.609159099363739, 6.3782076592711885,
                                                         8.704303197679629,
                                                         6.1950256610618135, 3.7836557445596464,
                                                         1.7560205289962763,
                                                         4.366363995027777, 3.3114883533312236, 1.250690879995941,
                                                         1.7907619419001841, 4.88748519534807, 0.0]})
    invest_before_year_start = pd.DataFrame({
        'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [0.0, 0.0]})

    CO2_credits = pd.DataFrame({GlossaryEnergy.Years: range(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
                                'CO2_credits': 50.})

    market_demand = pd.DataFrame(
        {GlossaryEnergy.Years: range(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1), 'carbon_demand': 5e-2})

    # DESC_IN.update(
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe',
                                       'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe',
                                                               'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False},
               'CO2_credits': {'type': 'dataframe', 'default': CO2_credits, 'unit': '$/t/year', 'structuring': True,
                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                        'CO2_credits': ('float', None, True), }
                               },
               'market_demand': {'type': 'dataframe', 'default': market_demand, 'unit': 'Mt/year', 'structuring': True,
                                 'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                          'carbon_demand': ('float', None, True),}
                                 }
               }

    # -- add specific techno inputs to this
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    # DESC_OUT = HydrogenTechnoDiscipline.DESC_OUT
    DESC_OUT = {'percentage_resource': {'type': 'dataframe', 'unit': '%'},
                'carbon_quantity_to_be_stored': {'type': 'dataframe', 'unit': 'Mt', 'namespace': 'ns_carb',
                                                 'visibility': 'Shared'}}
    DESC_OUT.update(GaseousHydrogenTechnoDiscipline.DESC_OUT)

    def setup_sos_disciplines(self):

        super().setup_sos_disciplines()

        if self.get_data_in() is not None:
            if GlossaryEnergy.YearStart in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                years = np.arange(year_start, year_end + 1)

                if self.get_sosdisc_inputs('CO2_credits')[GlossaryEnergy.Years].values.tolist() != list(years):
                    self.update_default_value(
                        'CO2_credits', self.IO_TYPE_IN, pd.DataFrame({GlossaryEnergy.Years: years, 'CO2_credits': 50.}))

                if self.get_sosdisc_inputs('market_demand')[GlossaryEnergy.Years].values.tolist() != list(years):
                    self.update_default_value(
                        'market_demand', self.IO_TYPE_IN,
                        pd.DataFrame({GlossaryEnergy.Years: years, 'carbon_demand': 5e-2}))

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = PlasmaCracking(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def run(self):
        GaseousHydrogenTechnoDiscipline.run(self)
        self.specific_run()

    def specific_run(self):
        inputs_dict = self.get_sosdisc_inputs()

        percentage_resource = self.techno_model.compute_percentage_resource(
            inputs_dict['CO2_credits'], inputs_dict['market_demand'])

        techno_prices = self.techno_model.add_percentage_to_total(
            percentage_resource)

        quantity = self.techno_model.compute_revenues(
            inputs_dict['CO2_credits'], inputs_dict['market_demand'])

        outputs_dict = {GlossaryEnergy.TechnoPricesValue: techno_prices,
                        'percentage_resource': percentage_resource,
                        'carbon_quantity_to_be_stored': quantity[[GlossaryEnergy.Years, GlossaryEnergy.carbon_storage]]
                        # quantity[[GlossaryEnergy.Years, 'carbon_production', 'carbon_sales', GlossaryEnergy.carbon_storage]]
                        }
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        GaseousHydrogenTechnoDiscipline.compute_sos_jacobian(self)

        '''
   GRADIENT H2 VS ENERGY_CO2_EMISSION
        '''
        percentage_resource_df = self.get_sosdisc_outputs(
            'percentage_resource')
        percentage_resource = percentage_resource_df[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values / 100

        energy_CO2_emission = self.get_sosdisc_inputs(GlossaryEnergy.EnergyCO2EmissionsValue)
        for energy in energy_CO2_emission:
            if energy != GlossaryEnergy.Years:
                if (energy == GlossaryEnergy.methane) | (energy == GlossaryEnergy.electricity):
                    dtechno_price_denergy_CO2_emission = self.dprices_demissions[energy]

                else:
                    dtechno_price_denergy_CO2_emission = np.array([
                                                                      [0] * len(energy_CO2_emission)] * len(
                        energy_CO2_emission))

                if dtechno_price_denergy_CO2_emission is not None:
                    value = percentage_resource * dtechno_price_denergy_CO2_emission
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                        (GlossaryEnergy.EnergyCO2EmissionsValue, energy), value)

        '''
   GRADIENT H2 VS ENERGY_PRICES
        '''

        inputs_dict = self.get_sosdisc_inputs()
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        CO2_credits = inputs_dict['CO2_credits']
        carbon_market_demand = inputs_dict['market_demand']

        energy_prices = self.get_sosdisc_inputs(GlossaryEnergy.EnergyPricesValue)
        techno_prices = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoPricesValue)[self.techno_name].values
        techno_prices_wotaxes = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoPricesValue)[f'{self.techno_name}_wotaxes'].values

        for energy in energy_prices:
            if energy != GlossaryEnergy.Years:
                dpercentage_resources_denergy_prices = self.techno_model.grad_percentage_resource_vs_energy_prices(
                    CO2_credits, carbon_market_demand, energy)

                if (energy == GlossaryEnergy.methane) | (energy == GlossaryEnergy.electricity):
                    dtechno_price_denergy_prices = self.grad_total[energy]
                    dtechno_price_denergy_prices_wotaxes = self.grad_total[energy]

                else:
                    dtechno_price_denergy_prices = np.array([
                                                                [0] * len(energy_prices)] * len(energy_prices))
                    dtechno_price_denergy_prices_wotaxes = np.array([
                                                                        [0] * len(energy_prices)] * len(energy_prices))

                if dtechno_price_denergy_prices is not None:
                    x = np.array([[x_i if x_i > 1e-6 else 1e-6 for x_i in percentage_resource], ]
                                 * len(years)).transpose()
                    y = np.array([techno_prices, ] * len(years)).transpose()
                    y_wotaxes = np.array(
                        [techno_prices_wotaxes, ] * len(years)).transpose()
                    value = dtechno_price_denergy_prices * x + \
                            dpercentage_resources_denergy_prices * y / x
                    value_wotaxes = dtechno_price_denergy_prices_wotaxes * x + \
                                    dpercentage_resources_denergy_prices * y_wotaxes / x

                    self.set_partial_derivative_for_other_types(
                        ('percentage_resource', f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'),
                        (GlossaryEnergy.EnergyPricesValue, energy), dpercentage_resources_denergy_prices * 100)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                        (GlossaryEnergy.EnergyPricesValue, energy), value)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                        (GlossaryEnergy.EnergyPricesValue, energy), value_wotaxes)

        '''
   GRADIENT H2 VS INVEST_LEVEL
        '''
        scaling_factor_invest_level = self.get_sosdisc_inputs(
            'scaling_factor_invest_level')
        dtechno_price_dinvest = self.dprice_dinvest * \
                                scaling_factor_invest_level
        dtechno_price_dinvest_wotaxes = self.dprice_dinvest * \
                                        scaling_factor_invest_level

        dhydro_prod_dinvest = self.dprod_dinvest * \
                              scaling_factor_invest_level  # / scaling_factor_techno_production
        dcarbon_prod_dinvest = self.dprod_column_dinvest[f"{ResourceGlossary.CarbonResource} (Mt)"] * \
                               scaling_factor_invest_level  # / scaling_factor_techno_production

        if (dhydro_prod_dinvest is not None) & (dcarbon_prod_dinvest is not None):
            dpercentage_resources_dinvest = self.techno_model.grad_percentage_resource_vs_invest(
                CO2_credits, carbon_market_demand, dhydro_prod_dinvest, dcarbon_prod_dinvest)
            self.set_partial_derivative_for_other_types(
                ('percentage_resource', f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'),
                (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue), dpercentage_resources_dinvest * 100)

        if (dhydro_prod_dinvest is not None) & (dcarbon_prod_dinvest is not None) & (
                dtechno_price_dinvest is not None) & (dtechno_price_dinvest_wotaxes is not None):
            x = np.array(
                [[x_i if x_i > 0.0 else 1e-6 for x_i in percentage_resource], ] * len(years)).transpose()
            y = np.array([techno_prices, ] * len(years)).transpose()
            y_wotaxes = np.array(
                [techno_prices_wotaxes, ] * len(years)).transpose()

            value = dtechno_price_dinvest * x + \
                    dpercentage_resources_dinvest * y / x
            value_wotaxes = dtechno_price_dinvest_wotaxes * x + \
                            dpercentage_resources_dinvest * y_wotaxes / x

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue), value)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue), value_wotaxes)

        '''
   GRADIENT H2 VS CO2_TAXES
        '''

        dCO2_taxes_factory = (self.techno_model.CO2_taxes[GlossaryEnergy.Years] <= self.techno_model.carbon_intensity[
            GlossaryEnergy.Years].max(
        )) * self.techno_model.carbon_intensity[self.techno_name].clip(0).values
        dtechno_prices_dCO2_taxes = dCO2_taxes_factory * \
                                    self.techno_model.margin.loc[self.techno_model.margin[GlossaryEnergy.Years] <=
                                                                 self.techno_model.cost_details[
                                                                     GlossaryEnergy.Years].max()][
                                        GlossaryEnergy.MarginValue].values / 100.0

        techno_prices_techno = self.techno_model.cost_details[[
            GlossaryEnergy.Years, self.techno_name, f'{self.techno_name}_wotaxes']].merge(percentage_resource_df,
                                                                                          how='left').fillna(0)
        dtechno_prices_dCO2_taxes = dtechno_prices_dCO2_taxes.values * \
                                    techno_prices_techno[self.energy_name] / 100.

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, self.techno_name), (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
            dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

        '''
   GRADIENT H2 VS ALL_DEMAND_RATIO
        '''
        if GlossaryEnergy.electricity in self.dprod_dratio.keys():
            dhydro_prod_dratio_elec = self.dprod_dratio[GlossaryEnergy.electricity] * \
                                      scaling_factor_invest_level
        else:
            dhydro_prod_dratio_elec = np.array([[0] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[
                0]][0])] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[0]][0]))
        if GlossaryEnergy.methane in self.dprod_dratio.keys():
            dhydro_prod_dratio_meth = self.dprod_dratio[GlossaryEnergy.methane] * \
                                      scaling_factor_invest_level
        else:
            dhydro_prod_dratio_meth = np.array([[0] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[
                0]][0])] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[0]][0]))

        if GlossaryEnergy.electricity in self.dprod_column_dratio[f"{ResourceGlossary.CarbonResource} (Mt)"].keys():
            dcarbon_prod_dratio_elec = self.dprod_column_dratio[f"{ResourceGlossary.CarbonResource} (Mt)"][
                                           GlossaryEnergy.electricity] * \
                                       scaling_factor_invest_level  # / scaling_factor_techno_production
        else:
            dcarbon_prod_dratio_elec = np.array([[0] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[
                0]][0])] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[0]][0]))
        if GlossaryEnergy.methane in self.dprod_column_dratio[f"{ResourceGlossary.CarbonResource} (Mt)"].keys():
            dcarbon_prod_dratio_meth = self.dprod_column_dratio[f"{ResourceGlossary.CarbonResource} (Mt)"][GlossaryEnergy.methane] * \
                                       scaling_factor_invest_level  # / scaling_factor_techno_production
        else:
            dcarbon_prod_dratio_meth = np.array([[0] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[
                0]][0])] * len(self.dprod_dratio[list(self.dprod_dratio.keys())[0]][0]))

        dpercentage_resources_dratio_elec = self.techno_model.grad_percentage_resource_vs_ratio(
            CO2_credits, carbon_market_demand, dhydro_prod_dratio_elec, dcarbon_prod_dratio_elec)
        dpercentage_resources_dratio_meth = self.techno_model.grad_percentage_resource_vs_ratio(
            CO2_credits, carbon_market_demand, dhydro_prod_dratio_meth, dcarbon_prod_dratio_meth)

        self.set_partial_derivative_for_other_types(
            ('percentage_resource', f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.electricity), dpercentage_resources_dratio_elec)
        self.set_partial_derivative_for_other_types(
            ('percentage_resource', f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.methane), dpercentage_resources_dratio_meth)

        x = np.array(
            [[x_i if x_i > 0.0 else 1e-6 for x_i in percentage_resource], ] * len(years)).transpose()
        y = np.array([techno_prices, ] * len(years)).transpose()
        y_wotaxes = np.array(
            [techno_prices_wotaxes, ] * len(years)).transpose()
        value_elec = dpercentage_resources_dratio_elec * y / x
        value_wotaxes_elec = dpercentage_resources_dratio_elec * y_wotaxes / x
        value_meth = dpercentage_resources_dratio_meth * y / x
        value_wotaxes_meth = dpercentage_resources_dratio_meth * y_wotaxes / x

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, self.techno_name),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.electricity), value_elec / 100)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.electricity), value_wotaxes_elec / 100)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, self.techno_name),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.methane), value_meth / 100)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
            (GlossaryEnergy.AllStreamsDemandRatioValue, GlossaryEnergy.methane), value_wotaxes_meth / 100)

        '''
   GRADIENT H2 VS RESOURCES_PRICES
        '''
        dcarbon_price_dresources_price = np.identity(
            len(self.techno_model.years))
        dpercentage_resources_dresources_price = self.techno_model.grad_percentage_resource_vs_resources_price(
            CO2_credits, carbon_market_demand, dcarbon_price_dresources_price)
        self.set_partial_derivative_for_other_types(
            ('percentage_resource', f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'),
            (GlossaryEnergy.ResourcesPriceValue, 'carbon_resource'), dpercentage_resources_dresources_price * 100)
        x = np.array(
            [[x_i if x_i > 0.0 else 1e-6 for x_i in percentage_resource], ] * len(years)).transpose()
        y = np.array([techno_prices, ] * len(years)).transpose()
        y_wotaxes = np.array(
            [techno_prices_wotaxes, ] * len(years)).transpose()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, self.techno_name),
            (GlossaryEnergy.ResourcesPriceValue, 'carbon_resource'), dpercentage_resources_dresources_price * y / x)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
            (GlossaryEnergy.ResourcesPriceValue, 'carbon_resource'),
            dpercentage_resources_dresources_price * y_wotaxes / x)
