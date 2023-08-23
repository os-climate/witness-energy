from climateeconomics.glossary import Glossary as GlossaryWitnessCore


class Glossary(GlossaryWitnessCore):
    """Glossary for witness energy, inheriting from glossary of Witness Core"""
    CO2Taxes = GlossaryWitnessCore.CO2Taxes
    CO2Taxes['namespace'] = 'ns_energy_study'
