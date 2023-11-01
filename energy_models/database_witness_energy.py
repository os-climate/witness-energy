from datetime import date

class ColectedData:
    def __init__(self,
                 value,
                 description: str,
                 link: str,
                 source: str,
                 last_update_date: date):
        self.value = value
        self.description = description
        self.link = link
        self.source = source
        self.last_update_date = last_update_date


class DatabaseWitnessEnergy:
    # Example :
    InvestFossil2020 = ColectedData(839.,
                                    description="Investment in fossil in 2020 in G US$",
                                    link="https://www.iea.org/reports/world-energy-investment-2023/overview-and-key-findings",
                                    source="World energy investment - IEA",
                                    last_update_date=date(2023, 10, 26))

    InvestCleanEnergy2020 = ColectedData(1259.,
                                    description="Investment in clean energy in 2020 in G US$",
                                    link="https://www.iea.org/reports/world-energy-investment-2023/overview-and-key-findings",
                                    source="World energy investment - IEA",
                                    last_update_date=date(2023, 10, 26))

    InvestCCUS2020 = ColectedData(4.,
                                    description="Investment in all CCUS technos in 2020 in G US$",
                                    link="https://iea.blob.core.windows.net/assets/181b48b4-323f-454d-96fb-0bb1889d96a9/CCUS_in_clean_energy_transitions.pdf", #page 13
                                    source="CCUS in clean energy transitions - IEA",
                                    last_update_date=date(2023, 10, 26))

