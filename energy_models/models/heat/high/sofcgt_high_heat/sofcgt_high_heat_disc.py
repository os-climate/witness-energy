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
import numpy as np
import pandas as pd

from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import HighHeatTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.high.sofcgt_high_heat.sofcgt_high_heat import SofcgtHighHeat
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel


class SofcgtHighHeatDiscipline(HighHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Sofcgt Model',
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
    techno_name = 'SofcgtHighHeat'
    energy_name = hightemperatureheat.name

    # Heat Producer [Online]
    #https://www.sciencedirect.com/science/article/pii/S095965262301569X
    lifetime = 30 # years

    construction_delay = 2  # years

    techno_infos_dict_default = {

        'Capex_init': 1250,
         #From <https://www.google.com/search?q=capex+of+sofc+technologies+worldwide+%24%2Fkw&sca_esv=8ab36c672be0c8ca&rlz=1C1GCEA_enIN1087IN1087&ei=5drWZaPAGd6YseMPiu-7iAM&ved=0ahUKEwjjxtzsmr6EAxVeTGwGHYr3DjEQ4dUDCBA&uact=5&oq=capex+of+sofc+technologies+worldwide+%24%2Fkw&gs_lp=Egxnd3Mtd2l6LXNlcnAiKWNhcGV4IG9mIHNvZmMgdGVjaG5vbG9naWVzIHdvcmxkd2lkZSAkL2t3MgUQIRigATIFECEYoAEyBRAhGKABMgUQIRigAUi_TFDRCViZRHABeAGQAQCYAakBoAGiBaoBAzAuNbgBA8gBAPgBAcICChAAGEcY1gQYsAPCAggQABiABBiiBIgGAZAGAw&sclient=gws-wiz-serp> 

        # table 5.2.
        'Capex_init_unit': '$/kW',  # $ per kW of electricity
        'Opex_percentage': 0.02,#https://www.diva-portal.org/smash/get/diva2:1666533/FULLTEXT01.pdf
        #https://www.researchgate.net/publication/260609024_Economic_analysis_of_a_solid_oxide_fuel_cell_cogenerationtrigeneration_system_for_hotels_in_Hong_Kong

         ##https://ec.europa.eu/research/participants/documents/downloadPublic?documentIds=080166e5b09ca4e9&appId=PPGMS
        'lifetime': lifetime,
        'lifetime_unit': GlossaryEnergy.Years,
        GlossaryEnergy.ConstructionDelay: construction_delay,
        'construction_delay_unit': GlossaryEnergy.Years,
        'efficiency': 0.6 , # consumptions and productions already have efficiency included
        #From <https://www.sciencedirect.com/science/article/pii/S0378775316310011
        
        'hydrogen_demand': 1.08 ,  # at 100% efficiency
        #https://www.sciencedirect.com/science/article/abs/pii/S0360544220302693
        'hydrogen_demand_unit': 'kg/kWh',
        'learning_rate': 0.56,
        'full_load_hours': 8760.0,
        'WACC': 0.062,
        'techno_evo_eff': 'no',
    }

    # production in 2019: 1.51 EJ = 419 TWh
    # production 120 MW Net power= 0.00012 terawatt-hours (TWh)
    # From <https://www.google.com/search?sca_esv=62aa5c07e907627d&rlz=1C1GCEA_enIN1087IN1087&q=electricity+output+from+sofcgt+plant&nfpr=1&sa=X&ved=2ahUKEwj4mrLwgKWEAxX-8DgGHbzUDtsQvgUoAXoECAUQAw&biw=1280&bih=585&dpr=1.5
     # in TWh
    initial_production = 0.00012

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
               3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 
               ]
    
    
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})
    
    # Renewable Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: 0})

    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {
                                           GlossaryEnergy.Years: ('int', [1900, 2100], False),
                                           'age': ('float', None, True),
                                           'distrib': ('float', None, True),
                                           }
                                       },
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},

               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               }
    DESC_IN.update(HighHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HighHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = SofcgtHighHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
