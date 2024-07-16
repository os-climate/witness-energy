'''
Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore as GlossaryWitnessCore


class GlossaryEnergy(GlossaryWitnessCore):
    """Glossary for witness energy, inheriting from glossary of Witness Core"""

    CCSListName = "ccs_list"
    EnergyListName = "energy_list"
    NS_ENERGY = "ns_energy"

    CO2Taxes = GlossaryWitnessCore.CO2Taxes
    CO2Taxes["namespace"] = "ns_energy_study"

    NB_POLES_FULL: int = 8  # number of poles in witness full
    NB_POLE_ENERGY_MIX_PROCESS = 12
    EXPORT_PROFILES_AT_POLES = "export_invest_profiles_at_poles"
    YearEndDefaultValueGradientTest = 2030
    LifetimeDefaultValueGradientTest = 7
    YearEndDefault = 2050
    YearEndDefaultCore = GlossaryWitnessCore.YearEndDefault
    YearEndVar = {
        "type": "int",
        "default": YearEndDefault,
        "unit": "year",
        "visibility": "Shared",
        "namespace": "ns_public",
        "range": [2000, 2300],
    }

    methanol = "methanol"
    biogas = "biogas"
    biodiesel = "biodiesel"
    biomass_dry = "biomass_dry"
    ethanol = "ethanol"
    electricity = "electricity"
    fossil = "fossil"
    fuel = "fuel"
    gasoline = "gasoline"
    heating_oil = "heating_oil"
    hydrogen = "hydrogen"
    kerosene = "kerosene"
    liquid_fuel = "liquid_fuel"
    liquid_hydrogen = "liquid_hydrogen"
    gaseous_hydrogen = "gaseous_hydrogen"
    liquefied_petroleum_gas = "liquefied_petroleum_gas"
    hydrotreated_oil_fuel = "hydrotreated_oil_fuel"
    methane = "methane"
    renewable = "renewable"
    solid_fuel = "solid_fuel"
    syngas = "syngas"
    ultra_low_sulfur_diesel = "ultra_low_sulfur_diesel"
    wet_biomass = "wet_biomass"
    carbon_capture = "carbon_capture"
    carbon_storage = "carbon_storage"
    direct_air_capture = "direct_air_capture"
    flue_gas_capture = "flue_gas_capture"
    heat = "heat"
    lowtemperatureheat = "lowtemperatureheat"
    mediumtemperatureheat = "mediumtemperatureheat"
    hightemperatureheat = "hightemperatureheat"
    lowtemperatureheat_energyname = f"{heat}.{lowtemperatureheat}"
    mediumtemperatureheat_energyname = f"{heat}.{mediumtemperatureheat}"
    hightemperatureheat_energyname = f"{heat}.{hightemperatureheat}"
    AllEnergies = [
        biogas,
        biodiesel,
        biomass_dry,
        ethanol,
        electricity,
        fossil,
        fuel,
        gasoline,
        heating_oil,
        hydrogen,
        kerosene,
        liquid_fuel,
        liquid_hydrogen,
        gaseous_hydrogen,
        liquefied_petroleum_gas,
        hydrotreated_oil_fuel,
        methane,
        renewable,
        solid_fuel,
        syngas,
        ultra_low_sulfur_diesel,
        wet_biomass,
        carbon_capture,
        carbon_storage,
        direct_air_capture,
        flue_gas_capture,
        heat,
        lowtemperatureheat,
        mediumtemperatureheat,
        hightemperatureheat,
    ]
    syngas_ratio = "syngas_ratio"
    data_fuel_dict = "data_fuel_dict"
    technologies_list = "technologies_list"
    loss_percentage = "loss_percentage"

    LifetimeName = "lifetime"
    Transesterification = "Transesterification"
    AnaerobicDigestion = "AnaerobicDigestion"

    AllStreamsDemandRatioValue = "all_streams_demand_ratio"
    FlueGasMean = "flue_gas_mean"
    MarginValue = "margin"
    CO2EmissionsValue = "CO2_emissions"
    TechnoProductionValue = "techno_production"
    TechnoPricesValue = "techno_prices"
    TechnoDetailedConsumptionValue = "techno_detailed_consumption"
    TechnoDetailedProductionValue = "techno_detailed_production"
    TechnoDetailedPricesValue = "techno_detailed_prices"
    TechnoConsumptionValue = "techno_consumption"
    TechnoProductionWithoutRatioValue = "techno_production_woratio"
    RessourcesCO2EmissionsValue = "resources_CO2_emissions"
    TransportCostValue = "transport_cost"
    TransportMarginValue = "transport_margin"
    TransportDemandValue = "transport_demand"
    ForestInvestmentValue = "forest_investment"
    CarbonCapturedValue = "carbon_captured_type"
    InstalledPower = (
        "power_production"  # todo : rename string to Installed Power [MW] (check unit)
    )

    InstalledPowerDf = {
        "type": "dataframe",
        "unit": "MW",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            "new_power_production": ("float", None, True),
            "total_installed_power": ("float", None, True),
            "removed_power_production": ("float", None, True),
        },
    }

    MeanAgeProductionDf = {
        "type": "dataframe",
        "unit": "years",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            "mean age": ("float", None, True),
        },
    }

    # energy techno discipline names
    CarbonCaptureAndStorageTechno = "CarbonCaptureAndStorageTechno"
    DirectAirCapture = "direct_air_capture.DirectAirCaptureTechno"
    FlueGasCapture = f"{flue_gas_capture}.FlueGasTechno"

    AllStreamsDemandRatio = {
        "type": "dataframe",
        "unit": "-",
        "visibility": "Shared",
        "namespace": "ns_energy",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, YearEndDefaultCore], False),
        },
    }

    ResourcesUsedForProductionValue = "Resources used for production"
    ResourcesUsedForProduction = {
        "var_name": ResourcesUsedForProductionValue,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
    }

    ResourcesUsedForBuildingValue = "Resources used for building plants"
    ResourcesUsedForBuilding = {
        "var_name": ResourcesUsedForBuildingValue,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
    }

    StreamsUsedForProductionValue = "Streams used for production"
    StreamsUsedForProduction = {
        "var_name": StreamsUsedForProductionValue,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
    }

    CostOfResourceUsageValue = "cost_of_resources_usage"
    CostOfResourceUsageDf = {
        "var_name": CostOfResourceUsageValue,
        "type": "dataframe",
        "unit": "?",
        "description": "Cost of usage for each resource",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
        },
    }
    GhGPerUse = "{}_per_use"
    N2OPerUse = "N2O_per_use"
    CH4PerUse = "CH4_per_use"
    CO2PerUse = "CO2_per_use"
    CO2PerUseDf = {
        "varname": CO2PerUse,
        "type": "dataframe",
        "unit": "kg/kWh",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            CO2PerUse: ("float", None, True),
        },
    }
    CH4PerUseDf = {
        "varname": CH4PerUse,
        "type": "dataframe",
        "unit": "kg/kWh",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            CH4PerUse: ("float", None, True),
        },
    }
    N2OPerUseDf = {
        "varname": N2OPerUse,
        "type": "dataframe",
        "unit": "kg/kWh",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            N2OPerUse: ("float", None, True),
        },
    }

    CostOfStreamsUsageValue = "cost_of_streams_usage"
    CostOfStreamsUsageDf = {
        "var_name": CostOfStreamsUsageValue,
        "type": "dataframe",
        "unit": "?",
        "description": "Cost of usage for each stream (energy or ccs)",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
        },
    }

    SpecificCostsForProductionValue = "Specific costs for production"
    SpecificCostsForProduction = {
        "var_name": SpecificCostsForProductionValue,
        "type": "dataframe",
        "description": "Costs that are specific to the techno",
        "dynamic_dataframe_columns": True,
    }

    CCSTechnoInvest = {
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "namespace": "ns_ccs",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            "invest": ("float", [0.0, 1e30], True),
        },
    }

    EnergyTechnoInvest = {
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "namespace": "ns_energy",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            "invest": ("float", [0.0, 1e30], True),
        },
    }
    TechnoCapitalDf = {
        "var_name": GlossaryWitnessCore.TechnoCapitalValue,
        "type": "dataframe",
        "unit": "G$",
        "description": "Capital in G$ of the technology",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            GlossaryWitnessCore.Capital: ("float", [0.0, 1e30], False),
        },
    }

    MarginDf = {
        "type": "dataframe",
        "unit": "%",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, True),
            MarginValue: ("float", None, True),
        },
    }
    TechnoInvestDf = {
        "type": "dataframe",
        "unit": "G$",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, YearEndDefaultCore], False),
            GlossaryWitnessCore.InvestValue: ("float", None, True),
        },
        "dataframe_edition_locked": False,
    }

    UtilisationRatioDf = {
        "var_name": GlossaryWitnessCore.UtilisationRatioValue,
        "type": "dataframe",
        "namespace": "ns_witness",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            GlossaryWitnessCore.UtilisationRatioValue: ("float", [0, 100], False),
        },
    }

    EnergyTypeCapitalDfValue = "energy_type_capital"
    EnergyTypeCapitalDf = {
        "var_name": EnergyTypeCapitalDfValue,
        "type": "dataframe",
        "unit": "G$",
        # namespace: ns_energy,
        # visibility: Shared,
        "description": "Capital in G$ of the energy type",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            GlossaryWitnessCore.Capital: ("float", [0.0, 1e30], False),
        },
    }

    TechnoInvestPercentageName = "techno_invest_percentage"
    TechnoInvestPercentage = {
        "var_name": TechnoInvestPercentageName,
        "type": "dataframe",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
        },
        "unit": "%",
        "description": "Percentage of investments in each energy technology based on total energy investments",
    }

    EnergyInvestPercentageGDPName = "percentage_of_gdp_energy_invest"
    EnergyInvestPercentageGDP = {
        "var_name": EnergyInvestPercentageGDPName,
        "type": "dataframe",
        "unit": "%",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "int",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            EnergyInvestPercentageGDPName: ("float", [0, 100], True),
        },
        "description": "percentage of total energy investment in each of the energy technologies",
    }

    ManagedWoodInvestmentName = "managed_wood_investment"
    ManagedWoodInvestment = {
        "var_name": ManagedWoodInvestmentName,
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "float",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            GlossaryWitnessCore.InvestmentsValue: ("float", [0.0, 1e30], False),
        },
        "namespace": "ns_forest",
        "dataframe_edition_locked": False,
    }

    DeforestationInvestmentName = "deforestation_investment"
    DeforestationInvestment = {
        "var_name": DeforestationInvestmentName,
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("float", None, False),
            GlossaryWitnessCore.InvestmentsValue: ("float", [0.0, 1e30], False),
        },
        "namespace": "ns_forest",
        "dataframe_edition_locked": False,
    }

    CropInvestmentName = "crop_investment"
    CropInvestment = {
        "var_name": CropInvestmentName,
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "float",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            GlossaryWitnessCore.InvestmentsValue: ("float", [0.0, 1e30], False),
        },
        "namespace": "ns_crop",
        "dataframe_edition_locked": False,
    }

    TechnoListName = "technologies_list"
    TechnoList = {
        "var_name": TechnoListName,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
        "structuring": True,
        "visibility": "Shared",
    }

    InvestLevel = {"type": "dataframe", "unit": "G$", "visibility": "Shared"}

    EnergyList = {
        "var_name": EnergyListName,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
        "visibility": "Shared",
        "namespace": "ns_energy_study",
        "editable": False,
        "structuring": True,
    }

    CCSList = {
        "var_name": CCSListName,
        "type": "list",
        "subtype_descriptor": {"list": "string"},
        "visibility": "Shared",
        "namespace": "ns_energy_study",
        "editable": False,
        "structuring": True,
    }

    ForestInvestment = {
        "var_name": ForestInvestmentValue,
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "float",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            ForestInvestmentValue: ("float", [0.0, 1e30], False),
        },
        "namespace": "ns_invest",
        "dataframe_edition_locked": False,
    }

    CarbonCaptured = {
        "var_name": CarbonCapturedValue,
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: (
                "float",
                [1900, GlossaryWitnessCore.YearEndDefault],
                False,
            ),
            CarbonCapturedValue: ("float", [0.0, 1e30], False),
        },
        "namespace": "ns_invest",
        "dataframe_edition_locked": False,
    }

    TechnoProductionDf = {
        "var_name": TechnoProductionValue,
        "type": "dataframe",
        "unit": "TWh or Mt",
        "dynamic_dataframe_columns": True,
    }

    EnergyPricesDf = {
        "var_name": GlossaryWitnessCore.StreamPricesValue,
        "type": "dataframe",
        "unit": "$/MWh",
        "dynamic_dataframe_columns": True,
    }

    # techno names
    NaturalGas = "NaturalGas"
    CropEnergy = "CropEnergy"
    ManagedWood = "ManagedWood"
    UnmanagedWood = "UnmanagedWood"
    OrganicWaste = "OrganicWaste"
    BiomassBuryingFossilization = "BiomassBuryingFossilization"
    CarbonStorageTechno = "CarbonStorageTechno"
    DeepOceanInjection = "DeepOceanInjection"
    DeepSalineFormation = "DeepSalineFormation"
    DepletedOilGas = "DepletedOilGas"
    EnhancedOilRecovery = "EnhancedOilRecovery"
    GeologicMineralization = "GeologicMineralization"
    PureCarbonSolidStorage = "PureCarbonSolidStorage"
    Reforestation = "Reforestation"
    BiomassFired = "BiomassFired"
    CoalGen = "CoalGen"
    BiogasFired = "BiogasFired"
    CombinedCycleGasTurbine = "CombinedCycleGasTurbine"
    GasTurbine = "GasTurbine"
    Geothermal = "Geothermal"
    Hydropower = "Hydropower"
    Nuclear = "Nuclear"
    OilGen = "OilGen"
    RenewableElectricitySimpleTechno = "RenewableElectricitySimpleTechno"
    SolarPv = "SolarPv"
    SolarThermal = "SolarThermal"
    Solar = "Solar"
    WindOffshore = "WindOffshore"
    WindOnshore = "WindOnshore"
    WindOnshoreAndOffshore = "WindOnShoreandOffShore"
    BiomassFermentation = "BiomassFermentation"
    FossilSimpleTechno = "FossilSimpleTechno"
    ElectrolysisAWE = "Electrolysis.AWE"
    ElectrolysisPEM = "Electrolysis.PEM"
    ElectrolysisSOEC = "Electrolysis.SOEC"
    PlasmaCracking = "PlasmaCracking"
    Electrolysis = "Electrolysis"
    WaterGasShift = "WaterGasShift"
    CHPHighHeat = "CHPHighHeat"
    ElectricBoilerHighHeat = "ElectricBoilerHighHeat"
    GeothermalHighHeat = "GeothermalHighHeat"
    HeatPumpHighHeat = "HeatPumpHighHeat"
    NaturalGasBoilerHighHeat = "NaturalGasBoilerHighHeat"
    CHPLowHeat = "CHPLowHeat"
    ElectricBoilerLowHeat = "ElectricBoilerLowHeat"
    GeothermalLowHeat = "GeothermalLowHeat"
    HeatPumpLowHeat = "HeatPumpLowHeat"
    NaturalGasBoilerLowHeat = "NaturalGasBoilerLowHeat"
    CHPMediumHeat = "CHPMediumHeat"
    ElectricBoilerMediumHeat = "ElectricBoilerMediumHeat"
    GeothermalMediumHeat = "GeothermalMediumHeat"
    HeatPumpMediumHeat = "HeatPumpMediumHeat"
    NaturalGasBoilerMediumHeat = "NaturalGasBoilerMediumHeat"
    HefaDecarboxylation = "HefaDecarboxylation"
    HefaDeoxygenation = "HefaDeoxygenation"
    FischerTropsch = "FischerTropsch"
    Refinery = "Refinery"
    HydrogenLiquefaction = "HydrogenLiquefaction"
    FossilGas = "FossilGas"
    Methanation = "Methanation"
    UpgradingBiogas = "UpgradingBiogas"
    CO2Hydrogenation = "CO2Hydrogenation"
    RenewableSimpleTechno = "RenewableSimpleTechno"
    CoalExtraction = "CoalExtraction"
    Pelletizing = "Pelletizing"
    AutothermalReforming = "AutothermalReforming"
    BiomassGasification = "BiomassGasification"
    CoElectrolysis = "CoElectrolysis"
    CoalGasification = "CoalGasification"
    Pyrolysis = "Pyrolysis"
    ReversedWaterGasShift = "RWGS"
    Crop = "Crop"
    Forest = "Forest"
    SMR = "SMR"
    AnimalManure = "AnimalManure"
    WetCropResidues = "WetCropResidues"
    ForestProduction = "ForestProduction"

    AmineScrubbing = "AmineScrubbing"
    CalciumPotassiumScrubbing = "CalciumPotassiumScrubbing"
    CalciumLooping = "CalciumLooping"
    ChilledAmmoniaProcess = "ChilledAmmoniaProcess"
    CO2Membranes = "CO2Membranes"
    MonoEthanolAmine = "MonoEthanolAmine"
    PiperazineProcess = "PiperazineProcess"
    PressureSwingAdsorption = "PressureSwingAdsorption"

    FlueGasTechno = "FlueGasTechno"
    DirectAirCaptureTechno = "DirectAirCaptureTechno"

    # Techno Dicts :
    stream_type = "type"
    energy_type = "energy"
    agriculture_type = "agriculture"
    ccus_type = "CCUS"
    value = "value"
    DEFAULT_TECHNO_DICT_DEV = {
        methane: {
            stream_type: energy_type,
            value: [FossilGas, UpgradingBiogas, Methanation],
        },
        f"{hydrogen}.{gaseous_hydrogen}": {
            stream_type: energy_type,
            value: [
                WaterGasShift,
                ElectrolysisSOEC,
                ElectrolysisPEM,
                ElectrolysisAWE,
                PlasmaCracking,
            ],
        },
        biogas: {stream_type: energy_type, value: [AnaerobicDigestion]},
        syngas: {stream_type: energy_type, value: [BiomassGasification]},
        f"{fuel}.{liquid_fuel}": {
            stream_type: energy_type,
            value: [Refinery, FischerTropsch],
        },
        hightemperatureheat_energyname: {
            stream_type: energy_type,
            value: [
                NaturalGasBoilerHighHeat,
                ElectricBoilerHighHeat,
                HeatPumpHighHeat,
                GeothermalHighHeat,
                CHPHighHeat,
            ],
        },
        mediumtemperatureheat_energyname: {
            stream_type: energy_type,
            value: [
                NaturalGasBoilerMediumHeat,
                ElectricBoilerMediumHeat,
                HeatPumpMediumHeat,
                GeothermalMediumHeat,
                CHPMediumHeat,
            ],
        },
        lowtemperatureheat_energyname: {
            stream_type: energy_type,
            value: [
                NaturalGasBoilerLowHeat,
                ElectricBoilerLowHeat,
                HeatPumpLowHeat,
                GeothermalLowHeat,
                CHPLowHeat,
            ],
        },
        f"{fuel}.{hydrotreated_oil_fuel}": {
            stream_type: energy_type,
            value: [HefaDecarboxylation, HefaDeoxygenation],
        },
        f"{fuel}.{biodiesel}": {stream_type: energy_type, value: [Transesterification]},
        f"{fuel}.{ethanol}": {stream_type: energy_type, value: [BiomassFermentation]},
        solid_fuel: {stream_type: energy_type, value: [CoalExtraction, Pelletizing]},
        biomass_dry: {
            stream_type: agriculture_type,
            value: [ManagedWood, UnmanagedWood, CropEnergy],
        },
        electricity: {stream_type: energy_type, value: [WindOffshore]},
        f"{hydrogen}.{liquid_hydrogen}": {
            stream_type: energy_type,
            value: [HydrogenLiquefaction],
        },
        carbon_capture: {
            stream_type: ccus_type,
            value: [
                f"{direct_air_capture}.{AmineScrubbing}",
                f"{direct_air_capture}.{CalciumPotassiumScrubbing}",
                f"{flue_gas_capture}.{CalciumLooping}",
                f"{flue_gas_capture}.{ChilledAmmoniaProcess}",
                f"{flue_gas_capture}.{CO2Membranes}",
                f"{flue_gas_capture}.{MonoEthanolAmine}",
                f"{flue_gas_capture}.{PiperazineProcess}",
                f"{flue_gas_capture}.{PressureSwingAdsorption}",
            ],
        },
        carbon_storage: {
            stream_type: ccus_type,
            value: [
                BiomassBuryingFossilization,
                DeepOceanInjection,
                DeepSalineFormation,
                DepletedOilGas,
                EnhancedOilRecovery,
                GeologicMineralization,
                PureCarbonSolidStorage,
            ],
        },
    }

    DEFAULT_COARSE_TECHNO_DICT = {
        renewable: {stream_type: energy_type, value: [RenewableSimpleTechno]},
        fossil: {stream_type: energy_type, value: [FossilSimpleTechno]},
        carbon_capture: {
            stream_type: ccus_type,
            value: [DirectAirCapture, FlueGasCapture],
        },
        carbon_storage: {
            stream_type: ccus_type,
            value: [CarbonStorageTechno],
        },
    }

    DEFAULT_TECHNO_DICT = {
        methane: {
            stream_type: energy_type,
            value: [FossilGas, UpgradingBiogas, Methanation],
        },
        f"{hydrogen}.{gaseous_hydrogen}": {
            stream_type: energy_type,
            value: [
                WaterGasShift,
                ElectrolysisSOEC,
                ElectrolysisPEM,
                ElectrolysisAWE,
                PlasmaCracking,
            ],
        },
        f"{hydrogen}.{liquid_hydrogen}": {
            stream_type: energy_type,
            value: [HydrogenLiquefaction],
        },
        # methanol: {stream_type: energy_type, 'value': [CO2Hydrogenation]},
        biogas: {stream_type: energy_type, value: [AnaerobicDigestion]},
        syngas: {
            stream_type: energy_type,
            value: [
                BiomassGasification,
                SMR,
                CoalGasification,
                Pyrolysis,
                AutothermalReforming,
                CoElectrolysis,
            ],
        },
        f"{fuel}.{liquid_fuel}": {
            stream_type: energy_type,
            value: [Refinery, FischerTropsch],
        },
        f"{fuel}.{hydrotreated_oil_fuel}": {
            stream_type: energy_type,
            value: [HefaDecarboxylation, HefaDeoxygenation],
        },
        f"{fuel}.{biodiesel}": {stream_type: energy_type, value: [Transesterification]},
        f"{fuel}.{ethanol}": {stream_type: energy_type, value: [BiomassFermentation]},
        solid_fuel: {stream_type: energy_type, value: [CoalExtraction, Pelletizing]},
        biomass_dry: {stream_type: agriculture_type, value: []},
        electricity: {
            stream_type: energy_type,
            value: [
                WindOffshore,
                WindOnshore,
                SolarPv,
                SolarThermal,
                Hydropower,
                Nuclear,
                CombinedCycleGasTurbine,
                GasTurbine,
                BiogasFired,
                CoalGen,
                OilGen,
                BiomassFired,
            ],
        },
        carbon_capture: {
            stream_type: ccus_type,
            value: [
                f"{direct_air_capture}.{AmineScrubbing}",
                f"{direct_air_capture}.{CalciumPotassiumScrubbing}",
                f"{flue_gas_capture}.{CalciumLooping}",
                f"{flue_gas_capture}.{ChilledAmmoniaProcess}",
                f"{flue_gas_capture}.{CO2Membranes}",
                f"{flue_gas_capture}.{MonoEthanolAmine}",
                f"{flue_gas_capture}.{PiperazineProcess}",
                f"{flue_gas_capture}.{PressureSwingAdsorption}",
            ],
        },
        carbon_storage: {
            stream_type: ccus_type,
            value: [
                BiomassBuryingFossilization,
                DeepOceanInjection,
                DeepSalineFormation,
                DepletedOilGas,
                EnhancedOilRecovery,
                GeologicMineralization,
                PureCarbonSolidStorage,
            ],
        },
    }

    stream_to_type_mapper = {
        fossil: energy_type,
        renewable: energy_type,
        methane: energy_type,
        f'{heat}.{lowtemperatureheat}': energy_type,
        f'{heat}.{mediumtemperatureheat}': energy_type,
        f'{heat}.{hightemperatureheat}': energy_type,
        f'{hydrogen}.{gaseous_hydrogen}': energy_type,
        f'{hydrogen}.{liquid_hydrogen}': energy_type,
        biogas: energy_type,
        syngas: energy_type,
        f'{fuel}.{liquid_fuel}': energy_type,
        f'{fuel}.{hydrotreated_oil_fuel}': energy_type,
        f'{fuel}.{biodiesel}': energy_type,
        f'{fuel}.{ethanol}': energy_type,
        f'{fuel}.{methanol}': energy_type,
        solid_fuel: energy_type,
        biomass_dry: agriculture_type,
        electricity: energy_type,
        carbon_capture: ccus_type,
        carbon_storage: ccus_type
    }

    UraniumResource = "uranium_resource"
    WaterResource = "water_resource"
    SeaWaterResource = "sea_water_resource"
    CO2Resource = "CO2_resource"
    BiomassDryResource = "biomass_dry_resource"
    WetBiomassResource = "wet_biomass_resource"
    NaturalOilResource = "natural_oil_resource"
    MethanolResource = "methanol_resource"
    SodiumHydroxideResource = "sodium_hydroxide_resource"
    WoodResource = "wood_resource"
    CarbonResource = "carbon_resource"
    ManagedWoodResource = "managed_wood_resource"
    OxygenResource = "oxygen_resource"
    DioxygenResource = "dioxygen_resource"
    CrudeOilResource = "crude_oil_resource"
    SolidFuelResource = "solid_fuel_resource"
    CalciumResource = "calcium_resource"
    CalciumOxydeResource = "calcium_oxyde_resource"
    PotassiumResource = "potassium_resource"
    PotassiumHydroxideResource = "potassium_hydroxide_resource"
    AmineResource = "amine_resource"
    EthanolAmineResource = "ethanol_amine_resource"
    MonoEthanolAmineResource = "mono_ethanol_amine_resource"
    GlycerolResource = "glycerol_resource"
    NaturalGasResource = "natural_gas_resource"
    CoalResource = "coal_resource"
    OilResource = "oil_resource"
    CopperResource = "copper_resource"
    PlatinumResource = "platinum_resource"

    ResourcesList = [
        UraniumResource,
        WaterResource,
        SeaWaterResource,
        CO2Resource,
        BiomassDryResource,
        WetBiomassResource,
        NaturalOilResource,
        MethanolResource,
        SodiumHydroxideResource,
        WoodResource,
        CarbonResource,
        ManagedWoodResource,
        OxygenResource,
        DioxygenResource,
        CrudeOilResource,
        SolidFuelResource,
        CalciumResource,
        CalciumOxydeResource,
        PotassiumResource,
        PotassiumHydroxideResource,
        AmineResource,
        EthanolAmineResource,
        MonoEthanolAmineResource,
        GlycerolResource,
        NaturalGasResource,
        CoalResource,
        OilResource,
        CopperResource,
        PlatinumResource,
    ]

    CO2FromFlueGas = "CO2 from Flue Gas"
    bio_oil = "bio_oil"
    char = "char"
    O2 = "O2"
    SolidCarbon = "solid_carbon"

    mass_unit = "Mt"
    energy_unit = "TWh"
    surface_unit = "Gha"

    unit_dicts = {
        renewable: energy_unit,
        fossil: energy_unit,
        biomass_dry: energy_unit,
        methane: energy_unit,
        f"{hydrogen}.{gaseous_hydrogen}": energy_unit,
        f"{hydrogen}.{liquid_hydrogen}": energy_unit,
        biogas: energy_unit,
        syngas: energy_unit,
        f"{fuel}.{liquid_fuel}": energy_unit,
        f"{fuel}.{hydrotreated_oil_fuel}": energy_unit,
        f"{fuel}.{biodiesel}": energy_unit,
        f"{fuel}.{ethanol}": energy_unit,
        f"{fuel}.{methanol}": energy_unit,
        f"{heat}.{lowtemperatureheat}": energy_unit,
        f"{heat}.{mediumtemperatureheat}": energy_unit,
        f"{heat}.{hightemperatureheat}": energy_unit,
        solid_fuel: energy_unit,
        electricity: energy_unit,
        carbon_capture: mass_unit,
        carbon_storage: mass_unit,
        GlossaryWitnessCore.N2O: mass_unit,
        CO2FromFlueGas: mass_unit,
        GlossaryWitnessCore.CH4: mass_unit,
        CO2Resource: mass_unit,
        GlycerolResource: mass_unit,
        WaterResource: mass_unit,
        heating_oil: energy_unit,
        gasoline: energy_unit,
        kerosene: energy_unit,
        ultra_low_sulfur_diesel: energy_unit,
        liquefied_petroleum_gas: energy_unit,
        bio_oil: mass_unit,
        DioxygenResource: mass_unit,
        O2: mass_unit,
        CarbonResource: mass_unit,
        char: mass_unit,
        SolidCarbon: mass_unit,
    }

    techno_byproducts = {
        FossilGas: [GlossaryWitnessCore.CH4, CO2FromFlueGas],
        UpgradingBiogas: [carbon_capture],
        Methanation: [WaterResource],
        WaterGasShift: [CO2FromFlueGas],
        ElectrolysisSOEC: [O2],
        ElectrolysisPEM: [O2],
        ElectrolysisAWE: [O2],
        PlasmaCracking: [SolidCarbon],
        BiomassGasification: [GlossaryWitnessCore.CH4],
        CoalGasification: [CO2FromFlueGas],
        Pyrolysis: [char, bio_oil, CO2FromFlueGas],
        AutothermalReforming: [WaterResource],
        CoElectrolysis: [DioxygenResource],
        Refinery: [
            kerosene,
            ultra_low_sulfur_diesel,
            GlossaryWitnessCore.CH4,
            gasoline,
            CO2FromFlueGas,
            liquefied_petroleum_gas,
            heating_oil,
        ],
        FischerTropsch: [WaterResource, CO2FromFlueGas],
        HefaDecarboxylation: [carbon_capture],
        HefaDeoxygenation: [WaterResource],
        Transesterification: [GlycerolResource],
        BiomassFermentation: [carbon_capture],
        CoalExtraction: [GlossaryWitnessCore.CH4, CO2Resource],
        Pelletizing: [CO2FromFlueGas],
        SolarThermal: [f"{heat}.{hightemperatureheat}"],
        Nuclear: [f"{heat}.{hightemperatureheat}"],
        CombinedCycleGasTurbine: [
            GlossaryWitnessCore.CH4,
            CO2FromFlueGas,
            GlossaryWitnessCore.N2O,
            f"{heat}.{hightemperatureheat}",
        ],
        GasTurbine: [
            GlossaryWitnessCore.CH4,
            CO2FromFlueGas,
            GlossaryWitnessCore.N2O,
            f"{heat}.{hightemperatureheat}",
        ],
        BiogasFired: [f"{heat}.{hightemperatureheat}", CO2FromFlueGas],
        CoalGen: [
            CO2FromFlueGas,
            GlossaryWitnessCore.N2O,
            f"{heat}.{hightemperatureheat}",
        ],
        OilGen: [
            CO2FromFlueGas,
            GlossaryWitnessCore.N2O,
            f"{heat}.{hightemperatureheat}",
        ],
        BiomassFired: [f"{heat}.{hightemperatureheat}", CO2FromFlueGas],
        f"{direct_air_capture}.{AmineScrubbing}": [CO2FromFlueGas],
        f"{direct_air_capture}.{CalciumPotassiumScrubbing}": [CO2FromFlueGas],
        f"{direct_air_capture}.{DirectAirCaptureTechno}": [CO2FromFlueGas],
        NaturalGasBoilerLowHeat: [CO2FromFlueGas],
        NaturalGasBoilerMediumHeat: [CO2FromFlueGas],
        NaturalGasBoilerHighHeat: [CO2FromFlueGas],
        ElectricBoilerLowHeat: [],
        ElectricBoilerMediumHeat: [],
        ElectricBoilerHighHeat: [],
        HeatPumpLowHeat: [],
        HeatPumpMediumHeat: [],
        HeatPumpHighHeat: [],
        CHPLowHeat: [electricity, CO2FromFlueGas],
        CHPMediumHeat: [electricity, CO2FromFlueGas],
        CHPHighHeat: [electricity, CO2FromFlueGas],
        GeothermalLowHeat: [carbon_capture],
        GeothermalMediumHeat: [carbon_capture],
        GeothermalHighHeat: [carbon_capture],
        HydrogenLiquefaction: [],
        AnaerobicDigestion: [],
        WindOffshore: [],
        WindOnshore: [],
        SolarPv: [],
        Hydropower: [],
        f"{flue_gas_capture}.{CalciumLooping}": [],
        f"{flue_gas_capture}.{ChilledAmmoniaProcess}": [],
        f"{flue_gas_capture}.{CO2Membranes}": [],
        f"{flue_gas_capture}.{MonoEthanolAmine}": [],
        f"{flue_gas_capture}.{PiperazineProcess}": [],
        f"{flue_gas_capture}.{PressureSwingAdsorption}": [],
        f"{flue_gas_capture}.{FlueGasTechno}": [],
        BiomassBuryingFossilization: [],
        DeepOceanInjection: [],
        DeepSalineFormation: [],
        DepletedOilGas: [],
        EnhancedOilRecovery: [],
        GeologicMineralization: [],
        PureCarbonSolidStorage: [],
        SMR: [],
        RenewableSimpleTechno: [],
        FossilSimpleTechno: [CO2FromFlueGas, GlossaryWitnessCore.CH4],
        CarbonStorageTechno: [],
        CO2Hydrogenation: [],
        ManagedWood: [],
        UnmanagedWood: [CO2Resource],
        CropEnergy: [],
        Reforestation: [],
        Geothermal: [],
        Crop: [],
        Forest: [],
        ReversedWaterGasShift: [WaterResource],
    }

    # dictionnary of energies used by each techno

    # idee: cree un transport fuel ->

    TechnoStreamsUsedDict = {
        Transesterification: [electricity],  # heat -> low, no electricity
        AnaerobicDigestion: [electricity],  # produce heat -> low, dont consume electricity, consume biomass_dry and wet
        ManagedWood: [electricity],  # consume fuel and electricity .. les tronçonneuses et les camions (donc transport fuel)
        UnmanagedWood: [electricity], # consume fuel and electricity .. les tronçonneuses et les camions (donc transport fuel)
        f"{direct_air_capture}.{AmineScrubbing}": [electricity, methane],   # put heat instead of methane
        f"{direct_air_capture}.{CalciumPotassiumScrubbing}": [electricity, methane], # put heat instead of methane
        f"{direct_air_capture}.{DirectAirCaptureTechno}": [renewable, fossil], # dont touch
        # in flue gas techno: heat comes directly from plant so just electricity
        f"{flue_gas_capture}.{CalciumLooping}": [electricity], # heat and electricity
        f"{flue_gas_capture}.{ChilledAmmoniaProcess}": [electricity], # heat and electricity
        f"{flue_gas_capture}.{CO2Membranes}": [electricity], # heat and electricity
        f"{flue_gas_capture}.{FlueGasTechno}": [renewable], # heat and electricity -> not heat because
        f"{flue_gas_capture}.{MonoEthanolAmine}": [electricity], # heat and electricity
        f"{flue_gas_capture}.{PiperazineProcess}": [electricity], # heat and electricity
        f"{flue_gas_capture}.{PressureSwingAdsorption}": [electricity], # heat and electricity
        BiomassFired: [biomass_dry],
        CoalGen: [solid_fuel],
        GasTurbine: [methane],
        CombinedCycleGasTurbine: [methane],
        BiogasFired: [biogas],
        OilGen: [f"{fuel}.{liquid_fuel}"],
        BiomassFermentation: [biomass_dry, electricity], # heat instead of electricity
        ElectrolysisAWE: [electricity],
        ElectrolysisPEM: [electricity],
        ElectrolysisSOEC: [electricity],
        PlasmaCracking: [electricity, methane],
        WaterGasShift: [electricity, syngas],  # heat instead of electricity
        CHPHighHeat: [methane],
        ElectricBoilerHighHeat: [electricity],
        GeothermalHighHeat: [electricity],
        HeatPumpHighHeat: [electricity],
        NaturalGasBoilerHighHeat: [methane],
        CHPLowHeat: [methane],
        ElectricBoilerLowHeat: [electricity],
        GeothermalLowHeat: [electricity],
        HeatPumpLowHeat: [electricity],
        NaturalGasBoilerLowHeat: [methane],
        CHPMediumHeat: [methane],
        ElectricBoilerMediumHeat: [electricity],
        GeothermalMediumHeat: [electricity],
        HeatPumpMediumHeat: [electricity],
        FischerTropsch: [electricity],
        NaturalGasBoilerMediumHeat: [methane],
        HefaDecarboxylation: [f"{hydrogen}.{gaseous_hydrogen}", electricity],  # heat instead of electricity, use resource natural_oil (trygliceride)
        HefaDeoxygenation: [f"{hydrogen}.{gaseous_hydrogen}", electricity],  # heat instead of electricity, use resource natural_oil (trygliceride)
        Refinery: [f"{hydrogen}.{gaseous_hydrogen}", electricity],  # idea : creer une techno puit de pétrole (CrudeOil)
        HydrogenLiquefaction: [f"{hydrogen}.{gaseous_hydrogen}", electricity],  # might need some heat ? produced or consumed, not clear
        FossilGas: [electricity], # "transport fuel"
        Methanation: [f"{hydrogen}.{gaseous_hydrogen}"],  # consumed CO2 (which can come from carbon_capture)
        UpgradingBiogas: [electricity, biogas], # heat not electricity
        CO2Hydrogenation: [
            f"{hydrogen}.{gaseous_hydrogen}",
            electricity,
            carbon_capture,  # consumed CO2 (which can come from carbon_capture)
        ],
        CoalExtraction: [electricity],  # transport fuel instead of electricity
        Pelletizing: [electricity, biomass_dry],  # might be heat instead of electricity
        AutothermalReforming: [methane], # add heat
        BiomassGasification: [electricity, biomass_dry],  # heat instead of electricity, produce syngas
        CoElectrolysis: [electricity],  # consumed CO2 (which can come from carbon_capture)
        CoalGasification: [solid_fuel],  # add heat
        ReversedWaterGasShift: [electricity, syngas], # heat instead of electricity, CO2 instead of carbon_capture
        SMR: [electricity, methane],  # heat instead of elec
        AnimalManure: [electricity],  # transport fuel in stead of elec
        WetCropResidues: [electricity], # transport fuel in stead of elec
        Geothermal: [f"{heat}.{mediumtemperatureheat}"],  # just electricity
        BiomassBuryingFossilization: [biomass_dry],  # add transport fuel
        DeepOceanInjection: [carbon_capture],  # add transport fuel
        DeepSalineFormation: [carbon_capture],  # add transport fuel
        DepletedOilGas: [carbon_capture],  # add transport fuel
        EnhancedOilRecovery: [carbon_capture],  # add transport fuel
        GeologicMineralization: [carbon_capture],  # add transport fuel
        CarbonStorageTechno: [carbon_capture],
    }

    # dict of resources used by technos
    TechnoResourceUsedDict = {
        Transesterification: [
            MethanolResource,
            NaturalOilResource,
            SodiumHydroxideResource,
            WaterResource,
        ],
        AnaerobicDigestion: [WetBiomassResource],
        f"{direct_air_capture}.{AmineScrubbing}": [AmineResource],
        f"{direct_air_capture}.{CalciumPotassiumScrubbing}": [
            CalciumResource,
            PotassiumResource,
        ],
        CoalGen: [WaterResource],
        Nuclear: [UraniumResource, WaterResource],
        OilGen: [WaterResource],
        BiomassFermentation: [WaterResource],
        ElectrolysisAWE: [WaterResource],
        ElectrolysisPEM: [WaterResource, PlatinumResource],
        ElectrolysisSOEC: [WaterResource],
        Refinery: [OilResource],
        FossilGas: [NaturalGasResource],
        Methanation: [CO2Resource],
        CO2Hydrogenation: [WaterResource],
        CoalExtraction: [CoalResource],
        AutothermalReforming: [CO2Resource, OxygenResource],
        CoElectrolysis: [CO2Resource, WaterResource],
        Pyrolysis: [WoodResource],
        WaterGasShift: [WaterResource],
        ReversedWaterGasShift: [CO2Resource],
        SMR: [WaterResource],
        HefaDecarboxylation: [NaturalOilResource],
        HefaDeoxygenation: [NaturalOilResource],
        BiomassGasification: [WaterResource],
        CropEnergy: [CO2Resource],
        UpgradingBiogas: [MonoEthanolAmineResource],
        PureCarbonSolidStorage: [SolidCarbon],  # note : could be a stream but we prefered to let it as a resource for the moment
    }

    #TechnoResourceUsedDict[FischerTropsch] = TechnoResourceUsedDict[ReversedWaterGasShift] + TechnoResourceUsedDict[WaterGasShift]

    TechnoBuildingResourceDict = {
        CoalGen: [CopperResource],
        Nuclear: [CopperResource],
        OilGen: [CopperResource],
        WindOnshore: [CopperResource],
        WindOffshore: [CopperResource],
        SolarPv: [CopperResource],
        SolarThermal: [CopperResource],
        Hydropower: [CopperResource],
        CombinedCycleGasTurbine: [CopperResource],
        GasTurbine: [CopperResource],
        BiogasFired: [CopperResource],
        BiomassFired: [CopperResource],
    }

    TechnoStreamProducedDict = {
        FossilGas: methane,
        UpgradingBiogas: methane,
        Methanation: methane,
        ElectrolysisSOEC: f"{hydrogen}.{gaseous_hydrogen}",
        ElectrolysisPEM: f"{hydrogen}.{gaseous_hydrogen}",
        ElectrolysisAWE: f"{hydrogen}.{gaseous_hydrogen}",
        PlasmaCracking: f"{hydrogen}.{gaseous_hydrogen}",
        HydrogenLiquefaction: f"{hydrogen}.{liquid_hydrogen}",
        AnaerobicDigestion: biogas,
        BiomassGasification: syngas,
        SMR: syngas,
        CoalGasification: syngas,
        Pyrolysis: syngas,
        AutothermalReforming: syngas,
        CoElectrolysis: syngas,
        Refinery: f"{fuel}.{liquid_fuel}",
        FischerTropsch: f"{fuel}.{liquid_fuel}",
        HefaDecarboxylation: f'{fuel}.{hydrotreated_oil_fuel}',
        HefaDeoxygenation: f'{fuel}.{hydrotreated_oil_fuel}',
        Transesterification: f'{fuel}.{biodiesel}',
        BiomassFermentation: f'{fuel}.{ethanol}',
        CoalExtraction: solid_fuel,
        Pelletizing: solid_fuel,
        WindOffshore: electricity,
        WindOnshore: electricity,
        SolarPv: electricity,
        SolarThermal: electricity,
        Hydropower: electricity,
        Nuclear: electricity,
        CombinedCycleGasTurbine: electricity,
        GasTurbine: electricity,
        BiogasFired: electricity,
        CoalGen: electricity,
        OilGen: electricity,
        BiomassFired: electricity,
        f"{direct_air_capture}.{AmineScrubbing}": carbon_capture,
        f"{direct_air_capture}.{CalciumPotassiumScrubbing}": carbon_capture,
        f"{flue_gas_capture}.{CalciumLooping}": carbon_capture,
        f"{flue_gas_capture}.{ChilledAmmoniaProcess}": carbon_capture,
        f"{flue_gas_capture}.{CO2Membranes}": carbon_capture,
        f"{flue_gas_capture}.{MonoEthanolAmine}": carbon_capture,
        f"{flue_gas_capture}.{PiperazineProcess}": carbon_capture,
        f"{flue_gas_capture}.{PressureSwingAdsorption}": carbon_capture,
        BiomassBuryingFossilization: carbon_storage,
        DeepOceanInjection: carbon_storage,
        DeepSalineFormation: carbon_storage,
        DepletedOilGas: carbon_storage,
        EnhancedOilRecovery: carbon_storage,
        GeologicMineralization: carbon_storage,
        PureCarbonSolidStorage: carbon_storage,
        ReversedWaterGasShift: syngas,
        WaterGasShift: f"{hydrogen}.{gaseous_hydrogen}",
        f"{direct_air_capture}.{DirectAirCaptureTechno}": carbon_capture,
        CropEnergy: biomass_dry,
        ManagedWood: biomass_dry,
        CarbonStorageTechno: carbon_storage,
        Reforestation: carbon_storage,
        Geothermal: electricity,
        UnmanagedWood: biomass_dry,
        f"{flue_gas_capture}.{FlueGasTechno}": carbon_capture,
        ElectricBoilerHighHeat: f"{heat}.{hightemperatureheat}",
        HeatPumpHighHeat: f"{heat}.{hightemperatureheat}",
        GeothermalHighHeat: f"{heat}.{hightemperatureheat}",
        CHPHighHeat: f"{heat}.{hightemperatureheat}",
        NaturalGasBoilerHighHeat: f"{heat}.{hightemperatureheat}",
        NaturalGasBoilerLowHeat: f"{heat}.{lowtemperatureheat}",
        CHPMediumHeat: f"{heat}.{mediumtemperatureheat}",
        HeatPumpMediumHeat: f"{heat}.{mediumtemperatureheat}",
        ElectricBoilerLowHeat: f"{heat}.{lowtemperatureheat}",
        GeothermalLowHeat: f"{heat}.{lowtemperatureheat}",
        ElectricBoilerMediumHeat: f"{heat}.{mediumtemperatureheat}",
        GeothermalMediumHeat: f"{heat}.{mediumtemperatureheat}",
        #CO2Hydrogenation: f'{fuel}.{methanol}',
        NaturalGasBoilerMediumHeat: f"{heat}.{mediumtemperatureheat}",
        HeatPumpLowHeat: f"{heat}.{lowtemperatureheat}",
        CHPLowHeat: f"{heat}.{lowtemperatureheat}",
        RenewableSimpleTechno: renewable,
        FossilSimpleTechno: fossil,
    }

    @classmethod
    def get_land_use_df(cls, techno_name: str):
        return {
            "type": "dataframe",
            "unit": "Gha",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, GlossaryWitnessCore.YearEndDefault], False),
                f"{techno_name} ({cls.surface_unit})": ("float", None, False),
            },
        }

    @classmethod
    def get_non_use_capital_df(cls, techno_name: str):
        return {
            "type": "dataframe",
            "unit": "G$",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, GlossaryWitnessCore.YearEndDefault], False),
                techno_name: ("float", None, False),
            },
        }

    @classmethod
    def get_techno_detailed_price_df(cls, techno_name: str):
        techno_used_resource_list = (
            cls.TechnoResourceUsedDict[techno_name]
            if techno_name in cls.TechnoResourceUsedDict
            else []
        )
        techno_used_streams_list = (
            cls.TechnoStreamsUsedDict[techno_name]
            if techno_name in cls.TechnoStreamsUsedDict
            else []
        )
        extra_cols = []
        if techno_name == cls.PlasmaCracking:
            extra_cols = [f"{techno_name}_amort", f"{techno_name}_factory_amort"]
        if techno_name == cls.FischerTropsch:
            extra_cols = [
                "syngas before transformation",
                "RWGS",
                "WGS",
                "WGS or RWGS",
                "syngas_needs_for_FT",
            ]
        return {
            "type": "dataframe",
            "unit": "$/MWh",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, GlossaryWitnessCore.YearEndDefault], False),
                f"{techno_name}": ("float", None, False),
                f"{techno_name}_wotaxes": ("float", None, False),
                f"Capex_{techno_name}": ("float", None, False),
                cls.InvestValue: ("float", None, False),
                "efficiency": ("float", None, False),
                "energy_costs": ("float", None, False),
                "transport": ("float", None, False),
                f"{techno_name}_factory": ("float", None, False),
                cls.MarginValue: ("float", None, False),
                "CAPEX_Part": ("float", None, False),
                "OPEX_Part": ("float", None, False),
                "CO2_taxes_factory": ("float", None, False),
                "CO2Tax_Part": ("float", None, False),
                **{
                    f"{resource}_needs": ("float", None, False)
                    for resource in techno_used_resource_list
                },
                **{
                    f"{stream}_needs": ("float", None, False)
                    for stream in techno_used_streams_list
                },
                **{col: ("float", None, False) for col in extra_cols},
            },
        }

    @classmethod
    def get_techno_price_df(cls, techno_name: str):
        return {
            "type": "dataframe",
            "unit": "$/MWh",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, GlossaryWitnessCore.YearEndDefault], False),
                f"{techno_name}": ("float", None, False),
                f"{techno_name}_wotaxes": ("float", None, False),
            },
        }

    @classmethod
    def get_age_distrib_prod_df(cls, energy_name: str):
        techno_unit = cls.unit_dicts[energy_name]
        return {
            "type": "dataframe",
            "unit": techno_unit,
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, GlossaryWitnessCore.YearEndDefault], False),
                f"distrib_prod ({techno_unit})": ("float", None, False),
                "age_x_prod": ("float", None, False),
            },
        }

    @classmethod
    def get_techno_prod_df(
        cls, energy_name: str, techno_name: str, byproducts_list: list[str]
    ):
        return {
            "type": "dataframe",
            "unit": cls.unit_dicts[energy_name],
            "description": f"Production of {energy_name} by from techno {techno_name}",
            "dataframe_descriptor": {
                cls.Years: (
                    "int",
                    [1900, GlossaryWitnessCore.YearEndDefault],
                    False,
                ),
                f"{energy_name} ({cls.unit_dicts[energy_name]})": (
                    "float",
                    None,
                    False,
                ),
                **{
                    f"{bp} ({cls.unit_dicts[bp]})": ("float", None, False)
                    for bp in byproducts_list
                },
            },
        }

    @classmethod
    def get_stream_prices_df(cls, stream_used_for_production: list[str]):
        return {
            "varname": cls.StreamPricesValue,
            "type": "dataframe",
            "unit": "$/MWh or $/mass",
            "visibility": "Shared",
            "namespace": cls.NS_ENERGY,
            "description": "Price of streams used by the technos",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, 2100], False),
                **{
                    stream: ("float", [0.0, 1e30], False)
                    for stream in stream_used_for_production
                },
            },
        }

    @classmethod
    def get_stream_co2_emissions_df(cls, stream_used_for_production: list[str]):
        return {
            "var_name": cls.StreamsCO2EmissionsValue,
            "type": "dataframe",
            "unit": "kg/kWh",
            "visibility": "Shared",
            "namespace": cls.NS_ENERGY,
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, 2100], False),
                **{
                    stream: ("float", [0.0, 1e30], False)
                    for stream in stream_used_for_production
                },
            },
        }

    @classmethod
    def get_techno_consumption_df(
        cls,
        techno_name: str,
        resources_used_for_building: list[str],
        resources_used_for_production: list[str],
        stream_used_for_production: list[str],
    ):
        extra_cols = []
        if techno_name == GlossaryEnergy.FischerTropsch:
            extra_cols = [
                f"{cls.carbon_capture} ({cls.unit_dicts[cls.carbon_capture]})",
                f"{cls.syngas} ({cls.unit_dicts[cls.syngas]})",
                f"{cls.WaterResource} ({cls.mass_unit})",
            ]
        if techno_name == GlossaryEnergy.ReversedWaterGasShift:
            extra_cols = [
                f"{cls.carbon_capture} ({cls.unit_dicts[cls.carbon_capture]})",
            ]

        return {
            "type": "dataframe",
            "unit": "see columns",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, 2100], False),
                **{
                    f"{stream} ({cls.unit_dicts[stream]})": (
                        "float",
                        [0.0, 1e30],
                        False,
                    )
                    for stream in stream_used_for_production
                },
                **{
                    f"{resource} ({cls.mass_unit})": ("float", [0.0, 1e30], False)
                    for resource in resources_used_for_building
                },
                **{
                    f"{resource} ({cls.mass_unit})": ("float", [0.0, 1e30], False)
                    for resource in resources_used_for_production
                },
                **{col: ("float", None, False) for col in extra_cols},
            },
        }

    @classmethod
    def get_one_stream_price_df(cls, stream_name: str):
        return {
            "varname": cls.StreamPricesValue,
            "type": "dataframe",
            "unit": "$/MWh",
            "dataframe_descriptor": {
                cls.Years: ("int", [1900, 2100], False),
                f"{stream_name}": ("float", [0.0, 1e30], False),
                f"{stream_name}_wotaxes": ("float", [0.0, 1e30], False),
            },
        }
