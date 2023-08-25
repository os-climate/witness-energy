from climateeconomics.glossarycore import GlossaryCore as GlossaryWitnessCore


class GlossaryEnergy(GlossaryWitnessCore):
    """Glossary for witness energy, inheriting from glossary of Witness Core"""
    CO2Taxes = GlossaryWitnessCore.CO2Taxes
    CO2Taxes['namespace'] = 'ns_energy_study'
