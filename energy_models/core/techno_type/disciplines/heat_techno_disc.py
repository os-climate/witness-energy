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

from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.techno_disc import TechnoDiscipline


class LowHeatTechnoDiscipline(TechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Low Heat Model',
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
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_low',
                                  'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                           'transport': ('float', None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                    'namespace': 'ns_heat_low',
                                    'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                             'margin': ('float', None, True)},
                                    'dataframe_edition_locked': False},
                             'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                'namespace': 'ns_heat_low', 'default': lowtemperatureheat.data_energy_dict},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = lowtemperatureheat.name

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        TechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions')
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)


class MediumHeatTechnoDiscipline(TechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Medium Heat Model',
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
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_medium',
                                  'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                           'transport': ('float', None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                    'namespace': 'ns_heat_medium',
                                    'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                             'margin': ('float', None, True)},
                                    'dataframe_edition_locked': False},
                              'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                 'namespace': 'ns_heat_medium', 'default': mediumtemperatureheat.data_energy_dict},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = mediumtemperatureheat.name

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        TechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions')
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)


class HighHeatTechnoDiscipline(TechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'High Heat Model',
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
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_high',
                                  'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                           'transport': ('float', None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                    'namespace': 'ns_heat_high',
                                    'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                             'margin': ('float', None, True)},
                                    'dataframe_edition_locked': False},
                              'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                 'namespace': 'ns_heat_high', 'default': hightemperatureheat.data_energy_dict},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = hightemperatureheat.name

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        TechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions')
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)
