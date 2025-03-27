'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2024/06/24 Copyright 2023 Capgemini

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
"""
import logging
from copy import deepcopy

import numpy as np
import pandas as pd
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.techno_type.disciplines.liquid_fuel_techno_disc import (
    LiquidFuelTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch import (
    FischerTropsch,
)
from energy_models.models.syngas.autothermal_reforming.autothermal_reforming_disc import (
    AutothermalReformingDiscipline,
)
from energy_models.models.syngas.biomass_gasification.biomass_gasification_disc import (
    BiomassGasificationDiscipline,
)
from energy_models.models.syngas.co_electrolysis.co_electrolysis_disc import (
    CoElectrolysisDiscipline,
)
from energy_models.models.syngas.coal_gasification.coal_gasification_disc import (
    CoalGasificationDiscipline,
)
from energy_models.models.syngas.pyrolysis.pyrolysis_disc import PyrolysisDiscipline
from energy_models.models.syngas.smr.smr_disc import SMRDiscipline


class FischerTropschDiscipline(LiquidFuelTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Fischer Tropsch Kerosene Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-charging-station fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.FischerTropsch

    # 'reaction1 if r1<n/(2n+1)': 'H2 + r1CO + aH20  <--> H2 + n/(2n+1)CO +bCO2',
    #          'reaction2': '(2n+1)H2 + nCO --> CnH_2n+1 + nH20 ',

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.03,
                                 'CO2_from_production': 0.0,  # molar mass calcul
                                 # 1.5kg CO2--> 1kg syngas
                                 # 2.12kg syngas --> 1kg liquid_fuel
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0.0,  # no electricity is needed for FT synthesis or negligible
                                 'elec_demand_unit': 'kWh/kWh',
                                 #                                  'fuel_demand': 0.9,  # 0.8kWh of CH4 gives 1kWh of H2 to modify for CO2
                                 #                                  'fuel_demand_unit': 'kWh/kWh',
                                 'syngas_demand': 106.6 * 14.47 / (146 + 348 + 81),
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.15,
                                 'maximum_learning_capex_ratio': 0.5,
                                 # 'medium_heat_production': (165/28.01)*1000*2.77778e-13,
                                 # # https://www.sciencedirect.com/science/article/pii/S1385894718309215, reaction enthalpy of −165 kJ/molCO
                                 # 'medium_heat_production_unit': 'TWh/kg',
                                 # 60000 euro/bpd : 1 barrel = 1553,41kwh of
                                 # liquid_fuel per 24 hours
                                 # Capex initial at year 2020
                                 'Capex_init': 60000.0 / (1553.41 / 24.0 * 8000.0),
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 0.65,
                                 'techno_evo_eff': 'no',
                                 # N/2N+1 with N number of carbon mol in
                                 # liquid_fuel
                                 'carbon_number': 12}  # To review

    
    # FischerTropsch Wikipedia :
    # 140000+34000 BPD in Qatar GtL
    # 12000 BPD in Malaysia GtL
    # 112000 BPD in China CtL : http://www.synfuelschina.com.cn/en/about/
    # 165000 + 36000 BPD in South Africa CtL
    # BPD to TWh per year = 1700/1e9*365
    initial_production = (140000 + 34000 + 12000 + 112000 + 165000 +
                          36000) * 1700 / 1e9 * 365  # in TWh at year_start

    FLUE_GAS_RATIO = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default,
                                     'unit': 'defined in dict'},
                      
               'syngas_ratio': {'type': 'array', 'unit': '%',
                                'visibility': LiquidFuelTechnoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'},

               f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.data_fuel_dict': {'type': 'dict',
                                                            'visibility': LiquidFuelTechnoDiscipline.SHARED_VISIBILITY,
                                                            'namespace': 'ns_energy',
                                                            'default': GaseousHydrogen.data_energy_dict,
                                                            'unit': 'defined in dict'},
               f'{GlossaryEnergy.syngas}.{GlossaryEnergy.data_fuel_dict}': {'type': 'dict',
                                         'visibility': LiquidFuelTechnoDiscipline.SHARED_VISIBILITY,
                                         'namespace': 'ns_energy',
                                         'default': Syngas.data_energy_dict,
                                         'unit': 'defined in dict'}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(LiquidFuelTechnoDiscipline.DESC_IN)

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.dprices_demissions = None
        self.grad_total = None

    def init_execution(self):
        self.model = FischerTropsch(self.techno_name)

    def specific_run(self):

        # -- get inputs
        inputs_dict = deepcopy(self.get_sosdisc_inputs())
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        xto_liquid_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years})

        for techno in inputs_dict['energy_detailed_techno_prices']:
            if techno != GlossaryEnergy.Years:
                techno_model = FischerTropsch(self.techno_name)
                # Update init values syngas price and syngas_ratio
                inputs_dict[GlossaryEnergy.StreamPricesValue][GlossaryEnergy.syngas] = inputs_dict['energy_detailed_techno_prices'][
                    techno]
                inputs_dict['syngas_ratio'] = np.ones(
                    len(years)) * inputs_dict['syngas_ratio_technos'][techno]
                # -- configure class with inputs
                techno_model.configure_parameters(inputs_dict)
                techno_model.configure_parameters_update(inputs_dict)
                # -- compute informations

                # Compute the price with these new values
                techno_syngas_price = techno_model.compute_price()
                # Store only the overall price

                if techno == BiomassGasificationDiscipline.techno_name:
                    global_techno = 'PBtL'
                elif techno == PyrolysisDiscipline.techno_name:
                    global_techno = 'WtL-pyrolysis'
                elif techno == SMRDiscipline.techno_name:
                    global_techno = 'GtL-SMR'
                elif techno == AutothermalReformingDiscipline.techno_name:
                    global_techno = 'GtL-ATR'
                elif techno == CoalGasificationDiscipline.techno_name:
                    global_techno = 'CtL'
                elif techno == CoElectrolysisDiscipline.techno_name:
                    global_techno = 'PtL'
                else:
                    global_techno = 'unknown techno name'
                xto_liquid_prices[global_techno] = techno_syngas_price[self.techno_name]

        self.store_sos_outputs_values(
            {'xto_liquid_prices': xto_liquid_prices})

    def get_chart_filter_list(self):

        chart_filters = super().get_chart_filter_list()
        chart_filters[0].extend(['Age Distribution Production', 'X to Liquid technologies'])
        chart_filters[1].extend(['$/USgallon'])

        return chart_filters

    def get_post_processing_list(self, filters=None):
        charts = []
        price_unit_list = ['$/MWh', '$/t', "$/USgallon"]
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        generic_filter = LiquidFuelTechnoDiscipline.get_chart_filter_list(self)
        instanciated_charts = LiquidFuelTechnoDiscipline.get_post_processing_list(
            self, generic_filter)

        if 'Detailed prices' in charts and '$/USgallon' in price_unit_list:
            techno_detailed_prices = self.get_sosdisc_outputs(
                GlossaryEnergy.TechnoDetailedPricesValue)
            chart_name = f'Detailed prices of {self.techno_name} technology over the years'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/USgallon]',
                                                 chart_name=chart_name)

            if 'part_of_total' in self.get_data_in():
                part_of_total = self.get_sosdisc_inputs('part_of_total')
                new_chart.annotation_upper_left = {
                    'Percentage of total price': f'{part_of_total[0] * 100.0} %'}
                tot_price = techno_detailed_prices[self.techno_name].values * \
                            data_fuel_dict['calorific_value'] / \
                            part_of_total
                serie = InstanciatedSeries(
                    techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                    tot_price.tolist(), 'Total price without percentage', 'lines')
                new_chart.series.append(serie)
            # Add total price
            techno_gallon_price = techno_detailed_prices[self.techno_name].values * \
                                  data_fuel_dict['calorific_value'] * \
                                  data_fuel_dict['density'] / 1e6 * 3.78

            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                techno_gallon_price.tolist(), 'Total price with margin', 'lines')

            new_chart.series.append(serie)
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_detailed_price_in_dollar_kwh(self):

        techno_detailed_prices = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedPricesValue)
        cost_of_energies_usage = self.get_sosdisc_outputs(GlossaryEnergy.CostOfStreamsUsageValue)
        specific_costs = self.get_sosdisc_outputs(GlossaryEnergy.SpecificCostsForProductionValue)
        chart_name = f'Detailed prices of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices[GlossaryEnergy.Years].values.tolist())
        year_end = max(techno_detailed_prices[GlossaryEnergy.Years].values.tolist())
        minimum = 0
        maximum = max(
            techno_detailed_prices[self.techno_name].values.tolist()) * 1.2

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/kWh]', [year_start, year_end],
                                             [minimum, maximum],
                                             chart_name=chart_name)

        # Add total price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices[self.techno_name].values.tolist(), 'Total price with margin', 'lines')

        new_chart.series.append(serie)

        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices[f'{self.techno_name}_factory'].values.tolist(), 'Factory', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values.tolist(), f'{GlossaryEnergy.syngas} before transformation',
            'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            cost_of_energies_usage[GlossaryEnergy.Years].values.tolist(),
            cost_of_energies_usage[GlossaryEnergy.electricity].values.tolist(), GlossaryEnergy.electricity, 'lines')

        new_chart.series.append(serie)
        # Transport price
        if 'WGS' in techno_detailed_prices:
            WGS_cost = specific_costs[GlossaryEnergy.syngas].values - \
                       techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), 'WGS', 'lines')

            new_chart.series.append(serie)
        if GlossaryEnergy.RWGS in techno_detailed_prices:
            WGS_cost = specific_costs[GlossaryEnergy.syngas].values - \
                       techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), GlossaryEnergy.RWGS, 'lines')

            new_chart.series.append(serie)
        if 'WGS or RWGS' in techno_detailed_prices:
            WGS_cost = specific_costs[GlossaryEnergy.syngas].values - \
                       techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), 'WGS or RWGS', 'lines')

            new_chart.series.append(serie)
        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices['transport'].values.tolist(), 'Transport', 'lines')

        new_chart.series.append(serie)
        # CO2 taxes
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices['CO2_taxes_factory'].values.tolist(), 'CO2 taxes due to production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_detailed_price_in_dollar_kg(self):

        techno_detailed_prices = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)
        cost_of_energies_usage = self.get_sosdisc_outputs(GlossaryEnergy.CostOfStreamsUsageValue)
        specific_costs = self.get_sosdisc_outputs(GlossaryEnergy.SpecificCostsForProductionValue)
        calorific_value = self.get_sosdisc_inputs('data_fuel_dict')[
            'calorific_value']
        chart_name = f'Detailed prices [$/t] of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices[GlossaryEnergy.Years].values.tolist())
        year_end = max(techno_detailed_prices[GlossaryEnergy.Years].values.tolist())
        minimum = 0
        max_price = techno_detailed_prices[self.techno_name].values * \
                    calorific_value
        maximum = max(max_price.tolist()) * 1.2

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/t]', [year_start, year_end],
                                             [minimum, maximum],
                                             chart_name=chart_name)

        total_price_kg = techno_detailed_prices[self.techno_name].values * \
                         calorific_value
        # Add total price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            total_price_kg.tolist(), 'Total price with margin', 'lines')

        new_chart.series.append(serie)

        factory_price_kg = techno_detailed_prices[f'{self.techno_name}_factory'].values * calorific_value
        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            factory_price_kg.tolist(), 'Factory', 'lines')

        new_chart.series.append(serie)

        total_price_kg = techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values * calorific_value

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            total_price_kg.tolist(), f'{GlossaryEnergy.syngas} before transformation', 'lines')

        new_chart.series.append(serie)
        total_price_kg = cost_of_energies_usage[GlossaryEnergy.electricity].values * \
                         calorific_value

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            total_price_kg.tolist(), GlossaryEnergy.electricity, 'lines')

        new_chart.series.append(serie)
        # Transport price
        if 'WGS' in techno_detailed_prices:
            WGS_cost = (specific_costs[GlossaryEnergy.syngas].values -
                        techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values) * calorific_value
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), 'WGS', 'lines')

            new_chart.series.append(serie)
        if GlossaryEnergy.RWGS in techno_detailed_prices:
            WGS_cost = (specific_costs[GlossaryEnergy.syngas].values -
                        techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values) * calorific_value
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), GlossaryEnergy.RWGS, 'lines')

            new_chart.series.append(serie)
        if 'WGS or RWGS' in techno_detailed_prices:
            WGS_cost = (specific_costs[GlossaryEnergy.syngas].values -
                        techno_detailed_prices[f'{GlossaryEnergy.syngas} before transformation'].values) * calorific_value
            # Factory price
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                WGS_cost.tolist(), 'WGS or RWGS', 'lines')

            new_chart.series.append(serie)
        total_price_kg = techno_detailed_prices['transport'].values * \
                         calorific_value
        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            total_price_kg.tolist(), 'Transport', 'lines')

        new_chart.series.append(serie)
        # CO2 taxes
        total_price_kg = techno_detailed_prices['CO2_taxes_factory'].values * \
                         calorific_value
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            total_price_kg.tolist(), 'CO2 taxes due to production', 'lines')
        new_chart.series.append(serie)

        return new_chart
"""
