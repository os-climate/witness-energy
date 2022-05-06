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
from energy_models.models.electricity.coal_gen.coal_gen import CoalGen
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline


class CoalGenDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Coal Generation Model',
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
    techno_name = 'CoalGen'
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
                                 # IEA (2014), World Energy Outlook 2014, IEA,
                                 # Paris
                                 # https://www.iea.org/reports/world-energy-outlook-2014
                                 'Opex_percentage': 0.0339,  # Mean of IEA World Energy Outlook 2014
                                 # Bruckner, T., Bashmakov, I.A., Mulugetta, Y., Chum, H., De la Vega Navarro, A., Edmonds,
                                 # J., Faaij, A., Fungtammasan, B., Garg, A., Hertwich, E. and Honnery, D., 2014.
                                 # Energy systems. IPCC
                                 # https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_chapter7.pdf
                                 # Or for a simplified chart:
                                 # https://www.world-nuclear.org/information-library/energy-and-the-environment/carbon-dioxide-emissions-from-electricity.aspx
                                 'CO2_from_production': 0.82,
                                 'CO2_from_production_unit': 'kg/kWh',
                                 # IEA (2020), Levelised Cost of Electricity Calculator,
                                 #IEA and NEA, Paris
                                 # https://www.iea.org/articles/levelised-cost-of-electricity-calculator
                                 'elec_demand': 0.16,
                                 'elec_demand_unit': 'kWh/kWh',
                                 # IEA (2015), Projected Costs of Generating Electricity 2015,
                                 #IEA, Paris
                                 # https://www.iea.org/reports/projected-costs-of-generating-electricity-2015
                                 'fuel_demand': 0.836,  # at 100% efficiency
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # Renewable Power Generation Costs in 2020
                                 #IRENA, 2020
                                 # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
                                 'WACC': 0.075,
                                 # Rubin, E.S., Azevedo, I.M., Jaramillo, P. and Yeh, S., 2015.
                                 # A review of learning rates for electricity supply technologies.
                                 # Energy Policy, 86, pp.198-218.
                                 # https://www.cmu.edu/epp/iecm/rubin/PDF%20files/2015/A%20review%20of%20learning%20rates%20for%20electricity%20supply%20technologies.pdf
                                 'learning_rate': 0.083,
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # IEA (2014), World Energy Outlook 2014, IEA, Paris
                                 # https://www.iea.org/reports/world-energy-outlook-2014
                                 'Capex_init': 1900,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760,
                                 'water_demand': 2.22,
                                 'water_demand_unit': 'kg/kWh',
                                 # EIA, U., 2021. Electric Power Monthly,
                                 # Table 6.07.A. Capacity Factors for Utility Scale Generators Primarily Using Fossil Fuels
                                 # https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_6_07_a
                                 'capacity_factor': 0.405,  # Average value in the US in 2020
                                 'transport_cost_unit': '$/kg',  # check if pertinent
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 # efficiency computed to match IEA datas
                                 'efficiency': 0.41,
                                 'efficiency_max': 0.48,
                                 'efficiency evolution slope': 0.5,
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default
    initial_production = 9914.45  # in TWh at year_start source IEA 2019
    # Invest before year start in $ source IEA 2019
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0.0, 87.0, 76.5, 90.0, 67.5]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [2.6, 2.6, 2.6, 2.6, 2.6, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                                                         1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                                                         1.1, 1.1, 1.1, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25,
                                                         3.25, 3.25, 3.25,
                                                         3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25,

                                                         ]})
    coal_flue_gas_ratio = np.array([0.13])
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               'flue_gas_co2_ratio': {'type': 'array', 'default': coal_flue_gas_ratio, 'unit': ''}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CoalGen(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
