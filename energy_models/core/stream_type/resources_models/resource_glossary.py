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
from energy_models.glossaryenergy import GlossaryEnergy


class ResourceGlossary:
    '''
    Just a glossary to harmonize the resources names and data
    CO2 emissions [kgCO2/kg]
    Prices [$/t]
    '''

    UNITS = {'production': 'Mt',
             'consumption': 'Mt',
             'price': '$/t',
             GlossaryEnergy.CO2EmissionsValue: 'kgCO2/kg'}

    Uranium = {'name': GlossaryEnergy.UraniumResource,
               GlossaryEnergy.CO2EmissionsValue: 0.474 / 277.78,
               'price': 1390000.0, }
    Water = {'name': GlossaryEnergy.WaterResource,
             GlossaryEnergy.CO2EmissionsValue: 0.0,
             'price': 1.78}

    SeaWater = {'name': GlossaryEnergy.SeaWaterResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 1.4313}
    CO2 = {'name': GlossaryEnergy.CO2Resource,
           GlossaryEnergy.CO2EmissionsValue: -1.0,
           'price': 200.0}
    BiomassDry = {'name': GlossaryEnergy.BiomassDryResource,
                  GlossaryEnergy.CO2EmissionsValue: - 0.425 * 44.01 / 12.0,
                  'price': 68.12}
    WetBiomass = {'name': GlossaryEnergy.WetBiomassResource,
                  GlossaryEnergy.CO2EmissionsValue: - 0.9615,
                  'price': 56.0}
    # - 0.425 * 44.01 / 12.0 (old CO2_emissions value)
    # Calibration to have zero CO2 emissions in biogas.anaerobic_digestion when biogas use

    NaturalOil = {'name': GlossaryEnergy.NaturalOilResource,
                  GlossaryEnergy.CO2EmissionsValue: -2.95,
                  'price': 1100.0}
    Methanol = {'name': GlossaryEnergy.MethanolResource,
                GlossaryEnergy.CO2EmissionsValue: 0.54,
                'price': 400.0}
    SodiumHydroxide = {'name': GlossaryEnergy.SodiumHydroxideResource,
                       GlossaryEnergy.CO2EmissionsValue: 0.6329,
                       'price': 425.0}
    Wood = {'name': GlossaryEnergy.WoodResource,
            GlossaryEnergy.CO2EmissionsValue: 1.78,
            'price': 120.0, }
    Carbon = {'name': GlossaryEnergy.CarbonResource,
              GlossaryEnergy.CO2EmissionsValue: 44.01 / 12.0,
              'price': 25000.0}
    ManagedWood = {'name': GlossaryEnergy.ManagedWoodResource,
                   GlossaryEnergy.CO2EmissionsValue: 0.0,
                   'price': 37.5}
    Oxygen = {'name': GlossaryEnergy.OxygenResource,
              GlossaryEnergy.CO2EmissionsValue: 0.0,
              'price': 10.0}
    Dioxygen = {'name': GlossaryEnergy.DioxygenResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 10.0}
    CrudeOil = {'name': GlossaryEnergy.CrudeOilResource,
                GlossaryEnergy.CO2EmissionsValue: 0.02533,
                'price': 44.0}
    SolidFuel = {'name': GlossaryEnergy.SolidFuelResource,
                 GlossaryEnergy.CO2EmissionsValue: 0.64 / 4.86,
                 'price': 250.0}
    Calcium = {'name': GlossaryEnergy.CalciumResource,
               GlossaryEnergy.CO2EmissionsValue: 0.0,
               'price': 85.0}
    CalciumOxyde = {'name': GlossaryEnergy.CalciumOxydeResource,
                    GlossaryEnergy.CO2EmissionsValue: 0.0,
                    'price': 150.0}
    Potassium = {'name': GlossaryEnergy.PotassiumResource,
                 GlossaryEnergy.CO2EmissionsValue: 0.0,
                 'price': 500.0}
    PotassiumHydroxide = {'name': GlossaryEnergy.PotassiumHydroxideResource,
                          GlossaryEnergy.CO2EmissionsValue: 0.0,
                          'price': 500.0}
    Amine = {'name': GlossaryEnergy.AmineResource,
             GlossaryEnergy.CO2EmissionsValue: 0.0,
             'price': 1300.0}
    EthanolAmine = {'name': GlossaryEnergy.EthanolAmineResource,
                    GlossaryEnergy.CO2EmissionsValue: 0.0,
                    'price': 1700.0}
    MonoEthanolAmine = {'name': GlossaryEnergy.MonoEthanolAmineResource,
                        GlossaryEnergy.CO2EmissionsValue: 0.0,
                        'price': 1700.0}
    Glycerol = {'name': GlossaryEnergy.GlycerolResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 0.0}
    NaturalGas = {'name': GlossaryEnergy.NaturalGasResource,
                  GlossaryEnergy.CO2EmissionsValue: 0.0,
                  'price': 0.0}
    Coal = {'name': GlossaryEnergy.CoalResource,
            GlossaryEnergy.CO2EmissionsValue: 0.0,
            'price': 0.0}
    Oil = {'name': GlossaryEnergy.OilResource,
           GlossaryEnergy.CO2EmissionsValue: 0.02533,
           'price': 44.0}

    Copper = {'name': GlossaryEnergy.CopperResource,
              GlossaryEnergy.CO2EmissionsValue: 0.0,
              'price': 10057.0}

    Platinum = {'name': GlossaryEnergy.PlatinumResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 32825887.76}

    SolidCarbon = {'name': GlossaryEnergy.SolidCarbon,
                   GlossaryEnergy.CO2EmissionsValue: 0.0,
                   'price': 1180.} # https://www.made-in-china.com/price/solid-carbon-price.html

    GlossaryDict = {
        'Uranium': Uranium, 'Water': Water, 'SeaWater': SeaWater, GlossaryEnergy.CO2: CO2, 'BiomassDry': BiomassDry,
        'WetBiomass': WetBiomass, 'NaturalOil': NaturalOil, 'Methanol': Methanol,
        'SodiumHydroxide': SodiumHydroxide, 'Wood': Wood, 'Carbon': Carbon, 'ManagedWood': ManagedWood,
        'Oxygen': Oxygen, 'Dioxygen': Dioxygen, 'CrudeOil': CrudeOil, 'SolidFuel': SolidFuel,
        'Calcium': Calcium, 'CalciumOxyde': CalciumOxyde, 'Potassium': Potassium,
        'PotassiumHydroxide': PotassiumHydroxide, 'Amine': Amine, 'EthanolAmine': EthanolAmine,
        'MonoEthanolAmine': MonoEthanolAmine, 'Glycerol': Glycerol, 'NaturalGas': NaturalGas,
        'Coal': Coal, 'Oil': Oil, 'Copper': Copper, 'Platinum': Platinum, GlossaryEnergy.SolidCarbon: SolidCarbon
    }
