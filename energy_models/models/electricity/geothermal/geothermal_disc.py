'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/03-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.geothermal.geothermal import Geothermal
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class GeothermalDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Geothermal Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-temperature-high fa-fw',
        'version': '',
    }
    techno_name = 'Geothermal'
    # Tsiropoulos, I., Tarvydas, D. and Zucker, A., 2018.
    # Cost development of low carbon energy technologies-Scenario-based cost trajectories to 2050, 2017 Edition.
    # Publications Office of the European Union, Luxemburgo.
    lifetime = 30
    # Cole, W.J., Gates, N., Mai, T.T., Greer, D. and Das, P., 2020.
    # 2019 standard scenarios report: a US electric sector outlook (No. NREL/PR-6A20-75798).
    # National Renewable Energy Lab.(NREL), Golden, CO (United States).
    construction_delay = 7

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.045,
                                 # Fixed 4.0% and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.048,  # Weighted averaged cost of capital / ATB NREL 2020
                                 # Zucker, A., 2018. Cost development of low carbon energy technologies.
                                 # https://publications.jrc.ec.europa.eu/repository/bitstream/JRC109894/cost_development_of_low_carbon_energy_technologies_v2.2_final_online.pdf
                                 'learning_rate': 0.05,
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # Timilsina, G.R., 2020.
                                 # Demystifying the Costs of Electricity Generation Technologies.
                                 # https://openknowledge.worldbank.org/bitstream/handle/10986/34018/Demystifying-the-Costs-of-Electricity-Generation-Technologies.pdf?sequence=4
                                 'Capex_init': 4275,  # average
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies
                                 'capacity_factor': 0.85,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 0.16,
                                 # https://www.sciencedirect.com/science/article/abs/pii/S0375650513001120
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'copper_needs': 1100,
                                 # no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 621 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    initial_production = 92

    # Invest from IRENA
    # Renewable Power Generation Costs in 2020
    # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [2.4, 2.9, 2.5,
                                                                                       2.7, 2.4, 2.5,
                                                                                       1.2]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 9.800600043, 7.549068948, 6.398734632, 5.909842548, 8.986986843,
                                                 6.916385074, 3.867999137, 6.614422316, 0, 3.192177727, 6.326838738,
                                                 4.600337264, 3.177798548, 3.335969516, 2.05622259, 2.05622259,
                                                 2.05622259, 1.567330505, 2.530735495, 3.2784528, 3.2784528,
                                                 3.2784528, 3.220936085, 0, 0, 0, 0, 0, 0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Geothermal(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.CopperResource in product:
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryEnergy.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.CopperResource in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000  # convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)

        return instanciated_chart
