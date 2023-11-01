from climateeconomics.glossarycore import GlossaryCore as GlossaryWitnessCore


class GlossaryEnergy(GlossaryWitnessCore):
    """Glossary for witness energy, inheriting from glossary of Witness Core"""

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
