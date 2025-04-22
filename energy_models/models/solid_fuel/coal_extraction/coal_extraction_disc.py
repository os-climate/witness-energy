'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.disciplines.solid_fuel_techno_disc import (
    SolidFuelTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.solid_fuel.coal_extraction.coal_extraction import (
    CoalExtraction,
)


class CoalExtractionDiscipline(SolidFuelTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Coal Extraction Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cube fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.CoalExtraction

    # Most coal seams are too deep underground for opencast mining and require
    # underground mining, a method that currently accounts for about 60
    # percent of world coal production. Wikipedia source :
    # https://en.wikipedia.org/wiki/Coal_mining
    # https://globalenergymonitor.org/wp-content/uploads/2021/03/Coal-Mine-Methane-On-the-Brink.pdf
    # Gas content mean for surface mining is 2.25m3/t
    # Gas content mean for underground mining is 11.5m3/t
    techno_infos_dict_default = {'maturity': 0,
                                 'product': '',
                                 'Opex_percentage': 0.20,
                                 # Pandey, B., Gautam, M. and Agrawal, M., 2018.
                                 # Greenhouse gas emissions from coal mining activities and their possible mitigation strategies.
                                 # In Environmental carbon footprints (pp.
                                 # 259-294). Butterworth-Heinemann.
                                 'CO2_flue_gas_intensity_by_prod_unit': 0.64,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'underground_mining_gas_content': 11.5,
                                 'surface_mining_gas_content': 2.25,
                                 'gas_content_unit': 'm3/t',
                                 'underground_mining_percentage': 60.,
                                 'emission_factor_coefficient': 1.6,
                                 'ch4_from_abandoned_mines': 15.,
                                 'ch4_from_abandoned_mines_unit': 'Mt',
                                 'fuel_demand': 0.0040,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # CF : Crude oil refinery on bibliography folder
                                 # ratio elec use / kerosene product
                                 'elec_demand': 0.01,
                                 'elec_demand_unit': 'kWh/kWh',
                                 GlossaryEnergy.electricity: 'solar',
                                 'heat_demand': 0.0,
                                 'heat_demand_unit': 'kWh/kWh',
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.0,  # 0.15,
                                 # Estimating average total cost of open pit coal mines in Australia
                                 # Average : 5Mtcoal/year for 258M Australian$
                                 #  -- 1AU$ = 0.77$
                                 'Capex_init': 0.0083,
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'CO2_capacity_peryear': 3.6E+8,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 'water_demand': 0.0,
                                 'water_demand_unit': '',
                                 'produced_energy': 0.0,
                                 'direct_energy': 0.0,
                                 GlossaryEnergy.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgcoal',
                                 'enthalpy': 0.0,
                                 'techno_evo_eff': 'no',
                                 'enthalpy_unit': 'kWh/m^3',
                                 GlossaryEnergy.EnergyEfficiency: 1.0,
                                 'pourcentage_of_total': 0.09,
                                 'energy_burn': 'no'}

    # computing CH4 emission factor (Mt/TWh)
    '''
    Method to compute CH4 emissions from coal mines
    The proposed V0 only depends on production. The V1 could depend on mining depth (deeper and deeper along the years)
    Equation is taken from the GAINS model
    https://gem.wiki/Estimating_methane_emissions_from_coal_mines#Model_for_Calculating_Coal_Mine_Methane_.28MC2M.29,
    Nazar Kholod &al Global methane emissions from coal mining to continue growing even with declining coal production,
     Journal of Cleaner Production, Volume 256, February 2020.
    '''

    emission_factor_coeff = techno_infos_dict_default['emission_factor_coefficient']

    # compute gas content with surface and underground_gas_content in m3/t
    underground_mining_gas_content = techno_infos_dict_default['underground_mining_gas_content']
    surface_mining_gas_content = techno_infos_dict_default['surface_mining_gas_content']
    gas_content = techno_infos_dict_default['underground_mining_percentage'] / \
                  100.0 * underground_mining_gas_content + \
                  (1. - techno_infos_dict_default['underground_mining_percentage'] /
                   100.0) * surface_mining_gas_content

    # gascontent must be passed in Mt/Twh
    emission_factor_mt_twh = gas_content * emission_factor_coeff * Methane.data_energy_dict['density'] / \
                             SolidFuel.data_energy_dict['calorific_value'] * 1e-3

    techno_infos_dict_default['CH4_emission_factor'] = emission_factor_mt_twh

    techno_info_dict = techno_infos_dict_default

    energy_own_use = 952.78  # TWh
    # From ourworldindata
    initial_production = 43752. - energy_own_use
    # First invest is zero to get exactly the initial production in 2020

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(SolidFuelTechnoDiscipline.DESC_IN)

    DESC_OUT = SolidFuelTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.model = CoalExtraction(self.techno_name)
