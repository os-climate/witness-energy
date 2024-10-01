'''
Copyright 2022 Airbus SAS
Modifications on 26/03/2024 Copyright 2024 Capgemini

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
from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.glossaryenergy import GlossaryEnergy


class NaturalOil(BaseStream):
    """Natural Oil consists of oil coming from plants
    Most current ones are palm oil, rapeseed oil, soybeen oil, canola oil
    vegetable oils are triglycerides obtained from plant materials
    that are liquid at room temperature (triglycerides that are solid
    at room temperature are fats – whether derived from animal or
    plants)"""
    name = GlossaryEnergy.NaturalOilResource
    data_energy_dict = {
        'reference': 'https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth/an-introduction-to-biogas-and-biomethane ',
        'maturity': 5,

        # https://www.aceitedelasvaldesas.com/en/faq/varios/densidad-del-aceite/
        'density': 917.44,
        'density_unit': 'kg/m^3',

        # https://www.chem.wilkes.edu/~mencer/pdf_docs/Biodiesel_RF.pdf
        'molar_mass': 876.6,
        'molar_mass_unit': 'g/mol',

        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
        # 1 MJ/kg = 1000 J/g = 1 GJ/t  = 238.85 kcal/kg = 429.9
        # Btu(IT)/lb = 0.2778 kWh/kg
        'calorific_value': 10.5,
        'calorific_value_unit': 'kWh/kg',
        'high_calorific_value': 11.25,
        'high_calorific_value_unit': 'kWh/kg'
        }
