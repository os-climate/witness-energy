'''
Copyright 2022 Airbus SAS

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

from energy_models.core.techno_type.disciplines.biomass_dry_techno_disc import BiomassDryTechnoDiscipline
from energy_models.models.biomass_dry.unmanaged_wood.unmanaged_wood import UnmanagedWood
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart


class UnmanagedWoodDiscipline(BiomassDryTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Unmanaged Wood Biomass Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tree fa-fw',
        'version': '',
    }

    # wood residues comes from forestry residues
    # prices come from harvest, transport, chipping, drying (depending from
    # where it comes)

    techno_name = 'UnmanagedWood'
    lifetime = 150
    construction_delay = 3  # years, time for wood to dry

    # reference:
    # https://qtimber.daf.qld.gov.au/guides/wood-density-and-hardness
    wood_density = 600.0  # kg/m3
    residues_density = 150.0  # kg/m3

    # reference :
    # https://www.eubia.org/cms/wiki-biomass/biomass-resources/challenges-related-to-biomass/recovery-of-forest-residues/
    # average of 155 and 310 divided by 5
    residue_density_m3_per_ha = 46.5
    # average of 360 and 600 divided by 5
    wood_density_m3_per_ha = 96

    # in litterature, average price of residue is 30-50�/t
    # wood price is 100-200�/t => 26% between
    wood_residue_price_percent_dif = 0.34

    # 1,62% of managed wood is used for energy purpose
    # (3% of goal forest is used for energy purpose and
    # 54% of gobal forest are managed forests)
    wood_percentage_for_energy = 0.48
    residue_percentage_for_energy = 0.48

    density_per_ha = residue_density_m3_per_ha + \
        wood_density_m3_per_ha

    wood_percentage = wood_density_m3_per_ha / density_per_ha
    residue_percentage = residue_density_m3_per_ha / density_per_ha

    mean_density = wood_percentage * wood_density + \
        residue_percentage * residues_density

    # reference :
    # https://www.eubia.org/cms/wiki-biomass/biomass-resources/challenges-related-to-biomass/recovery-of-forest-residues/
    years_between_harvest = 20

    recycle_part = 0.52  # 52%

    techno_infos_dict_default = {'maturity': 5,
                                 'wood_residues_moisture': 0.35,  # 35% moisture content
                                 'wood_residue_colorific_value': 4.356,

                                 # chipping + off_road transport 8 euro/Mwh
                                 # (www.eubia.org )
                                 'Opex_percentage': 0.016,

                                 'CO2_from_production': 0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate': 0.0,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': 'years',
                                 # Capex init: 12000 $/ha to buy the land (CCUS-report_V1.30)
                                 # 1USD = 0,87360 euro in 2019
                                 'Capex_init': 10483,
                                 'Capex_init_unit': 'euro/ha',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.1447,  # in 2019, date of the paper

                                 # available planted forests in 2020: 290 Mha (worldbioenergy.org)
                                 # 40% is used for energy purpose
                                 #(7% of global area is planted forest, 3% is for energy purpose (fao.org))
                                 #'available_land': 3713490000,
                                 #'available_land_unit': 'ha',
                                 'percentage_production': 0.31,

                                 'residue_density_percentage': residue_percentage,
                                 'non_residue_density_percentage': wood_percentage,
                                 'density_per_ha': density_per_ha,

                                 'wood_percentage_for_energy': wood_percentage_for_energy,
                                 'residue_percentage_for_energy': residue_percentage_for_energy,

                                 # kg/m3,
                                 # https://qtimber.daf.qld.gov.au/guides/wood-density-and-hardness
                                 'density': mean_density,
                                 'wood_density': wood_density,
                                 'residues_density': residues_density,
                                 'density_per_ha_unit': 'm^3/ha',
                                 'efficiency': 1.0,
                                 'techno_evo_eff': 'no',  # yes or no
                                 'years_between_harvest': years_between_harvest,
                                 'recyle_part': recycle_part,
                                 'wood_residue_price_percent_dif': wood_residue_price_percent_dif,

                                 'construction_delay': construction_delay}
    # invest: no invest, regenerated naturally forests
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0, 0, 0]})
    # www.fao.org : 54% of forest under long-term management plans = 2.05 Billion Ha
    # 31% of All forests is used for production : 0.31 * 4.06 = 1.25
    # 92% of the production come from managed wood. 8% from unmanaged wood
    # 3.36 : calorific value of wood kwh/kg
    # 4.356 : calorific value of residues
    # initial_production = 1.25 * 0.92 * density_per_ha * density * 3.36  # in
    # Twh
    initial_production = 1.25 * 0.08 * \
        (residue_density_m3_per_ha * residues_density * 4.356 + wood_density_m3_per_ha *
         wood_density * 3.36) / years_between_harvest / (1 - recycle_part)  # in Twh

    # distrib computed, for planted forests since 150 years
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51,
                                                         0.51, 0.51, 0.51, 0.52, 0.51, 0.52, 0.52, 0.52, 0.52, 0.52,
                                                         0.52, 0.53, 0.53, 0.53, 0.53, 0.53, 0.53, 0.54, 0.54, 0.54,
                                                         0.54, 0.54, 0.54, 0.54, 0.55, 0.55, 0.55, 0.55, 0.55, 1.52,
                                                         1.55, 1.56, 1.56, 1.56, 0.56, 0.56, 0.56, 0.56, 0.57, 0.57,
                                                         1.52, 1.52, 0.57, 0.57, 0.57, 0.57, 0.58, 0.58, 0.58, 0.58,
                                                         0.58, 0.58, 0.58, 0.59, 0.59, 0.59, 0.59, 0.59, 0.59, 0.59,
                                                         1.52, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.61, 0.61, 0.61, 0.61,
                                                         0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.71, 0.7, 0.7, 0.71, 0.71,
                                                         0.63, 0.63, 0.64, 0.64, 0.64, 0.64, 0.64, 0.65, 0.65, 0.65,
                                                         0.65, 0.65, 0.65, 0.65, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66,
                                                         0.66, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.68, 0.68,
                                                         0.68, 0.68, 0.68, 0.68, 0.68, 0.69, 0.69, 0.69, 0.69, 0.69,
                                                         0.69, 1.53, 0.69, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.71,
                                                         0.98, 0.71, 0.71, 0.71, 0.71, 0.71]})

    # distrib computed, for planted forests since 1980 (40years)
#                                              'distrib': [3.25, 3.26, 3.27, 3.27, 3.27, 3.24, 3.21, 3.17, 3.14, 3.1,
#                                                           3.04, 2.99, 2.94, 2.89, 2.83, 2.77, 2.71, 2.66, 2.57, 2.51,
#                                                           2.47, 2.42, 2.38, 2.34, 2.3, 2.27, 2.23, 2.18, 2.14, 2.1,
# 2.06, 2.02, 1.98, 1.94, 1.9, 1.86, 1.82, 1.77, 1.73]})

    # distrib computed, for all forests since 1980 (40years)
#                                              'distrib': [2.51, 2.51, 2.51, 2.51, 2.51, 2.53, 2.52, 2.52, 2.52, 2.52,
#                                                          2.54, 2.54, 2.54, 2.53, 2.53, 2.57, 2.57, 2.57, 2.55, 2.55,
#                                                          2.59, 2.58, 2.58, 2.58, 2.58, 2.61, 2.61, 2.61, 2.6, 2.6,
# 2.6, 2.6, 2.61, 2.6, 2.6, 2.6, 2.61, 2.6, 2.59]})

#

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default,
                                     'unit': 'define in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True),
                                                                }
               },
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
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
        self.techno_model = UnmanagedWood(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def run(self):
        BiomassDryTechnoDiscipline.run(self)
        self.specific_run()

    def specific_run(self):

        outputs_dict = {'mix_detailed_prices': self.techno_model.price_mix,
                        'mix_detailed_production': self.techno_model.production_mix}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        BiomassDryTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions')

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions)

        capex = self.get_sosdisc_outputs('techno_detailed_prices')[
            f'Capex_{self.techno_name}'].values

        production, consumption = self.get_sosdisc_outputs(
            ['techno_production', 'techno_consumption'])
        production_mix = self.get_sosdisc_outputs('mix_detailed_production')
        scaling_factor_invest_level = self.get_sosdisc_inputs(
            'scaling_factor_invest_level')
        scaling_factor_techno_production = self.get_sosdisc_inputs(
            'scaling_factor_techno_production')

        grad_production = self.techno_model.grad_production_invest(
            capex, production, production_mix)

        for column in production:
            if column == f'{self.energy_name} ({self.techno_model.product_energy_unit})':
                self.set_partial_derivative_for_other_types(
                    ('techno_production', column), ('invest_level', 'invest'), grad_production[column] * self.techno_model.applied_ratio['applied_ratio'].values[:, np.newaxis] * scaling_factor_invest_level / scaling_factor_techno_production)

    def get_post_processing_list(self, filters=None):
        instanciated_charts = []
        charts = []
        price_unit_list = []
        years_list = [self.get_sosdisc_inputs('year_start')]

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
        production_mix_df = self.get_sosdisc_outputs('mix_detailed_production')
        production_df = self.get_sosdisc_outputs('techno_detailed_production')

        name_residue = f'{self.energy_name}_residue (TWh)'
        name_wood = f'{self.energy_name}_wood (TWh)'
        name_non_energy = f'{self.energy_name}_non_energy (TWh)'

        year_start = min(production_mix_df['years'].values.tolist())
        year_end = max(production_mix_df['years'].values.tolist())

        max1 = max(production_mix_df[name_residue].values.tolist())
        max2 = max(production_mix_df[name_wood].values.tolist())
        max3 = max(production_mix_df[name_non_energy].values.tolist())
        maximum = (max1 + max2 + max3) * 1.2

        min1 = min(production_mix_df[name_residue].values.tolist())
        min2 = min(production_mix_df[name_wood].values.tolist())
        min3 = min(production_mix_df[name_non_energy].values.tolist())
        minimum = min(0, min1, min2, min3) * 0.8

        chart_name = f'Production of Unmanaged wood over the years'
        new_chart = TwoAxesInstanciatedChart('years', f'Production of Unmanaged wood (TWh)',
                                             [year_start, year_end], [
                                                 minimum, maximum],
                                             chart_name=chart_name, cumulative_surface=True)

        wood_serie = InstanciatedSeries(
            production_mix_df['years'].values.tolist(),
            production_mix_df[name_wood].values.tolist(),
            f'biomass for energy from wood energy', 'lines')
        new_chart.series.append(wood_serie)

        residue_serie = InstanciatedSeries(
            production_mix_df['years'].values.tolist(),
            production_mix_df[name_residue].values.tolist(),
            f'biomass for energy from wood residue', 'lines')
        new_chart.series.append(residue_serie)

        non_energy_serie = InstanciatedSeries(
            production_mix_df['years'].values.tolist(),
            production_mix_df[name_non_energy].values.tolist(),
            f'biomass for non energy production', 'lines')
        new_chart.series.append(non_energy_serie)
        return new_chart

    def get_chart_price_in_dollar_kg(self):
        price_mix_df = self.get_sosdisc_outputs('mix_detailed_prices')
        name_residue = f'{self.energy_name}_residue'
        name_wood = f'{self.energy_name}_wood'

        chart_name = f'Detailed Price of Unmanaged wood technology over the years'

        year_start = min(price_mix_df['years'].values.tolist())
        year_end = max(price_mix_df['years'].values.tolist())

        max1 = max(price_mix_df[name_residue].values.tolist())
        max2 = max(price_mix_df[name_wood].values.tolist())
        maximum = max(max1, max2) * 1.2 * \
            self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
        new_chart = TwoAxesInstanciatedChart('years', f'Production of Unmanaged wood ($/t)',
                                             [year_start, year_end], [0.0, maximum], chart_name=chart_name)

        residue_serie = InstanciatedSeries(
            price_mix_df['years'].values.tolist(),
            (price_mix_df[name_residue].values *
             self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']).tolist(),
            f'price of wood residue', 'lines')
        new_chart.series.append(residue_serie)

        wood_serie = InstanciatedSeries(
            price_mix_df['years'].values.tolist(),
            (price_mix_df[name_wood].values *
             self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']).tolist(),
            f'price of wood energy', 'lines')
        new_chart.series.append(wood_serie)

        return new_chart

    def get_chart_price_in_dollar_Mwh(self):
        price_mix_df = self.get_sosdisc_outputs('mix_detailed_prices')
        name_residue = f'{self.energy_name}_residue'
        name_wood = f'{self.energy_name}_wood'

        chart_name = f'Detailed Price of Unmanaged wood technology over the years'
        techno_price = self.get_sosdisc_outputs('techno_detailed_prices')
        year_start = min(price_mix_df['years'].values.tolist())
        year_end = max(price_mix_df['years'].values.tolist())

        max1 = max(price_mix_df[name_residue].values.tolist())
        max2 = max(price_mix_df[name_wood].values.tolist())
        maximum = max(max1, max2) * 1.2
        new_chart = TwoAxesInstanciatedChart('years', f'Production of Unmanaged wood ($/MWh)',
                                             [year_start, year_end], [0.0, maximum], chart_name=chart_name)

        residue_serie = InstanciatedSeries(
            price_mix_df['years'].values.tolist(),
            price_mix_df[name_residue].values.tolist(),
            f'price of wood residue', 'lines')
        new_chart.series.append(residue_serie)

        wood_serie = InstanciatedSeries(
            price_mix_df['years'].values.tolist(),
            price_mix_df[name_wood].values.tolist(),
            f'price of wood energy', 'lines')
        new_chart.series.append(wood_serie)

        return new_chart

    def get_chart_initial_production(self):
        # surcharge of the methode in techno_disc to change historical data with the
        # energy part
        year_start = self.get_sosdisc_inputs(
            'year_start')
        initial_production = self.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = self.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = pd.DataFrame({'age': initial_age_distrib['age'].values,
                                     'distrib': initial_age_distrib['distrib'].values, })

        techno_infos_dict = self.get_sosdisc_inputs(
            'techno_infos_dict')
        wood_percentage_for_non_energy = 1 - \
            techno_infos_dict['wood_percentage_for_energy']
        wood_density = techno_infos_dict['non_residue_density_percentage']
        residue_percentage_for_non_energy = 1 - \
            techno_infos_dict['residue_percentage_for_energy']
        residue_density = techno_infos_dict['residue_density_percentage']

        non_energy_percentage = (wood_percentage_for_non_energy * wood_density +
                                 residue_percentage_for_non_energy * residue_density)

        initial_prod['energy (TWh)'] = initial_prod['distrib'] / \
            100.0 * initial_production * (1 - non_energy_percentage)
        initial_prod['years'] = year_start - initial_prod['age']
        initial_prod.sort_values('years', inplace=True)
        initial_prod['cum energy (TWh)'] = initial_prod['energy (TWh)'].cumsum(
        )
        study_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.energy_name} World Production for energy via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart('years', f'{self.energy_name} production for energy (TWh)',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            initial_prod['years'].values.tolist(),
            initial_prod[f'cum energy (TWh)'].values.tolist(), 'Initial production for energy by 2020 factories', 'lines')

        study_prod = study_production[f'{self.energy_name} (TWh)'].values
        new_chart.series.append(serie)
        years_study = study_production['years'].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(
            0, initial_prod[f'cum energy (TWh)'].values.tolist()[-1])
        serie = InstanciatedSeries(
            years_study,
            study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)

        return new_chart
