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
from climateeconomics.glossarycore import GlossaryCore


class ResourceGlossary():
    '''
    Just a glossary to harmonize the resources names and data
    CO2 emissions [kgCO2/kg]
    Prices [$/t]
    '''

    UNITS={'production': 'Mt', 'consumption': 'Mt', 'price': '$/t', GlossaryCore.CO2EmissionsValue: 'kgCO2/kg'}

    ResourceList = ['Uranium', 'Water', 'SeaWater', 'CO2', 'BiomassDry', 'WetBiomass', 'NaturalOil', 'Methanol',
                    'SodiumHydroxide', 'Wood', 'Carbon', 'ManagedWood', 'Oxygen', 'CrudeOil', 'SolidFuel',
                    'Calcium', 'CalciumOxyde', 'Potassium', 'PotassiumHydroxide', 'Amine', 'Dioxygen',
                    'EthanolAmine', 'MonoEthanolAmine', 'Glycerol', 'NaturalGas', 'Coal', 'Oil', 'Copper', 'Platinum']

    Uranium = {'name': 'uranium_resource',
               GlossaryCore.CO2EmissionsValue: 0.474 / 277.78,
               'price': 1390000.0, }
    Water = {'name': 'water_resource',
             GlossaryCore.CO2EmissionsValue: 0.0,
             'price': 1.78}
    SeaWater = {'name': 'sea_water_resource',
                GlossaryCore.CO2EmissionsValue: 0.0,
                'price': 1.4313}
    CO2 = {'name': 'CO2_resource',
           GlossaryCore.CO2EmissionsValue: -1.0,
           'price': 200.0}
    BiomassDry = {'name': 'biomass_dry_resource',
                  GlossaryCore.CO2EmissionsValue: - 0.425 * 44.01 / 12.0,
                  'price': 68.12}
    WetBiomass = {'name': 'wet_biomass_resource',
                  GlossaryCore.CO2EmissionsValue: - 0.9615,
                  'price': 56.0}
    # - 0.425 * 44.01 / 12.0 (old CO2_emissions value)
    # Calibration to have zero CO2 emissions in biogas.anaerobic_digestion when biogas use

    NaturalOil = {'name': 'natural_oil_resource',
                  GlossaryCore.CO2EmissionsValue: -2.95,
                  'price': 1100.0}
    Methanol = {'name': 'methanol_resource',
                GlossaryCore.CO2EmissionsValue: 0.54,
                'price': 400.0}
    SodiumHydroxide = {'name': 'sodium_hydroxide_resource',
                       GlossaryCore.CO2EmissionsValue: 0.6329,
                       'price': 425.0}
    Wood = {'name': 'wood_resource',
            GlossaryCore.CO2EmissionsValue: 1.78,
            'price': 120.0, }
    Carbon = {'name': 'carbon_resource',
              GlossaryCore.CO2EmissionsValue: 44.01 / 12.0,
              'price': 25000.0}
    ManagedWood = {'name': 'managed_wood_resource',
                   GlossaryCore.CO2EmissionsValue: 0.0,
                   'price': 37.5}
    Oxygen = {'name': 'oxygen_resource',
              GlossaryCore.CO2EmissionsValue: 0.0,
              'price':  10.0}
    Dioxygen = {'name': 'dioxygen_resource',
                GlossaryCore.CO2EmissionsValue: 0.0,
                'price':  10.0}
    CrudeOil = {'name': 'crude_oil_resource',
                GlossaryCore.CO2EmissionsValue: 0.02533,
                'price': 44.0}
    SolidFuel = {'name': 'solid_fuel_resource',
                 GlossaryCore.CO2EmissionsValue: 0.64 / 4.86,
                 'price': 250.0}
    Calcium = {'name': 'calcium_resource',
               GlossaryCore.CO2EmissionsValue: 0.0,
               'price': 85.0}
    CalciumOxyde = {'name': 'calcium_oxyde_resource',
                    GlossaryCore.CO2EmissionsValue: 0.0,
                    'price': 150.0}
    Potassium = {'name': 'potassium_resource',
                 GlossaryCore.CO2EmissionsValue: 0.0,
                 'price': 500.0}
    PotassiumHydroxide = {'name': 'potassium_hydroxide_resource',
                          GlossaryCore.CO2EmissionsValue: 0.0,
                          'price': 500.0}
    Amine = {'name': 'amine_resource',
             GlossaryCore.CO2EmissionsValue: 0.0,
             'price': 1300.0}
    EthanolAmine = {'name': 'ethanol_amine_resource',
                    GlossaryCore.CO2EmissionsValue: 0.0,
                    'price': 1700.0}
    MonoEthanolAmine = {'name': 'mono_ethanol_amine_resource',
                        GlossaryCore.CO2EmissionsValue: 0.0,
                        'price': 1700.0}
    Glycerol = {'name': 'glycerol_resource',
                GlossaryCore.CO2EmissionsValue: 0.0,
                'price': 0.0}
    NaturalGas = {'name': 'natural_gas_resource',
                  GlossaryCore.CO2EmissionsValue: 0.0,
                  'price': 0.0}
    Coal = {'name': 'coal_resource',
            GlossaryCore.CO2EmissionsValue: 0.0,
            'price': 0.0}
    Oil = {'name': 'oil_resource',
           GlossaryCore.CO2EmissionsValue: 0.02533,
           'price': 44.0}

    Copper = {'name': 'copper_resource',
              GlossaryCore.CO2EmissionsValue: 0.0,
              'price': 10057.0}
            
    Platinum = {'name': 'platinum_resource',
                GlossaryCore.CO2EmissionsValue: 0.0,
                'price': 32825887.76}

    GlossaryDict = {
        'Uranium': Uranium, 'Water': Water, 'SeaWater': SeaWater, 'CO2': CO2, 'BiomassDry': BiomassDry,
        'WetBiomass': WetBiomass, 'NaturalOil': NaturalOil, 'Methanol': Methanol,
        'SodiumHydroxide': SodiumHydroxide, 'Wood': Wood, 'Carbon': Carbon, 'ManagedWood': ManagedWood,
        'Oxygen': Oxygen, 'Dioxygen': Dioxygen, 'CrudeOil': CrudeOil, 'SolidFuel': SolidFuel,
        'Calcium': Calcium, 'CalciumOxyde': CalciumOxyde, 'Potassium': Potassium,
        'PotassiumHydroxide': PotassiumHydroxide, 'Amine': Amine, 'EthanolAmine': EthanolAmine,
        'MonoEthanolAmine': MonoEthanolAmine, 'Glycerol': Glycerol, 'NaturalGas': NaturalGas,
        'Coal': Coal, 'Oil': Oil, 'Copper' : Copper, 'Platinum': Platinum,
    }
