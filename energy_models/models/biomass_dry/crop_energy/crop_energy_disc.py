'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/09 Copyright 2023 Capgemini

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
from energy_models.core.techno_type.disciplines.biomass_dry_techno_disc import BiomassDryTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.biomass_dry.crop_energy.crop_energy import CropEnergy
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2


class CropEnergyDiscipline(BiomassDryTechnoDiscipline):
    '''
        Crop energy is the technology that transforms crops and crops residues
        for energy into biomass_dry
    '''

    # ontology information
    _ontology_data = {
        'label': 'Crop Energy Biomass Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tractor fa-fw',
        'version': '',
    }
    techno_name = 'CropEnergy'
    lifetime = 50
    construction_delay = 1  # years

    # mdpi: according to the NASU recommendations,
    # a fixed value of 0.25 is applied to all crops
    # 50% of crops are left on the field,
    # 50% of the left on the field can be used as crop residue =>
    # 25% of the crops is residue
    residue_percentage = 0.25

    # bioenergyeurope.org : Dedicated energy crops
    # represent 0.1% of the total biomass production in 2018
    energy_crop_percentage = 0.005

    # 23$/t for residue, 60$/t for crop
    crop_residue_price_percent_dif = 23 / 60

    # ourworldindata, average cereal yield: 4070t/ha +
    # average yield of switchgrass on grazing lands: 2565,67t/ha
    # residue is 0.25 more than that
    density_per_ha = 2903 * 1.25

    techno_infos_dict_default = {'maturity': 5,
                                 # computed 87.7euro/ha, counting harvest,
                                 # fertilizing, drying...from gov.mb.ca
                                 # plus removing residue price:
                                 # FACT_Sheet_Harvesting_Crop_Residues_-_revised_2016-2
                                 # 22$/t for harvest residue + 23$/t for
                                 # fertilizing => 37.5euro/ha for residues
                                 'Opex_percentage': 0.52,
                                 'Opex_percentage_for_residue_only': 0.15,
                                 # CO2 from production from tractor is taken
                                 # into account into the energy net factor
                                 'CO2_from_production': - 0.425 * 44.01 / 12.0,  # same as biomass_dry
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate':  0.0,  # augmentation of forests ha per year?
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryCore.Years,
                                 # capex from
                                 # gov.mb.ca/agriculture/farm-management/production-economics/pubs/cop-crop-production.pdf
                                 # 237.95 euro/ha (717 $/acre)
                                 # 1USD = 0,82 euro in 2021
                                 'Capex_init': 237.95,
                                 'Capex_init_unit': 'euro/ha',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.2195,  # in 2021, date of the paper
                                 'density_per_ha': density_per_ha,  # average, worldbioenergy.org
                                 'density_per_ha_unit': 'kg/ha',
                                 'residue_density_percentage': residue_percentage,
                                 'crop_percentage_for_energy': energy_crop_percentage,
                                 'residue_percentage_for_energy': 0.05,  # hypothesis
                                 'efficiency': 1.0,
                                 'techno_evo_eff': 'no',
                                 'crop_residue_price_percent_dif': crop_residue_price_percent_dif,

                                 'construction_delay': construction_delay}

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [0]})
    # available ha of crop: 4.9Gha, initial prod = crop energy + residue for
    # energy of all surfaces
    initial_production = 4.8 * density_per_ha * \
        3.36 * energy_crop_percentage   # in Twh
    # Age distribution of forests in 2008 (
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.16, 0.24, 0.31, 0.39, 0.47, 0.55, 0.63, 0.71, 0.78, 0.86,
                                                         0.94, 1.02, 1.1, 1.18, 1.26, 1.33, 1.41, 1.49, 1.57, 1.65,
                                                         1.73, 1.81, 1.88, 1.96, 2.04, 2.12, 2.2, 2.28, 2.35, 2.43,
                                                         2.51, 2.59, 2.67, 2.75, 2.83, 2.9, 2.98, 3.06, 3.14, 3.22,
                                                         3.3, 3.38, 3.45, 3.53, 3.61, 3.69, 3.77, 3.85, 3.92]})
    # The increase in land is of 10Mha each year, in CAPEX and OPEX
    land_surface_for_food = pd.DataFrame({GlossaryCore.Years: np.arange(2020, 2101),
                                          'Agriculture total (Gha)': np.ones(81) * 4.8})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryCore.Years: ('int', [1900, 2100], False),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True),
                                                                }
                                       },
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int', [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float', None, True)},
                                        'dataframe_edition_locked': False},
               CropEnergy.LAND_SURFACE_FOR_FOOD_DF: {'type': 'dataframe', 'unit': 'Gha',
                                                     'visibility': BiomassDryTechnoDiscipline.SHARED_VISIBILITY,
                                                     'namespace': 'ns_witness',
                                                     'default': land_surface_for_food,
                                                     'dataframe_descriptor': {GlossaryCore.Years: ('int',  [1900, 2100], False),
                                                                              'Agriculture total (Gha)': ('float', None, True),},
                                                     'dataframe_edition_locked': False}}
    # -- add specific techno inputs to this
    DESC_IN.update(BiomassDryTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = {
        'mix_detailed_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        'mix_detailed_production': {'type': 'dataframe', 'unit': 'TWh or Mt'},
    }
    DESC_OUT.update(BiomassDryTechnoDiscipline.DESC_OUT)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CropEnergy(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def run(self):
        '''
        specific run for crops 
        '''
        # -- get inputs
        super().run()
        self.specific_run()

    def specific_run(self):
        '''
        Retrieve specific outputs
        '''
        outputs_dict = {'mix_detailed_prices': self.techno_model.price_mix,
                        'mix_detailed_production': self.techno_model.production_mix}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        super().compute_sos_jacobian()

        scaling_factor_techno_production = self.get_sosdisc_inputs(
            'scaling_factor_techno_production')
        scaling_factor_techno_consumption = self.get_sosdisc_inputs(
            'scaling_factor_techno_consumption')
        inputs_dict = self.get_sosdisc_inputs()
        invest_level = inputs_dict[GlossaryCore.InvestLevelValue]
        scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']

        d_prod_dland_for_food = self.techno_model.compute_grad_dprod_dland_for_food()
        d_conso_dland_for_food = self.techno_model.compute_grad_dconso_dland_for_food()

        self.set_partial_derivative_for_other_types(
            (GlossaryCore.TechnoProductionValue, f'{self.energy_name} ({self.techno_model.product_energy_unit})'), (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), d_prod_dland_for_food / scaling_factor_techno_production)
        self.set_partial_derivative_for_other_types(
            (GlossaryCore.TechnoConsumptionValue, f'{CO2.name} (Mt)'), (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), d_conso_dland_for_food / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryCore.TechnoConsumptionWithoutRatioValue, f'{CO2.name} (Mt)'), (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), d_conso_dland_for_food / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoCapitalDfValue, GlossaryCore.Capital), (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), d_prod_dland_for_food / scaling_factor_techno_production)

        dcapex_dinvest = self.techno_model.compute_dcapex_dinvest(
            invest_level.loc[invest_level[GlossaryCore.Years]
                             <= self.techno_model.year_end][GlossaryCore.InvestValue].values * scaling_factor_invest_level, self.techno_model.techno_infos_dict, self.techno_model.initial_production)

        dnon_use_capital_dinvest, dtechnocapital_dinvest = self.techno_model.compute_dnon_usecapital_dinvest(
            dcapex_dinvest, d_prod_dland_for_food / scaling_factor_techno_production)
        self.set_partial_derivative_for_other_types(
            ('non_use_capital', self.techno_model.name), (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), dnon_use_capital_dinvest)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoCapitalDfValue, GlossaryCore.Capital),
            (CropEnergy.LAND_SURFACE_FOR_FOOD_DF, 'Agriculture total (Gha)'), dtechnocapital_dinvest)

    def get_post_processing_list(self, filters=None):
        charts = []
        price_unit_list = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        generic_filter = BiomassDryTechnoDiscipline.get_chart_filter_list(self)
        instanciated_charts = BiomassDryTechnoDiscipline.get_post_processing_list(
            self, generic_filter)

        if 'Consumption and production' in charts:
            production_chart = self.get_production_chart()
            instanciated_charts.append(production_chart)

        if 'Detailed prices' in charts:
            if '$/MWh' in price_unit_list:
                price_chart_Mwh = self.get_chart_price_in_dollar_Mwh()
                instanciated_charts.append(price_chart_Mwh)
            if '$/t' in price_unit_list:
                price_chart = self.get_chart_price_in_dollar_kg()
                instanciated_charts.append(price_chart)

        return instanciated_charts

    def get_production_chart(self):
        '''
        Create chart with production details for industry/energy 
        '''
        production_mix_df = self.get_sosdisc_outputs('mix_detailed_production')

        name_residue = f'{self.energy_name}_residue (TWh)'
        name_crop = f'{self.energy_name}_crop (TWh)'
        name_non_energy = f'{self.energy_name}_non_energy (TWh)'
        name_residue_non_energy = f'{self.energy_name}_residue_non_energy (TWh)'

        year_start = min(production_mix_df[GlossaryCore.Years].values.tolist())
        year_end = max(production_mix_df[GlossaryCore.Years].values.tolist())

        max1 = max(production_mix_df[name_residue].values.tolist())
        max2 = max(production_mix_df[name_crop].values.tolist())
        max3 = max(production_mix_df[name_non_energy].values.tolist())
        max4 = max(production_mix_df[name_residue_non_energy].values.tolist())
        maximum = (max1 + max2 + max3 + max4) * 1.2

        min1 = min(production_mix_df[name_residue].values.tolist())
        min2 = min(production_mix_df[name_crop].values.tolist())
        min3 = min(production_mix_df[name_non_energy].values.tolist())
        min4 = min(production_mix_df[name_residue_non_energy].values.tolist())
        minimum = min(0, min1, min2, min3, min4) * 0.8

        chart_name = f'Production of Crop over the years'
        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, f'Production of Crop (TWh)',
                                             [year_start, year_end], [
                                                 minimum, maximum],
                                             chart_name=chart_name, cumulative_surface=True)

        wood_serie = InstanciatedSeries(
            production_mix_df[GlossaryCore.Years].values.tolist(),
            production_mix_df[name_crop].values.tolist(),
            f'biomass for energy from crop energy', 'lines')
        new_chart.series.append(wood_serie)

        residue_serie = InstanciatedSeries(
            production_mix_df[GlossaryCore.Years].values.tolist(),
            production_mix_df[name_residue].values.tolist(),
            f'biomass for energy from crop residue', 'lines')
        new_chart.series.append(residue_serie)

        residue_non_energy_serie = InstanciatedSeries(
            production_mix_df[GlossaryCore.Years].values.tolist(),
            production_mix_df[name_residue_non_energy].values.tolist(),
            f'biomass from residue for non energy production', 'lines')
        new_chart.series.append(residue_non_energy_serie)

        non_energy_serie = InstanciatedSeries(
            production_mix_df[GlossaryCore.Years].values.tolist(),
            production_mix_df[name_non_energy].values.tolist(),
            f'biomass from crop for non energy production', 'lines')
        new_chart.series.append(non_energy_serie)

        return new_chart

    def get_chart_price_in_dollar_kg(self):
        '''
        Create chart for residue and wood price in dollar/kg
        '''
        price_mix_df = self.get_sosdisc_outputs('mix_detailed_prices')
        name_residue = f'{self.energy_name}_residue'
        name_crop = f'{self.energy_name}_crop'

        chart_name = f'Price of Crop energy technology over the years'

        year_start = min(price_mix_df[GlossaryCore.Years].values.tolist())
        year_end = max(price_mix_df[GlossaryCore.Years].values.tolist())

        max1 = max(price_mix_df[name_residue].values.tolist())
        max2 = max(price_mix_df[name_crop].values.tolist())
        maximum = max(max1, max2) * 1.2 * \
            self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, f'Price of Crop energy ($/t)',
                                             [year_start, year_end], [0.0, maximum], chart_name=chart_name)

        residue_serie = InstanciatedSeries(
            price_mix_df[GlossaryCore.Years].values.tolist(),
            (price_mix_df[name_residue].values *
             self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']).tolist(),
            f'price of crop residue', 'lines')
        new_chart.series.append(residue_serie)

        wood_serie = InstanciatedSeries(
            price_mix_df[GlossaryCore.Years].values.tolist(),
            (price_mix_df[name_crop].values *
             self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']).tolist(),
            f'price of crop energy', 'lines')
        new_chart.series.append(wood_serie)

        return new_chart

    def get_chart_price_in_dollar_Mwh(self):
        '''
        Create chart for residue and wood price in dollar/MWh
        '''
        price_mix_df = self.get_sosdisc_outputs('mix_detailed_prices')
        name_residue = f'{self.energy_name}_residue'
        name_crop = f'{self.energy_name}_crop'

        chart_name = f'Price of Crop energy technology over the years'
        year_start = min(price_mix_df[GlossaryCore.Years].values.tolist())
        year_end = max(price_mix_df[GlossaryCore.Years].values.tolist())

        max1 = max(price_mix_df[name_residue].values.tolist())
        max2 = max(price_mix_df[name_crop].values.tolist())
        maximum = max(max1, max2) * 1.2
        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, f'Price of Crop energy ($/MWh)',
                                             [year_start, year_end], [0.0, maximum], chart_name=chart_name)

        residue_serie = InstanciatedSeries(
            price_mix_df[GlossaryCore.Years].values.tolist(),
            price_mix_df[name_residue].values.tolist(),
            f'price of crop residue', 'lines')
        new_chart.series.append(residue_serie)

        wood_serie = InstanciatedSeries(
            price_mix_df[GlossaryCore.Years].values.tolist(),
            price_mix_df[name_crop].values.tolist(),
            f'price of crop energy', 'lines')
        new_chart.series.append(wood_serie)

        return new_chart

    def get_chart_initial_production(self):
        '''
         surcharge of the methode in techno_disc to change historical data with the
         energy part
        '''
        year_start = self.get_sosdisc_inputs(
            GlossaryCore.YearStart)
        land_surface_for_food = self.get_sosdisc_inputs(
            CropEnergy.LAND_SURFACE_FOR_FOOD_DF)
        initial_production = self.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = self.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = pd.DataFrame({'age': initial_age_distrib['age'].values,
                                     'distrib': initial_age_distrib['distrib'].values, })

        techno_infos_dict = self.get_sosdisc_inputs(
            'techno_infos_dict')

        # Compute initial distrib prod with the agricultural land for food
        residue_food_production_init = land_surface_for_food['Agriculture total (Gha)'][0] *\
            techno_infos_dict['residue_density_percentage'] *\
            techno_infos_dict['density_per_ha'] * \
            self.get_sosdisc_inputs('data_fuel_dict')['high_calorific_value'] *\
            techno_infos_dict['residue_percentage_for_energy']
        initial_prod['energy (TWh)'] = initial_prod['distrib'] / \
            100.0 * initial_production
        initial_prod[GlossaryCore.Years] = year_start - initial_prod['age']
        initial_prod.sort_values(GlossaryCore.Years, inplace=True)
        initial_prod['cum energy (TWh)'] = initial_prod['energy (TWh)'].cumsum(
        )
        study_production = self.get_sosdisc_outputs(
            GlossaryCore.TechnoDetailedProductionValue)
        chart_name = f'{self.energy_name} World Production for energy via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, f'{self.energy_name} production for energy (TWh)',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            initial_prod[GlossaryCore.Years].values.tolist(),
            (initial_prod[f'cum energy (TWh)'].values +
             residue_food_production_init).tolist(),
            'Initial production for energy by 2020 factories', 'lines')

        study_prod = study_production[f'{self.energy_name} (TWh)'].values
        new_chart.series.append(serie)
        years_study = study_production[GlossaryCore.Years].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(
            0, initial_prod[f'cum energy (TWh)'].values.tolist()[-1] + residue_food_production_init)
        serie = InstanciatedSeries(
            years_study,
            study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)

        return new_chart
