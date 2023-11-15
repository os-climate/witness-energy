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
    TechnoListName = "technologies_list"

    CO2Taxes = GlossaryWitnessCore.CO2Taxes
    CO2Taxes["namespace"] = "ns_energy_study"

    NB_POLES_COARSE: int = 20

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
    TechnoCapitalDfValue = "techno_capital"
    TechnoCapitalDf = {
        "var_name": TechnoCapitalDfValue,
        "type": "dataframe",
        "unit": "G$",
        "description": "Capital in G$ of the technology",
        "dataframe_descriptor": {
            GlossaryWitnessCore.Years: ("int", [1900, 2100], False),
            GlossaryWitnessCore.Capital: ("float", None, False),
        },
    }

    EnergyTypeCapitalDfValue = "energy_type_capital"
    EnergyTypeCapitalDf = {
        "var_name": EnergyTypeCapitalDfValue,
        "type": "dataframe",
        "unit": "G$",
        #'namespace': 'ns_energy',
        #'visibility': 'Shared',
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
        "type": "float",
        "unit": "%",
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