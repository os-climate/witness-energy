'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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


from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import (
    HydrotreatedOilFuel,
)
from energy_models.core.techno_type.disciplines.hydrotreated_oil_fuel_techno_disc import (
    HydrotreatedOilFuelTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.hydrotreated_oil_fuel.hefa_deoxygenation.hefa_deoxygenation import (
    HefaDeoxygenation,
)


class HefaDeoxygenationDiscipline(HydrotreatedOilFuelTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'HEFA deoxygenation',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fa-solid fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.HefaDeoxygenation
    stream_name = HydrotreatedOilFuel.name
    # Tao, L., Milbrandt, A., Zhang, Y. and Wang, W.C., 2017.
    # Techno-economic and resource analysis of hydroprocessed renewable jet fuel.
    # Biotechnology for biofuels, 10(1), pp.1-16.
    # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0945-3/tables/2

    # conversion factors
    dollar_per_gallon_to_dollar_per_m3 = 264.17
    gallon_to_mc = 0.00378541

    techno_infos_dict_default = {

        # Pearlson, M.N., 2011. A techno-economic and environmental assessment of hydroprocessed renewable distillate fuels
        # (Doctoral dissertation, Massachusetts Institute of Technology).
        # https://dspace.mit.edu/bitstream/handle/1721.1/65508/746766700-MIT.pdf?sequence=2&isAllowed=y
        # (page 67)
        'Opex_percentage': 0.0715,
        'Invest_init': 347.5,
        'Invest_init_unit': 'M$',
        'Capex_init': 347.5 * 1e6 * dollar_per_gallon_to_dollar_per_m3 / 780
                      / (48.64 * 1e6),
        # Tao, L., Milbrandt, A., Zhang, Y. and Wang, W.C., 2017.
        # Techno-economic and resource analysis of hydroprocessed renewable jet fuel.
        # Biotechnology for biofuels, 10(1), pp.1-16.
        # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0945-3
        # Mean value computed for production volume (mean value)
        'Capex_init_unit': '$/kg',

        # Diederichs, G.W., 2015. Techno-economic assessment of processes that produce jet fuel from plant-derived sources
        # (Doctoral dissertation, Stellenbosch: Stellenbosch University).
        # https://core.ac.uk/download/pdf/37440495.pdf
        'efficiency': 0.753,
        # Pavlenko, N. and Searle, S., 2021.
        # Assessing the sustainability implications of alternative aviation fuels.
        # https://theicct.org/sites/default/files/publications/Alt-aviation-fuel-sustainability-mar2021.pdf
        # to review
        'CO2_from_production': 0.03 * 44,
        'CO2_from_production_unit': 'kg/kg',

        'maturity': 5,
        'learning_rate': 0.1,

        'full_load_hours': 7920.0,

        'WACC': 0.0878,
        'techno_evo_eff': 'no',
    }
    # Source: IEA 2022, Data and Statistics,
    # https://www.iea.org/data-and-statistics/charts/global-biofuel-production-in-2019-and-forecast-to-2025,
    # License: CC BY 4.0.
    # 9 bl of HVO/HEFA in 2020
    # https://www.ieabioenergy.com/wp-content/uploads/2021/06/IEA-Bioenergy-Task-39-Progress-in-the-commercialisation-of-biojet-fuels-May-2021-1.pdf
    # most current commercial HEFA production removes oxygen through the
    # addition of hydrogen
    initial_production = 9e6 * \
                         HydrotreatedOilFuel.data_energy_dict['density'] * \
                         HydrotreatedOilFuel.data_energy_dict['calorific_value'] * \
                         0.9 / 1e9  # TWh/year
    # Task, I.B., 2021.
    # Progress in Commercialization of Biojet/Sustainable Aviation Fuels (SAF).
    # https://www.ieabioenergy.com/wp-content/uploads/2021/06/IEA-Bioenergy-Task-39-Progress-in-the-commercialisation-of-biojet-fuels-May-2021-1.pdf
    # (page 23)
    # Existing: Neste(2014), Total(2015), Eni(2015).
    # Source
    # https://www.etipbioenergy.eu/value-chains/products-end-use/products/hvo-hefa
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
    }
    DESC_IN.update(HydrotreatedOilFuelTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HydrotreatedOilFuelTechnoDiscipline.DESC_OUT

    def init_execution(self):
        self.model = HefaDeoxygenation(self.techno_name)
