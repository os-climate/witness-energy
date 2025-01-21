'''
Copyright 2023 Capgemini

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


from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import (
    MediumHeatTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.medium.geothermal_medium_heat.geothermal_medium_heat import (
    GeothermalHeat,
)


class GeothermalMediumHeatDiscipline(MediumHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Geothermal Medium Heat Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.GeothermalMediumHeat
    energy_name = mediumtemperatureheat.name



    techno_infos_dict_default = {
        'Capex_init': 3830,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'Capex_init_unit': '$/kW',
        'Opex_percentage': 0.0287,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'efficiency': 1,  # consumptions and productions already have efficiency included
        'CO2_from_production': 0.122,
        # high GHG concentrations in the reservoir fluid # https://documents1.worldbank.org/curated/en/875761592973336676/pdf/Greenhouse-Gas-Emissions-from-Geothermal-Power-Production.pdf
        'CO2_from_production_unit': 'kg/kWh',
        'maturity': 5,
        'learning_rate': 0.00,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
        'output_temperature': 250,
        # Average Medium Temperature, Page Number 152, #https://www.medeas.eu/system/files/documentation/files/D8.11%28D35%29%20Model%20Users%20Manual.pdf
        'mean_temperature': 200,
        'output_temperature_unit': 'K',
        'mean_temperature_unit': 'K',
        'steel_needs': 968,
        # Page:21 #https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power
    }

    # geothermal_high_heat Heat production
    # production in 2019 #https://en.wikipedia.org/wiki/Geothermal_power
    # in TWh
    initial_production = 182500 / 3  # Equally split for High, low and Medium Heat production, #https://www.iea.org/data-and-statistics/charts/direct-use-of-geothermal-energy-world-2012-2024

    flux_input_dict = {'land_rate': 15000, 'land_rate_unit': '$/Gha', }
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      
               'flux_input_dict': {'type': 'dict', 'default': flux_input_dict, 'unit': 'defined in dict'},
               }
    DESC_IN.update(MediumHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MediumHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        self.model = GeothermalHeat(self.techno_name)
