'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.energy_models.kerosene import Kerosene
from energy_models.core.stream_type.energy_models.gasoline import Gasoline
from energy_models.core.stream_type.energy_models.lpg import LiquefiedPetroleumGas
from energy_models.core.stream_type.energy_models.heating_oil import HeatingOil
from energy_models.core.stream_type.energy_models.ultralowsulfurdiesel import UltraLowSulfurDiesel
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel


class LiquidFuelTechnoDiscipline(TechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Liquid Fuel Technology Model',
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
    DESC_IN = {GlossaryCore.TransportCostValue: {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_liquid_fuel',
                                  'dataframe_descriptor': {GlossaryCore.Years: ('int',  [1900, 2100], False),
                                                           'transport': ('float',  None, True)},
                                  'dataframe_edition_locked': False},
               GlossaryCore.TransportMarginValue: {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                    'namespace': 'ns_liquid_fuel',
                                    'dataframe_descriptor': {GlossaryCore.Years: ('int',  [1900, 2100], False),
                                                             GlossaryCore.MarginValue: ('float',  None, True)},
                                    'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict',
                                  'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_liquid_fuel',
                                  'default': LiquidFuel.data_energy_dict,
                                  'unit': 'defined in dict'
                                  },
               'other_fuel_dict': {'type': 'dict',
                                   'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                   'namespace': 'ns_liquid_fuel',
                                   'default': {Kerosene.name: Kerosene.data_energy_dict,
                                               Gasoline.name: Gasoline.data_energy_dict,
                                               LiquefiedPetroleumGas.name: LiquefiedPetroleumGas.data_energy_dict,
                                               HeatingOil.name: HeatingOil.data_energy_dict,
                                               UltraLowSulfurDiesel.name: UltraLowSulfurDiesel.data_energy_dict,
                                               },
                                   'unit': 'defined in dict'
                                   },
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = LiquidFuel.name
    kerosene_name = Kerosene.name
    gasoline_name = Gasoline.name
    lpg_name = LiquefiedPetroleumGas.name
    heating_oil_name = HeatingOil.name
    ulsd_name = UltraLowSulfurDiesel.name
