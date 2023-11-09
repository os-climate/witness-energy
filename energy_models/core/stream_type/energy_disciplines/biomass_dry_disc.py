'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/27-2023/11/07 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class BiomassDryDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Dry Biomass Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tree fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryCore.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': BiomassDry.default_techno_list,
                                     'default': BiomassDry.default_techno_list,
                                     'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                     'namespace': 'ns_biomass_dry',
                                     'structuring': True, 'unit': '-'},
               'data_fuel_dict': {'type': 'dict', 'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'unit': 'defined in dict',
                                  'namespace': 'ns_biomass_dry', 'default': BiomassDry.data_energy_dict},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    energy_name = BiomassDry.name

    DESC_OUT = EnergyDiscipline.DESC_OUT  # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = BiomassDry(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def get_chart_co2_emissions(self):
        '''
        surcharged from EnergyDiscipline to have emissions from technology production
        '''
        new_charts = []
        chart_name = f'Comparison of CO2 emissions due to production and use of {self.energy_name} technologies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryCore.Years, 'CO2 emissions (Gt)', chart_name=chart_name, stacked_bar=True)

        technology_list = self.get_sosdisc_inputs(GlossaryCore.techno_list)

        co2_per_use = self.get_sosdisc_outputs(
            'CO2_per_use')

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryCore.CO2EmissionsValue}')
            techno_production = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryCore.TechnoProductionValue}')
            year_list = techno_emissions[GlossaryCore.Years].values.tolist()
            emission_list = techno_emissions[technology].values * \
                            techno_production[f'{self.energy_name} ({BiomassDry.unit})'].values
            serie = InstanciatedSeries(
                year_list, emission_list.tolist(), technology, 'bar')
            new_chart.series.append(serie)
            # if there is a better way to know which technology is zero
            # emissions
            if technology == 'UnmanagedWood':
                co2_per_use = co2_per_use['CO2_per_use'].values * \
                              techno_production[f'{self.energy_name} ({BiomassDry.unit})'].values
        serie = InstanciatedSeries(
            year_list, co2_per_use.tolist(), 'CO2 from use of brut production', 'bar')
        new_chart.series.append(serie)
        new_charts.append(new_chart)

        return new_charts
