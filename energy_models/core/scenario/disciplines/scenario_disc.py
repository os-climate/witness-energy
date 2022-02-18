'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np
import pandas as pd

from energy_models.core.scenario.scenario import ScenarioModel
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline


class ScenarioDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Energy Core Scenario Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }

    year_index = np.arange(2018, 2051)

    # CO2 Taxe Data
    CPS_CO2_taxe = [15.71, 16.47, 17.22, 17.78, 18.34, 18.90, 19.46, 20.02, 20.97,
                    21.92, 22.87, 23.82, 24.77, 25.75, 26.72, 27.70, 28.68, 29.66, 30.63,
                    31.61, 32.59, 33.56, 34.54, 35.52, 36.49, 37.47, 38.45, 39.43, 40.40, 41.38, 42.36, 43.33, 44.31]

    STEPS_CO2_taxe = [14.86, 16.04, 17.22, 18.23, 19.24, 20.25, 21.26, 22.27, 23.618, 24.966, 26.314,
                      27.662, 29.01, 30.02, 31.02, 32.03, 33.04, 34.05, 35.05, 36.06, 37.07, 38.07,
                      39.08, 40.20, 41.32, 42.44, 43.56, 44.69, 45.81, 46.93, 48.05, 49.17, 50.29]

    SDS_CO2_taxe = [2.19, 9.70, 17.22, 24.74, 32.25, 39.77, 49.16, 54.80, 61.79, 68.78, 75.77, 82.76,
                    89.75, 94.04, 98.33, 102.62, 106.91, 111.20, 115.49, 119.78, 124.07, 128.36, 132.65,
                    137.89, 143.12, 148.36, 153.59, 158.83, 164.06, 169.30, 174.53, 179.77, 185.00, ]

    default_scenario_co2_taxe_all = {'CPS': pd.DataFrame(data=CPS_CO2_taxe, index=year_index, columns=['CO2_taxes']),
                                     'STEPS': pd.DataFrame(data=STEPS_CO2_taxe, index=year_index, columns=['CO2_taxes']),
                                     'SDS': pd.DataFrame(data=SDS_CO2_taxe, index=year_index, columns=['CO2_taxes'])
                                     }

    # CPS Transport
    CPS_kero_transport = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                          0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                          0.20, 0.20, 0.20, 0.20, 0.20]

    CPS_data_transport = {'kerosene': CPS_kero_transport}

    # STEPS Transport
    STEPS_kero_transport = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                            0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                            0.20, 0.20, 0.20, 0.20, 0.20]
    STEPS_h2_transport = [5.43, 5.43, 5.42, 5.42, 5.41, 5.41, 5.40, 5.40, 5.39, 5.39, 5.38, 5.38, 5.37, 5.37,
                          5.36, 5.36, 5.35, 5.35, 5.34, 5.34, 5.33, 5.33, 5.32, 4.85, 4.37, 3.90, 3.42, 2.95,
                          2.47, 2.00, 1.53, 1.05, 0.58]
    STEPS_CH4_transport = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14,
                           0.14, 0.14, 0.14, 0.14, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13,
                           0.12, 0.12, 0.12, 0.12, 0.12]
    STEPS_data_transport = {'kerosene': STEPS_kero_transport,
                            'H2': STEPS_h2_transport, 'CH4': STEPS_CH4_transport}

    # SDS transport
    SDS_kero_transport = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                          0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,
                          0.20, 0.20, 0.20, 0.20, 0.20]
    SDS_h2_transport = [2.73, 2.63, 2.53, 2.44, 2.34, 2.25, 2.15, 2.06, 1.96, 1.86, 1.77, 1.67, 1.58, 1.48,
                        1.39, 1.29, 1.19, 1.10, 1.00, 0.91, 0.81, 0.72, 0.62, 0.57, 0.52, 0.47, 0.42, 0.37,
                        0.31, 0.26, 0.21, 0.16, 0.11]
    SDS_CH4_transport = [0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14,
                         0.14, 0.14, 0.14, 0.14, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13,
                         0.12, 0.12, 0.12, 0.12, 0.12]

    SDS_data_transport = {'kerosene': SDS_kero_transport,
                          'H2': SDS_h2_transport, 'CH4': SDS_CH4_transport}

    default_transport_price_all = {'CPS': pd.DataFrame(data=CPS_data_transport, index=year_index),
                                   'STEPS': pd.DataFrame(data=STEPS_data_transport, index=year_index),
                                   'SDS': pd.DataFrame(data=SDS_data_transport, index=year_index)
                                   }

    CPS_transport_margin = [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                            1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                            1.1, 1.1, 1.1, 1.1, 1.1]
    STEP_transport_margin = [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                             1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                             1.1, 1.1, 1.1, 1.1, 1.1]
    SDS_transport_margin = [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                            1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1,
                            1.1, 1.1, 1.1, 1.1, 1.1]

    default_transport_margin_all = {'CPS': pd.DataFrame(data=CPS_transport_margin, index=year_index, columns=['transport_margin']),
                                    'STEPS': pd.DataFrame(data=STEP_transport_margin, index=year_index, columns=['transport_margin']),
                                    'SDS': pd.DataFrame(data=SDS_transport_margin, index=year_index, columns=['transport_margin'])
                                    }

    DESC_IN = {
        'yeart_start': {'type': 'int', 'default': 2020, 'unit': '[-]'},
        'yeart_end': {'type': 'int', 'default': 2100, 'unit': '[-]'},
        'scenario_name': {'type': 'string', 'default': 'CPS', 'possible_values': ['CPS', 'STEPS', 'SDS']},
        'CO2_taxes_all_scenario': {'type': 'dict', 'default': default_scenario_co2_taxe_all, 'unit': '$/ton_CO2'},
        'transport_price_all_scenario': {'type': 'dict', 'default': default_transport_price_all, 'unit': '$/kg'},
        'transport_margin_factor_all_scenario': {'type': 'dict', 'default': default_transport_margin_all, 'unit': '$/kg'}
    }

    DESC_OUT = {
        'scenario_name': {'type': 'string'},
        'CO2_taxes_scenario': {'type': 'dataframe', 'unit': '$/ton_CO2'},
        'transport_price_scenario': {'type': 'dataframe', 'unit': '$/kg'},
        'transport_margin_factor_scenario': {'type': 'dataframe', 'unit': '%'}
    }
    _maturity = 'Research'

    def run(self):
         #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        #-- instantiate specific class
        scenario = ScenarioModel(
            inputs_dict['scenario_name'], inputs_dict['CO2_taxes_all_scenario'],
            inputs_dict['transport_price_all_scenario'], inputs_dict['transport_margin_factor_all_scenario'])

        CO2_taxes_scenario = scenario.configure_co2_taxe()
        transport_price_scenario = scenario.configure_transport_price()
        transport_margin_factor_scenario = scenario.configure_transport_margin()

        ###
        # Need to adapt to the year_start / end of the study
        ###

        outputs_dict = {'scenario_name': inputs_dict['scenario_name'],
                        'CO2_taxes_scenario': CO2_taxes_scenario,
                        'transport_price_scenario': transport_price_scenario,
                        'transport_margin_factor_scenario': transport_margin_factor_scenario
                        }
        #-- store outputs
        self.store_sos_outputs_values(outputs_dict)
