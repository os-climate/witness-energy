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
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import HighHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.models.heat.high.electric_boiler_high_heat.electric_boiler_high_heat import ElectricBoilerHighHeat
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
class ElectricBoilerHighHeatDiscipline(HighHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Electric Boiler Model',
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
    techno_name = 'ElectricBoilerHighHeat'
    energy_name = hightemperatureheat.name

    # Heat Producer [Online]
    #https://www.google.com/search?q=electric+boiler+maximum+heat+temperature+in+degree+celcius&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEdf5IN3xbJw5uB3tC7-M-5nvtg8TKg%3A1683626939090&ei=uxtaZNOCBYWeseMP6ZuEwAM&ved=0ahUKEwiTzI2N_-f-AhUFT2wGHekNATgQ4dUDCA8&uact=5&oq=electric+boiler+maximum+heat+temperature+in+degree+celcius&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCCEQoAEyBQghEKABMgUIIRCgATIFCCEQoAE6CwgAEIoFEIYDELADOggIIRAWEB4QHToHCCEQoAEQCjoECCEQFUoECEEYAVDPB1izUGDqoQVoAXAAeACAAZ0BiAGUBJIBAzAuNJgBAKABAcgBA8ABAQ&sclient=gws-wiz-serp
    #https://www.google.com/search?q=electric+boiler+lifetime&rlz=1C1UEAD_enIN1000IN1000&oq=electric+boiler+lifetime&aqs=chrome..69i57j0i22i30l4j0i390i650l4.14155j0j7&sourceid=chrome&ie=UTF-8
    lifetime = 45          # years

    construction_delay = 2  # years

    techno_infos_dict_default = {

        'Capex_init': 42.86,          # https://capgemini-my.sharepoint.com/personal/valentin_joncquieres_capgemini_com/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fvalentin%5Fjoncquieres%5Fcapgemini%5Fcom%2FDocuments%2FFichiers%20de%20conversation%20Microsoft%20Teams%2FPriyankaChintada%5Ffinal%5Fthesis%2Epdf&parent=%2Fpersonal%2Fvalentin%5Fjoncquieres%5Fcapgemini%5Fcom%2FDocuments%2FFichiers%20de%20conversation%20Microsoft%20Teams&ga=1
                                      # table 5.2.
        'Capex_init_unit': '$/kW',    # $ per kW of electricity
        'Opex_percentage': 1.6,       #https://www.google.com/search?q=+OPEX+%25+of+an+electric+boiler&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEddXq4YjX58191BnDyTZd08c2VWtJw%3A1683713517747&ei=7W1bZJqaLaicseMP_pSKkAQ&ved=0ahUKEwjaxIPRwer-AhUoTmwGHX6KAkIQ4dUDCA8&uact=5&oq=+OPEX+%25+of+an+electric+boiler&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCAAQogQyBQgAEKIEMgUIABCiBDIFCAAQogQ6BQghEKABSgQIQRgAUABYxSdggjFoAHAAeACAAZYBiAGuA5IBAzIuMpgBAKABAcABAQ&sclient=gws-wiz-serp
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 0.99,           # consumptions and productions already have efficiency included
                                      # https://www.google.com/search?q=electric+boiler+efficiency&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEddgb3MP-p7vfw3Bi3_aNLESRLQX8g%3A1685475202926&ei=gk92ZJKcOL-VseMPs4WWuA0&ved=0ahUKEwiS5f215J3_AhW_SmwGHbOCBdcQ4dUDCA8&uact=5&oq=electric+boiler+efficiency&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCAAQgAQyBQgAEIAEMgYIABAWEB4yBggAEBYQHjIGCAAQFhAeMgYIABAWEB4yBggAEBYQHjIGCAAQFhAeMgYIABAWEB4yBggAEBYQHjoKCAAQRxDWBBCwAzoECCMQJzoHCCMQ6gIQJzoVCAAQAxCPARDqAhC0AhCMAxDlAhgBOhUILhADEI8BEOoCELQCEIwDEOUCGAE6BwgAEIoFEEM6CAgAEIoFEJECOgsIABCABBCxAxCDAToNCAAQigUQsQMQgwEQQzoKCAAQigUQsQMQQzoICAAQgAQQsQM6CggAEIAEEBQQhwJKBAhBGABQ-QRYx1pgxWVoAnABeAOAAcMBiAG0K5IBBTI3LjI2mAEAoAEBsAEUwAEByAEI2gEGCAEQARgL&sclient=gws-wiz-serp
        'elec_demand': 1,             #https://billswiz.com/electric-boiler-electricity-use
        'elec_demand_unit': 'KWh',
        'learning_rate': 0.56,
        'full_load_hours': 8760.0,
        'WACC': 0.062,
        'techno_evo_eff': 'no',
    }

    # production in 2019: 1.51 EJ = 419 TWh
    # https://www.worldbioenergy.org/uploads/211214%20WBA%20GBS%202021.pdf
    # page 14
    # in TWh
    initial_production = 139.67

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
               3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0,
               2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
               1.0, 1.0, 1.0, 1.0,
               ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})

    # Renewable Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': 0})

    flux_input_dict = {'land_rate': 22000, 'land_rate_unit': '$/Gha', }
    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True),
                                                                }
                                       },
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               'flux_input_dict': {'type': 'dict', 'default': flux_input_dict, 'unit': 'defined in dict'},
               }
    DESC_IN.update(HighHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HighHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectricBoilerHighHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
