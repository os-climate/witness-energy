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
from datetime import date
from os.path import join
from pathlib import Path

import pandas as pd


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
    data_folder = join(Path(__file__).parents[1], 'data_energy', 'data')
    data_invest = pd.read_csv(join(data_folder, 'invest_in_fossil.csv'))
    data_invest_nze_scenario = pd.read_csv(join(data_folder, 'nze_scenario.csv'))
    data_invest_steps_scenario = pd.read_csv(join(data_folder, 'scenario_steps.csv'))
    InvestFossil = ColectedData(data_invest,
                                    description="Percentage of Investment between 2020 and 2100 for the full fossil investment scenario",
                                    link="https://www.iea.org/data-and-statistics/data-product/world-energy-investment-2023-datafile-2#",
                                    source="World energy investment - IEA",
                                    last_update_date=date(2023, 11, 22))
    InvestNZE = ColectedData(data_invest_nze_scenario,
                                description="Percentage of Investment between 2020 and 2100 for nze scenario",
                                link="https://iea.blob.core.windows.net/assets/deebef5d-0c34-4539-9d0c-10b13d840027/NetZeroby2050-ARoadmapfortheGlobalEnergySector_CORR.pdf ",
                                source="World energy investment - IEA",
                                last_update_date=date(2023, 11, 22))
    InvestSteps = ColectedData(data_invest_steps_scenario,
                                description="Percentage of Investment between 2020 and 2100 for STEPS scenario",
                                link="https://iea.blob.core.windows.net/assets/614bb748-dc5e-440b-966a-adae9ea022fe/WorldEnergyOutlook2023.pdf",
                                source="World energy investment - IEA",
                                last_update_date=date(2023, 11, 22))



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

