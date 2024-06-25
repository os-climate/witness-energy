'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.gas.gas_elec import GasElec


class GasTurbineDiscipline(ElectricityTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Gas Turbine Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }

    techno_name = GlossaryEnergy.GasTurbine
    lifetime = 30  # Source U.S. Energy Information Administration 2020
    construction_delay = 2  # years #Lazard
    # Taud, R., Karg, J. and O'Leary, D., 1999.
    # Gas turbine based power plants: technology and market status.
    # The World Bank Energy Issues, (20).
    # https://documents1.worldbank.org/curated/en/640981468780885410/pdf/263500Energy0issues020.pdf
    heat_rate = 9.2  # 8.0-10. 5    Gj/Mwh
    # Convert heat rate into kwh/kwh
    # Corresponds to 39.1 % of efficiency , 46% is the record
    methane_needs = heat_rate / 3.6
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.019,  # World bank
                                 # C. KOST, S. SHAMMUGAM, V. FLURI, D. PEPER, A.D. MEMAR, T. SCHLEGL,
                                 # FRAUNHOFER INSTITUTE FOR SOLAR ENERGY SYSTEMS ISE
                                 # LEVELIZED COST OF ELECTRICITY RENEWABLE
                                 # ENERGY TECHNOLOGIES, June 2021
                                 'WACC': 0.075,  # fraunhofer
                                 'learning_rate': 0,  # fraunhofer
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 # 0.1025 kt/PJ (mean) at gas power plants in
                                 # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
                                 'CH4_emission_factor': 0.1025e-3 / 0.277,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR55-GAINS-N2O.pdf
                                 # 0.0001 kt/PJ
                                 'N2O_emission_factor': 0.0001e-3 / 0.277,
                                 'N2O_emission_factor_unit': 'Mt/TWh',
                                 # Source: U.S. Energy Information Administration, 2020
                                 # Capital Cost and Performance Characteristic Estimates for Utility Scale Electric Power Generating Technologies,
                                 # https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2020.pdf
                                 'Capex_init': 713,  # $/KW 2020 Source: U.S. Energy Information Administration
                                 'Capex_init_unit': '$/kW',
                                 'capacity_factor': 0.85,  # World bank
                                 'kwh_methane/kwh': methane_needs,
                                 'efficiency': 1,
                                 'techno_evo_eff': 'no',  # yes or no
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'full_load_hours': 8760,
                                 'copper_needs': 1100,
                                 # IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    # Major hypo: 25% of invest in gas go into gas turbine, 75% into CCGT
    share = 0.75
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [0.0, 51.0 * (1 - share)]})
    # For initial production: MAJOR hypothesis, took IEA WEO 2019 production for 2018
    # Source for initial production: IEA 2022, World Energy Outlook, https://www.iea.org/reports/world-energy-outlook-2018, License: CC BY 4.0.
    # In US according to U.S. Energy Information Administration  53% of capa
    # from CCGT and 47 for GT in 2017
    share_ccgt = 0.75
    # Initial prod in TWh
    initial_production = (1 - share_ccgt) * 6346
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [2.83, 1.76, 2.3, 2.58, 2.26, 0.9, 0.82, 3.37, 7.77,
                                                         13.53, 12.39, 4.53, 3.42, 3.17, 2.52, 2.1, 3.3,
                                                         2.15, 3.35, 2.89, 2.52, 2.13, 2.11, 2.65, 3.32,
                                                         2.99, 2.65, 2.49, 1.2]})
    FLUE_GAS_RATIO = np.array([0.0350])

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
                                                               'dataframe_edition_locked': False}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = GasElec(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
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
