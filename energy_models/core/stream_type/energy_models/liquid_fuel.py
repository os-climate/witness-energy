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
from energy_models.core.stream_type.energy_type import EnergyType


class LiquidFuel(EnergyType):
    name = 'liquid_fuel'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # ICAO, Carbon Calculator, 2017, CO2 per kg combustion = 3.16
                        # https://www.icao.int/environmental-protection/CarbonOffset/Documents/Methodology%20ICAO%20Carbon%20Calculator_v10-2017.pdf
                        # Alternative source:ADEME, CO2 per kg combustion in Europe = 3.15
                        # https://www.bilans-ges.ademe.fr/documentation/UPLOAD_DOC_EN/index.htm?new_liquides.htm
                        'CO2_per_use': 3.15,
                        'CO2_per_use_unit': 'kg/kg',
                        'NOx_per_energy': 0.1,
                        'NOX_per_energy_unit': 'yy',
                        # ref : U.S. Energy Information Administration EIA
                        # https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMA_EPPK_PWG_NUS_DPG&f=M
                        # price = 2.1 $.gallon-1 * (1/3.09) gallon.kg-1
                        'cost_now': 0.76,
                        'cost_now_unit': '$/kg',
                        'density': 821.0,  # at atmospheric pressure and 298K
                        'density_unit': 'kg/m^3',
                        'molar_mass': 170.0,
                        'molar_mass_unit': 'g/mol',
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 16/12/2021].
                        'calorific_value': 11.9,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 12.83,
                        'high_calorific_value_unit': 'kWh/kg',
                        # McDonald, A. and Schrattenholzer, L., 2001.
                        # Learning rates for energy technologies. Energy
                        # policy, 29(4), pp.255-261.
                        'learning_rate': 0.25,
                        'produced_energy': 4477.212,
                        # or energy industry own use (sum of crude oil
                        # extraction and refinery)
                        'direct_energy': 210.457,
                        'total_final_consumption': 3970.182,  # for oil products
                        # deduced from Brockway2019 results...
                        # Brockway, P.E., Owen, A., Brand-Correa, L.I. and Hardt, L., 2019.
                        # Estimation of global final-stage energy-return-on-investment for fossil fuels
                        # with comparison to renewable energy sources.
                        # Nature Energy, 4(7), pp.612-621.
                        'indirect_energy_percentage': 0.22,
                        'CH4_per_energy': 0,
                        'CH4_per_energy_unit': 'kg/kg',

                        # around 14% of oil is used for petrochemical plants
                        # around 8% of oil is used for construction (asphalt)
                        # or other use
                        'petrochemical_use_part': 0.14,
                        'construction_use_part': 0.08}

    def compute_co2_per_use(self, data_energy_dict):
        '''
        Specific computation for the CO2 per use taking into account the use of oil in petrochemical plants (plastic and textile) and construction


        We only take into account energy emissions and not industrial emissions in energy mix 
        --> CO2 per use petrochemical and construction will be used in an industrial co2 emissions model 
        '''


#         kgcoal_per_kgsteel = 1 / 1.7
#         kgcoal_per_kgcement = 0.25
#
#         kgco2_per_kgsteel = 1.852
#         kgco2_per_kgcement = 0.9
#
#         co2_per_use_steel = kgco2_per_kgsteel / kgcoal_per_kgsteel
#         co2_per_use_cement = kgco2_per_kgcement / kgcoal_per_kgcement

        co2_per_use_kgkg = data_energy_dict['CO2_per_use'] * \
            (1.0 - data_energy_dict['petrochemical_use_part'] -
             data_energy_dict['construction_use_part'])

        self.co2_per_use['CO2_per_use'] = co2_per_use_kgkg / \
            data_energy_dict['high_calorific_value']

        return self.co2_per_use
