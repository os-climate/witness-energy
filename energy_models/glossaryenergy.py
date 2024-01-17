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

    CO2Taxes = GlossaryWitnessCore.CO2Taxes
    CO2Taxes["namespace"] = "ns_energy_study"

    NB_POLES_COARSE: int = 20

    AllStreamsDemandRatioValue = "all_streams_demand_ratio"
    FlueGasMean = "flue_gas_mean"
    MarginValue = "margin"
    CO2EmissionsValue = "CO2_emissions"
    EnergyCO2EmissionsValue = "energy_CO2_emissions"
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
    InstalledPower = "power_production"  # todo : rename string to 'Installed Power [MW]' (check unit)

    # energy techno discipline names
    FossilSimpleTechno = 'FossilSimpleTechno'
    RenewableSimpleTechno = 'RenewableSimpleTechno'
    CarbonCaptureAndStorageTechno = 'CarbonCaptureAndStorageTechno'
    CarbonStorageTechno = 'CarbonStorageTechno'
    DirectAirCapture = 'direct_air_capture.DirectAirCaptureTechno'
    FlueGasCapture = 'flue_gas_capture.FlueGasTechno'

    CCSTechnoInvest = {
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "namespace": "ns_ccs",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            "invest": ("float", None, True),
        },
    }

    EnergyTechnoInvest = {
        "type": "dataframe",
        "unit": "G$",
        "visibility": "Shared",
        "namespace": "ns_energy",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            "invest": ("float", None, True),
        },
    }
    TechnoCapitalDf = {
        "var_name": GlossaryWitnessCore.TechnoCapitalValue,
        "type": "dataframe",
        "unit": "G$",
        "description": "Capital in G$ of the technology",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            GlossaryWitnessCore.Capital: ("float", None, False),
        },
    }

    UtilisationRatioDf = {
        "var_name": GlossaryWitnessCore.UtilisationRatioValue,
        "type": "dataframe",
        "namespace": "ns_witness",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            GlossaryWitnessCore.UtilisationRatioValue: ("float", [0, 100], False),
        },
    }


    EnergyTypeCapitalDfValue = "energy_type_capital"
    EnergyTypeCapitalDf = {
        "var_name": EnergyTypeCapitalDfValue,
        "type": "dataframe",
        "unit": "G$",
        # 'namespace': 'ns_energy',
        # 'visibility': 'Shared',
        "description": "Capital in G$ of the energy type",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            GlossaryWitnessCore.Capital: ("float", None, False),
        },
    }

    TechnoInvestPercentageName = "techno_invest_percentage"
    TechnoInvestPercentage = {
        "var_name": TechnoInvestPercentageName,
        "type": "dataframe",
        "dataframe_descriptor": {GlossaryWitnessCore.Years: ("int", [1900, 2100], False), },
        "unit": "%",
        "description": "Percentage of investments in each energy technology based on total energy investments",
    }

    EnergyInvestPercentageGDPName = "percentage_of_gdp_energy_invest"
    EnergyInvestPercentageGDP = {
        "var_name": EnergyInvestPercentageGDPName,
        "type": "dataframe",
        "unit": "%",

        "dataframe_descriptor": {GlossaryWitnessCore.Years: ('int', None, False),
                                 EnergyInvestPercentageGDPName: ('float', None, True)},
        "description": "percentage of total energy investment in each of the energy technologies",
    }

    ManagedWoodInvestmentName = "managed_wood_investment"
    ManagedWoodInvestment = {'var_name': ManagedWoodInvestmentName,
                             'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                             'dataframe_descriptor': {GlossaryWitnessCore.Years: ('float', None, False),
                                                      GlossaryWitnessCore.InvestmentsValue: ('float', None, False)},
                             'namespace': 'ns_forest', 'dataframe_edition_locked': False, }

    DeforestationInvestmentName = "deforestation_investment"
    DeforestationInvestment = {'var_name': DeforestationInvestmentName,
                               'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                               'dataframe_descriptor': {GlossaryWitnessCore.Years: ('float', None, False),
                                                        GlossaryWitnessCore.InvestmentsValue: ('float', None, False)},
                               'namespace': 'ns_forest', 'dataframe_edition_locked': False}

    CropInvestmentName = "crop_investment"
    CropInvestment = {'var_name': CropInvestmentName,
                      'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                      'dataframe_descriptor': {GlossaryWitnessCore.Years: ('float', None, False),
                                               GlossaryWitnessCore.InvestmentsValue: ('float', None, False)},
                      'namespace': 'ns_crop', 'dataframe_edition_locked': False}

    TechnoListName = "technologies_list"
    TechnoList = {'var_name': TechnoListName,
                  'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                  'visibility': 'Shared'}

    InvestLevel = {'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared'}

    EnergyList = {'var_name': EnergyListName, 'type': 'list', 'subtype_descriptor': {'list': 'string'},
                  'visibility': 'Shared', 'namespace': 'ns_energy_study',
                  'editable': False, 'structuring': True}

    CCSList = {'var_name': CCSListName, 'type': 'list', 'subtype_descriptor': {'list': 'string'},
               'visibility': 'Shared', 'namespace': 'ns_energy_study',
               'editable': False, 'structuring': True}

    ForestInvestment = {'var_name': ForestInvestmentValue, 'type': 'dataframe', 'unit': 'G$',
                        'visibility': 'Shared',
                        'dataframe_descriptor': {GlossaryWitnessCore.Years: ('float', None, False),
                                                 ForestInvestmentValue: (
                                                     'float', None, False)},
                        'namespace': 'ns_invest',
                        'dataframe_edition_locked': False}
