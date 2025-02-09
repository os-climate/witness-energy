'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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


class CarbonCapture(BaseStream):
    name = GlossaryEnergy.carbon_capture
    flue_gas_name = GlossaryEnergy.CO2FromFlueGas
    unit = 'Mt'
    default_techno_list = [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}', f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.CalciumPotassiumScrubbing}',
                           f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.ChilledAmmoniaProcess}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CO2Membranes}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.MonoEthanolAmine}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PiperazineProcess}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PressureSwingAdsorption}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.FlueGasTechno}']
    # Data dict from CO2 dioxyde
    data_energy_dict = {'maturity': 5,
                        'density': 1.98,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 44.01,
                        'molar_mass_unit': 'g/mol',
                        # Calorific values set to 1.0 for the calculation of transport cost (in $/kWh)
                        # Since it is not used as an energy source
                        'calorific_value': 1.0,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 1.0,
                        'high_calorific_value_unit': 'kWh/kg'}

