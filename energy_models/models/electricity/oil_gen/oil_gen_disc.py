'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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
from energy_models.models.electricity.oil_gen.oil_gen import OilGen
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class OilGenDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Oil Generation Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-industry fa-fw',
        'version': '',
    }
    techno_name = 'OilGen'
    lifetime = 46
    # Source: Cui, R.Y., Hultman, N., Edwards, M.R., He, L., Sen, A., Surana, K., McJeon, H., Iyer, G., Patel, P., Yu, S. and Nace, T., 2019.
    # Quantifying operational lifetimes for coal power plants under the Paris
    # goals. Nature communications, 10(1), pp.1-9.
    construction_delay = 5  # For 1000MW hypercritical in Korea
    techno_infos_dict_default = {'maturity': 0,
                                 'product': 'electricity',
                                 # Lorenczik, S., Kim, S., Wanner, B., Bermudez Menendez, J.M., Remme, U., Hasegawa,
                                 # T., Keppler, J.H., Mir, L., Sousa, G., Berthelemy, M. and Vaya Soler, A., 2020.
                                 # Projected Costs of Generating Electricity-2020 Edition (No. NEA--7531).
                                 # Organisation for Economic Co-Operation and Development.
                                 # U.S. Energy Information Association
                                 # Levelized Costs of New Generation Resources in the Annual Energy Outlook 2021
                                 # IEA 2022, World Energy Outlook 2014, IEA,
                                 # Paris
                                 # https://www.iea.org/reports/world-energy-outlook-2014,
                                 # License: CC BY 4.0.
                                 'Opex_percentage': 0.0339,  # Mean of IEA World Energy Outlook 2014

                                 # RTE France
                                 # https://www.rte-france.com/en/eco2mix/co2-emissions
                                 'CO2_from_production': 0.777,
                                 'CO2_from_production_unit': 'kg/kWh',
                                 # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR55-GAINS-N2O.pdf
                                 # 0.008 kt/PJ
                                 'N2O_emission_factor': 0.008e-3 / 0.277,
                                 'N2O_emission_factor_unit': 'Mt/TWh',
                                 # IEA 2022, Levelised Cost of Electricity Calculator,
                                 # IEA and NEA, Paris
                                 # https://www.iea.org/articles/levelised-cost-of-electricity-calculator
                                 # License: CC BY 4.0.
                                 # keep the same as coal generator (see:
                                 # https://www.duke-energy.com/energy-education/how-energy-works/oil-and-gas-electricity)
                                 'elec_demand': 0.16,
                                 'elec_demand_unit': 'kWh/kWh',

                                 # Source: IEA 2022
                                 # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Balances&year=2019
                                 # License: CC BY 4.0.
                                 # 5727280 TJ oil demand --> 1590.91 TWh
                                 # initial prod = 747.171 TWh
                                 'fuel_demand': 1590.91 / 747.171,  # at 100% efficiency
                                 'fuel_demand_unit': 'kWh/kWh',

                                 'WACC': 0.075,
                                 # Rubin, E.S., Azevedo, I.M., Jaramillo, P. and Yeh, S., 2015.
                                 # A review of learning rates for electricity supply technologies.
                                 # Energy Policy, 86, pp.198-218.
                                 # https://www.cmu.edu/epp/iecm/rubin/PDF%20files/2015/A%20review%20of%20learning%20rates%20for%20electricity%20supply%20technologies.pdf
                                 'learning_rate': 0.083,
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryCore.Years,

                                 # ESMAP, Study of Equipment Prices in the Power Sector, 2009
                                 # https://esmap.org/sites/default/files/esmap-files/TR122-09_GBL_Study_of_Equipment_Prices_in_the_Power_Sector.pdf
                                 # (mean value p46)
                                 'Capex_init': 1380,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760,

                                 # Water Demand
                                 # https://www.sciencedirect.com/science/article/pii/S1364032119305994#:~:text=Oil%20is%20a%20large%20water,)%20%5B26%2C35%5D.
                                 # 891L/MWh
                                 'water_demand': 0.891,
                                 'water_demand_unit': 'kg/kWh',

                                 # EIA, U., 2021. Electric Power Monthly,
                                 # Table 6.07.A. Capacity Factors for Utility Scale Generators Primarily Using Fossil Fuels
                                 # https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_6_07_a
                                 'capacity_factor': 0.139,  # Average value in the US in 2020
                                 'transport_cost_unit': '$/kg',  # check if pertinent
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1,
                                 'construction_delay': construction_delay,
                                 'copper_needs': 1100,  #no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    techno_info_dict = techno_infos_dict_default

    # In TWh at year_start source: IEA 2022, Data Tables,
    # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Electricity&year=2019,
    # License: CC BY 4.0.
    initial_production = 747.171

    # Source for Invest before year start in $:
    # IEA 2022, World Energy Investment 2019,
    # https://www.iea.org/reports/world-energy-investment-2019/power-sector
    # License: CC BY 4.0.
    # (linear from 2016, 2017, 2018 data)
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [21.0, 20.0, 19.0, 18.0, 17.0]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                                                         1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                                                         2.6, 2.6, 2.6, 2.6, 2.6,
                                                         3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25,
                                                         3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25,
                                                         ]})

    oil_flue_gas_ratio = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               'flue_gas_co2_ratio': {'type': 'array', 'default': oil_flue_gas_ratio, 'unit': ''},
               }

    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = OilGen(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
    
    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryCore.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryCore.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.Copper['name'] in product :
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryCore.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.Copper['name'] in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000 #convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryCore.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)
        
        return instanciated_chart