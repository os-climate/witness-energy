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

    UNITS = {'production': 'Mt', 'consumption': 'Mt', 'price': '$/t', GlossaryEnergy.CO2EmissionsValue: 'kgCO2/kg'}


    UraniumResource = 'uranium_resource'
    Uranium = {'name': UraniumResource,
               GlossaryEnergy.CO2EmissionsValue: 0.474 / 277.78,
               'price': 1390000.0, }
    WaterResource = 'water_resource'
    Water = {'name': WaterResource,
             GlossaryEnergy.CO2EmissionsValue: 0.0,
             'price': 1.78}

    SeaWaterResource = 'sea_water_resource'
    SeaWater = {'name': SeaWaterResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 1.4313}
    CO2Resource = 'CO2_resource'
    CO2 = {'name': CO2Resource,
           GlossaryEnergy.CO2EmissionsValue: -1.0,
           'price': 200.0}
    BiomassDryResource = 'biomass_dry_resource'
    BiomassDry = {'name': BiomassDryResource,
                  GlossaryEnergy.CO2EmissionsValue: - 0.425 * 44.01 / 12.0,
                  'price': 68.12}
    WetBiomassResource = 'wet_biomass_resource'
    WetBiomass = {'name': WetBiomassResource,
                  GlossaryEnergy.CO2EmissionsValue: - 0.9615,
                  'price': 56.0}
    # - 0.425 * 44.01 / 12.0 (old CO2_emissions value)
    # Calibration to have zero CO2 emissions in biogas.anaerobic_digestion when biogas use

    NaturalOilResource = 'natural_oil_resource'
    NaturalOil = {'name': NaturalOilResource,
                  GlossaryEnergy.CO2EmissionsValue: -2.95,
                  'price': 1100.0}
    MethanolResource = 'methanol_resource'
    Methanol = {'name': MethanolResource,
                GlossaryEnergy.CO2EmissionsValue: 0.54,
                'price': 400.0}
    SodiumHydroxideResource = 'sodium_hydroxide_resource'
    SodiumHydroxide = {'name': SodiumHydroxideResource,
                       GlossaryEnergy.CO2EmissionsValue: 0.6329,
                       'price': 425.0}
    WoodResource = 'wood_resource'
    Wood = {'name': WoodResource,
            GlossaryEnergy.CO2EmissionsValue: 1.78,
            'price': 120.0, }
    CarbonResource = 'carbon_resource'
    Carbon = {'name': CarbonResource,
              GlossaryEnergy.CO2EmissionsValue: 44.01 / 12.0,
              'price': 25000.0}
    ManagedWoodResource = 'managed_wood_resource'
    ManagedWood = {'name': ManagedWoodResource,
                   GlossaryEnergy.CO2EmissionsValue: 0.0,
                   'price': 37.5}
    OxygenResource = 'oxygen_resource'
    Oxygen = {'name': OxygenResource,
              GlossaryEnergy.CO2EmissionsValue: 0.0,
              'price': 10.0}
    DioxygenResource = 'dioxygen_resource'
    Dioxygen = {'name': DioxygenResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 10.0}
    CrudeOilResource = 'crude_oil_resource'
    CrudeOil = {'name': CrudeOilResource,
                GlossaryEnergy.CO2EmissionsValue: 0.02533,
                'price': 44.0}
    SolidFuelResource = 'solid_fuel_resource'
    SolidFuel = {'name': SolidFuelResource,
                 GlossaryEnergy.CO2EmissionsValue: 0.64 / 4.86,
                 'price': 250.0}
    CalciumResource = 'calcium_resource'
    Calcium = {'name': CalciumResource,
               GlossaryEnergy.CO2EmissionsValue: 0.0,
               'price': 85.0}
    CalciumOxydeResource = 'calcium_oxyde_resource'
    CalciumOxyde = {'name': CalciumOxydeResource,
                    GlossaryEnergy.CO2EmissionsValue: 0.0,
                    'price': 150.0}
    PotassiumResource = 'potassium_resource'
    Potassium = {'name': PotassiumResource,
                 GlossaryEnergy.CO2EmissionsValue: 0.0,
                 'price': 500.0}
    PotassiumHydroxideResource = 'potassium_hydroxide_resource'
    PotassiumHydroxide = {'name': PotassiumHydroxideResource,
                          GlossaryEnergy.CO2EmissionsValue: 0.0,
                          'price': 500.0}
    AmineResource = 'amine_resource'
    Amine = {'name': AmineResource,
             GlossaryEnergy.CO2EmissionsValue: 0.0,
             'price': 1300.0}
    EthanolAmineResource = 'ethanol_amine_resource'
    EthanolAmine = {'name': EthanolAmineResource,
                    GlossaryEnergy.CO2EmissionsValue: 0.0,
                    'price': 1700.0}
    MonoEthanolAmineResource = 'mono_ethanol_amine_resource'
    MonoEthanolAmine = {'name': MonoEthanolAmineResource,
                        GlossaryEnergy.CO2EmissionsValue: 0.0,
                        'price': 1700.0}
    GlycerolResource = 'glycerol_resource'
    Glycerol = {'name': GlycerolResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 0.0}
    NaturalGasResource = 'natural_gas_resource'
    NaturalGas = {'name': NaturalGasResource,
                  GlossaryEnergy.CO2EmissionsValue: 0.0,
                  'price': 0.0}
    CoalResource = 'coal_resource'
    Coal = {'name': CoalResource,
            GlossaryEnergy.CO2EmissionsValue: 0.0,
            'price': 0.0}
    OilResource = 'oil_resource'
    Oil = {'name': OilResource,
           GlossaryEnergy.CO2EmissionsValue: 0.02533,
           'price': 44.0}

    CopperResource = 'copper_resource'
    Copper = {'name': CopperResource,
              GlossaryEnergy.CO2EmissionsValue: 0.0,
              'price': 10057.0}

    PlatinumResource = 'platinum_resource'
    Platinum = {'name': PlatinumResource,
                GlossaryEnergy.CO2EmissionsValue: 0.0,
                'price': 32825887.76}

    GlossaryDict = {
        'Uranium': Uranium, 'Water': Water, 'SeaWater': SeaWater, 'CO2': CO2, 'BiomassDry': BiomassDry,
        'WetBiomass': WetBiomass, 'NaturalOil': NaturalOil, 'Methanol': Methanol,
        'SodiumHydroxide': SodiumHydroxide, 'Wood': Wood, 'Carbon': Carbon, 'ManagedWood': ManagedWood,
        'Oxygen': Oxygen, 'Dioxygen': Dioxygen, 'CrudeOil': CrudeOil, 'SolidFuel': SolidFuel,
        'Calcium': Calcium, 'CalciumOxyde': CalciumOxyde, 'Potassium': Potassium,
        'PotassiumHydroxide': PotassiumHydroxide, 'Amine': Amine, 'EthanolAmine': EthanolAmine,
        'MonoEthanolAmine': MonoEthanolAmine, 'Glycerol': Glycerol, 'NaturalGas': NaturalGas,
        'Coal': Coal, 'Oil': Oil, 'Copper': Copper, 'Platinum': Platinum,
    }

    TechnoResourceUsedDict = {
        "Transesterification": [MethanolResource, NaturalOilResource, SodiumHydroxideResource, WaterResource],
        "AnaerobicDigestion": [WetBiomassResource],
        f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing': [AmineResource],
        f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing': [CalciumResource, PotassiumResource],
        "CoalGen": [WaterResource],
        "Nuclear": [UraniumResource, WaterResource],
        "OilGen": [WaterResource],
        "BiomassFermentation": [WaterResource],
        GlossaryEnergy.ElectrolysisAWE: [WaterResource],
        GlossaryEnergy.ElectrolysisPEM: [WaterResource, PlatinumResource],
        GlossaryEnergy.ElectrolysisSOEC: [WaterResource],
        "Refinery": [OilResource],
        "FossilGas": [NaturalGasResource],
        "Methanation": [CO2Resource],
        "CO2Hydrogenation": [WaterResource],
        "CoalExtraction": [CoalResource],
        GlossaryEnergy.AutothermalReforming: [CO2Resource, OxygenResource],
        "CoElectrolysis" : [CO2Resource, WaterResource],
        "Pyrolysis": [WoodResource],
        GlossaryEnergy.WaterGasShift: [WaterResource],
        GlossaryEnergy.ReversedWaterGasShift: [CO2Resource],
        "SMR": [WaterResource],
        GlossaryEnergy.HefaDecarboxylation: [NaturalOilResource]
    }
