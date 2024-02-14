'''
Copyright 2022 Airbus SAS
Modifications on 2024/01/31-2024/02/01 Copyright 2024 Capgemini
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
from energy_models.glossaryenergy import GlossaryEnergy


class SolidFuel(EnergyType):
    '''mix of pellets and coal because they have near the same CO2_per_use
     and calorific_value
        major use is fired power electric generation
        coal brut production = 44000TWh
        coal used for elec and syngas around 24000TWh
        Source: IEA 2022, Iron and Steel technology roadmap,
        https://www.iea.org/reports/iron-and-steel-technology-roadmap,
        License: CC BY 4.0.
        says 627Mtoe of coal for steel
        coal_needed = 627*11.63 = 7292 TWh
        iron_use_part = 7292/20000 = 0.364
    '''
    name = GlossaryEnergy.solid_fuel
    ironsteel_use_part = 627 * 11.63 / (44000 - 24000)
    default_techno_list = ['CoalExtraction', 'Pelletizing']
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # Engineering ToolBox, (2009).
                        # Combustion of Fuels - Carbon Dioxide Emission. [online]
                        # Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        # [Accessed 17 12 2021].
                        'CO2_per_use': 2.42,
                        'CO2_per_use_unit': 'kg/kg',
                        # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR55-GAINS-N2O.pdf
                        # 0.0014 kt/PJ
                        'N2O_per_use': 0.0014e-3 / 0.277,
                        'N2O_per_use_unit': 'Mt/TWh',
                        'density': 1300.0,  # at atmospheric pressure and 298K
                        'density_unit': 'kg/m^3',
                        # Lee, Jun Sian. 2015.
                        # Calorific Value of Wood Pellets. Electronic Theses and Dissertations (ETDs) 2008+.
                        # T, University of British Columbia.
                        # doi:http://dx.doi.org/10.14288/1.0135651.
                        # Calorific Value of Wood pellets (HCV=5.46; NCV=5.39)
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values.
                        # [online] Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 17 12 2021].
                        # Calorific Value of Coal (HCV=8.39; NCV=8.06)
                        'calorific_value': 4.86,
                        # lower value for electricity use
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 6.97,
                        'high_calorific_value_unit': 'kWh/kg',
                        # percentage content of water
                        'pellets_moisture': 0.08,
                        'biomass_dry_moisture': 0.30,
                        'ironsteel_use_part': ironsteel_use_part,
                        'cement_use_part': ironsteel_use_part / 4,
                        'chemicals_use_part': ironsteel_use_part / 4}

    def compute_ghg_per_use(self, ghg_type):
        '''
        Specific computation for the CO2 per use taking into account the use of coal for cement and steel 


        1t of steel --> 1.852 t of CO2
        1.7 t of steel -->  1t of coal
        1T of cement --> 0.9 t of CO2
        1T of cement --> 0.25 t of coal

        We only take into account energy emissions and not industrial emissions in energy mix 
        --> CO2 per use for iron and steel and cement will be used in an industrial co2 emissions model 
        '''

        # Source: IEA 2022, Iron and Steel technology roadmap,
        # https://www.iea.org/reports/iron-and-steel-technology-roadmap,
        # License: CC BY 4.0.
        #         kgcoal_per_kgsteel = 1 / 1.7
        #         kgcoal_per_kgcement = 0.25
        #
        #         kgco2_per_kgsteel = 1.852
        #         kgco2_per_kgcement = 0.9
        #
        #         co2_per_use_steel = kgco2_per_kgsteel / kgcoal_per_kgsteel
        #         co2_per_use_cement = kgco2_per_kgcement / kgcoal_per_kgcement
        if ghg_type == 'CO2':
            co2_per_use_kgkg = self.data_energy_dict_input['CO2_per_use'] * \
                               (1.0 - self.data_energy_dict_input['ironsteel_use_part'] -
                                self.data_energy_dict_input['cement_use_part'] - self.data_energy_dict_input[
                                    'chemicals_use_part'])

            ghg_per_use = co2_per_use_kgkg / \
                          self.data_energy_dict_input['high_calorific_value']

        else:
            ghg_per_use = EnergyType.compute_ghg_per_use(self, ghg_type)

        return ghg_per_use
