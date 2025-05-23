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

import numpy as np
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.techno_type.disciplines.liquid_fuel_techno_disc import (
    LiquidFuelTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_fuel.refinery.refinery import Refinery


class RefineryDiscipline(LiquidFuelTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Refinery Liquid Fuel Model',
        'type': 'Test',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.Refinery

    # only energetical valuable product taken into acocun. Wastes are not
    # taken into account
    # mass ratio of product for 1 kg of crude oil refined
    product_break_down = {LiquidFuelTechnoDiscipline.kerosene_name: 0.137,
                          LiquidFuelTechnoDiscipline.gasoline_name: 0.465,
                          LiquidFuelTechnoDiscipline.lpg_name: 0.058,
                          LiquidFuelTechnoDiscipline.heating_oil_name: 0.085,
                          LiquidFuelTechnoDiscipline.ulsd_name: 0.094,
                          }

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.04,
                                 'CO2_flue_gas_intensity_by_prod_unit': 0.65 / 2.0,  # we split 0.65 in refinery and oil extraction
                                 # However it is really depending on type of extraction
                                 # see
                                 # https://theicct.org/sites/default/files/ICCT_crudeoil_Eur_Dec2010_sum.pdf

                                 'CO2_from_production_unit': 'kg/kg',
                                 # IEA Methane Tracker 2021 , (https://www.iea.org/articles/methane-tracker-data-explorer), License: CC BY 4.0.
                                 # Emission factor are computed with raw
                                 # production from WITNESS and emissions from
                                 # IEA Methane tracker
                                 # Are approximately same than GAINS 2017 model

                                 # venting + flaring + unintended leakage emissions factors (Mt/TWh):
                                 'CH4_emission_factor': (21.9 + 7.2) / 50731. + (1.4 + 6.9) / 50731. + (0.6 + 1.7) / 50731.,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 # 'medium_heat_production': (30000/136) * 0.000293 * 1.00E-09 / (1.13E-08),  # 30000  Btu/bbl, https://www.osti.gov/servlets/purl/7261027, Page No 41
                                 # 'medium_heat_production_unit': 'TWh/TWh',
                                 # a barrel of oil weighs around 300 pounds or about 136 kilograms.
                                 # 1 BTU = 0.000293 kWh
                                 # https://www.e-education.psu.edu/eme801/node/470
                                 # 1 kg of crude oil is 11.3 kWh
                                 # 0.137 * 11.9 kero
                                 # 0.058 * 12.8 lpg
                                 # 0.094 * 11.86 ulsd
                                 # 0.085 * 12.47 heating oil
                                 # 0.465 * 12.06 gasoline
                                 #  'fuel_demand': 0.137 * 11.9 + 0.058 * 12.8 + 0.094 * 11.86 + 0.085 * 12.47 + 0.465 * 12.06 / 11.3,
                                 'fuel_demand': 1,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # CF : Crude oil refinery on bibliography folder
                                 # ratio elec use / kerosene product
                                 'elec_demand': 0.008,
                                 'elec_demand_unit': 'kWh/kWh',
                                 # IEA 2022, Hydrogen,
                                 # https://www.iea.org/reports/hydrogen,
                                 # License: CC BY 4.0.
                                 # 2020 total hydrogen demand = 40Mt (calorific value 33.3 kWh/kg)
                                 # Source: IEA 2022, Data and Statistics,
                                 # https://www.iea.org/data-and-statistics/data-tables/?country=WORLD&energy=Oil&year=2019
                                 # License: CC BY 4.0.
                                 # 2019 fuel prod = 5672984+11916946+41878252+14072582+2176724+56524612+16475667 TJ
                                 # ratio for hydrogen demand = (40*33.3) /
                                 # (148717767/3.6/1000)
                                 'hydrogen_demand': (40 * 33.3) / (148717767 / 3.6 / 1000),
                                 'hydrogen_demand_unit': 'kWh/kWh',
                                 # for now constant in time but should increase
                                 # with time 10%/10year according to Fasihi2019
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.0,  # 0.15,
                                 # 22000 euro/bpd : 1 barrel = 1553,41kwh of
                                 # liquid_fuel per 24 hours
                                 # Capex initial at year 2020
                                 'Capex_init': 22000 / (1553.41 / 24.0 * 8000.0),
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 0.89,  # https://publications.anl.gov/anlpubs/2011/01/69026.pdf
                                 'techno_evo_eff': 'no',
                                 'pourcentage_of_total': 0.09,
                                 'product_break_down': product_break_down}

    techno_info_dict = techno_infos_dict_default
    energy_own_use = 2485.89  # TWh
    # Source for initial production: IEA 2022; Oil Information: Overview,
    # https://www.iea.org/reports/oil-information-overview,
    # License: CC BY 4.0.
    # in TWh at year_start from IEA (raw prod of oil products and not crude oil
    initial_production = 49472.0 - energy_own_use

    # Source for invest: IEA 2022; World Energy Investment,
    # https://www.iea.org/reports/world-energy-investment-2020,
    # License: CC BY 4.0.
    FLUE_GAS_RATIO = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(LiquidFuelTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        self.model = Refinery(self.techno_name)

    def get_chart_filter_list(self):

        chart_filters = super().get_chart_filter_list()
        chart_filters[0].extend(['Prices per flow', 'Age Distribution Production'])
        chart_filters[1].extend(['$/USgallon'])

        return chart_filters

    def get_post_processing_list(self, filters=None):
        charts = []
        price_unit_list = ['$/MWh', '$/t', "$/USgallon"]
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')
        other_fuel_dict = self.get_sosdisc_inputs('other_fuel_dict')
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        generic_filter = LiquidFuelTechnoDiscipline.get_chart_filter_list(
            self)
        instanciated_charts = LiquidFuelTechnoDiscipline.get_post_processing_list(
            self, generic_filter)

        if 'Detailed prices' in charts and '$/USgallon' in price_unit_list:
            techno_detailed_prices = self.get_sosdisc_outputs(
                GlossaryEnergy.TechnoDetailedPricesValue)
            chart_name = f'Detailed prices of {self.techno_name} technology '

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

        if 'Prices per flow' in charts and '$/USgallon' in price_unit_list:
            techno_detailed_prices = self.get_sosdisc_outputs(
                GlossaryEnergy.TechnoDetailedPricesValue)
            chart_name = f'Refinery breakdown price for {self.techno_name} technology '
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/USgallon]',
                                                 chart_name=chart_name)

            for energy in other_fuel_dict:
                # if it s a dict, so it is a data_energy_dict
                energy_price_mwh = techno_detailed_prices[self.techno_name].values * \
                                   (other_fuel_dict[energy]['calorific_value'] /
                                    data_fuel_dict['calorific_value'])

                energy_price_gal = energy_price_mwh * \
                                   data_fuel_dict['calorific_value'] * \
                                   data_fuel_dict['density'] / 1e6 * 3.78
                serie = InstanciatedSeries(
                    techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                    energy_price_gal.tolist(), f'{energy} price', 'lines')
                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(GlossaryEnergy.TechnoEnergyConsumptionValue)
        techno_production = self.get_sosdisc_outputs(GlossaryEnergy.TechnoProductionValue)
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(TWh)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != GlossaryEnergy.Years and products.endswith(
                    '(TWh)') and products != f'{LiquidFuelTechnoDiscipline.stream_name} ({GlossaryEnergy.energy_unit})':
                energy_twh = techno_production[products].values
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        # Check if we have kg in the consumption or prod :

        kg_values_consumption = 0
        reactant_found = None
        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                kg_values_consumption += 1
                reactant_found = reactant

        kg_values_production = 0
        product_found = None
        for product in techno_consumption.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                kg_values_production += 1
                product_found = product
        if kg_values_consumption == 1 and kg_values_production == 0:
            legend_title = f'{reactant_found} consumption'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        elif kg_values_production == 1 and kg_values_consumption == 0:
            legend_title = f'{product_found} production'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        else:
            chart_name = f'{self.techno_name} technology mass Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = -techno_consumption[reactant].values
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)
        for product in techno_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                legend_title = f'{product} production'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = techno_production[product].values
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts
