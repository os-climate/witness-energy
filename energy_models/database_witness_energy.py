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
import datetime
import os
from datetime import date
from os.path import join
from pathlib import Path

import pandas as pd
from climateeconomics.database.collected_data import ColectedData, HeavyCollectedData


class DatabaseWitnessEnergy:
    # Example :
    # todo : change following dataframe loading to HeavyCollectedData
    data_folder = join(Path(__file__).parents[1], "data_energy", "data")
    data_invest = pd.read_csv(join(data_folder, "invest_in_fossil.csv"))
    data_invest_nze_scenario = pd.read_csv(join(data_folder, "nze_scenario.csv"))
    data_invest_steps_scenario = pd.read_csv(join(data_folder, "scenario_steps.csv"))

    InvestFossil = ColectedData(
        value=data_invest,
        unit="%",
        description="Percentage of Investment between 2020 and GlossaryEnergy.YearEndDefaultCore for the full fossil investment scenario",
        link="https://www.iea.org/data-and-statistics/data-product/world-energy-investment-2023-datafile-2#",
        source="World energy investment - IEA",
        last_update_date=date(2023, 11, 22),
    )
    InvestNZE = ColectedData(
        value=data_invest_nze_scenario,
        unit="%",
        description="Percentage of Investment between 2020 and GlossaryEnergy.YearEndDefaultCore for nze scenario",
        link="https://iea.blob.core.windows.net/assets/deebef5d-0c34-4539-9d0c-10b13d840027/NetZeroby2050-ARoadmapfortheGlobalEnergySector_CORR.pdf ",
        source="World energy investment - IEA",
        last_update_date=date(2023, 11, 22),
    )
    InvestSteps = ColectedData(
        value=data_invest_steps_scenario,
        unit="%",
        description="Percentage of Investment between 2020 and GlossaryEnergy.YearEndDefaultCore for STEPS scenario",
        link="https://iea.blob.core.windows.net/assets/614bb748-dc5e-440b-966a-adae9ea022fe/WorldEnergyOutlook2023.pdf",
        source="World energy investment - IEA",
        last_update_date=date(2023, 11, 22),
    )

    InvestFossil2020 = ColectedData(
        value=839.0,
        unit="G$",
        description="Investment in fossil in 2020 in G US$",
        link="https://www.iea.org/reports/world-energy-investment-2023/overview-and-key-findings",
        source="World energy investment - IEA",
        last_update_date=date(2023, 10, 26),
    )

    InvestCleanEnergy2020 = ColectedData(
        value=1259.0,
        unit="G$",
        description="Investment in clean energy in 2020 in G US$",
        link="https://www.iea.org/reports/world-energy-investment-2023/overview-and-key-findings",
        source="World energy investment - IEA",
        last_update_date=date(2023, 10, 26),
    )

    InvestCCUS2020 = ColectedData(
        value=4.0,
        unit="G$",
        description="Investment in all CCUS technos in 2020 in G US$",
        link="https://iea.blob.core.windows.net/assets/181b48b4-323f-454d-96fb-0bb1889d96a9/CCUS_in_clean_energy_transitions.pdf",
        # page 13
        source="CCUS in clean energy transitions - IEA",
        last_update_date=date(2023, 10, 26),
    )

    invest_before_year_start_folder = join(Path(__file__).parents[1], "data_energy", "techno_invests")

    @classmethod
    def get_techno_invest_before_year_start(cls, techno_name: str, year_start: int, construction_delay: int, is_available_at_year: bool = False):
        name_formatted = techno_name.replace(".", "_")
        name_formatted = name_formatted.lower()
        path_to_csv = os.path.join(cls.invest_before_year_start_folder, name_formatted) + ".csv"
        df = pd.read_csv(path_to_csv)
        heavy_collected_data = HeavyCollectedData(
            value=path_to_csv,
            description="",
            unit="G$",
            link="",
            source="",
            last_update_date=datetime.datetime.today(),
            critical_at_year_start=True,
            column_to_pick="invest"
        )
        out_df = df.loc[df['years'] < year_start]
        if is_available_at_year:
            return construction_delay == 0 or (heavy_collected_data.is_available_at_year(year_start - construction_delay) and heavy_collected_data.is_available_at_year(year_start - 1))
        if construction_delay > 0:
            out_df = heavy_collected_data.get_between_years(year_start=year_start - construction_delay, year_end=year_start - 1)
        return out_df, heavy_collected_data


    techno_production_historic_folder = join(Path(__file__).parents[1], "data_energy", "techno_production_historic")
    @classmethod
    def get_techno_prod(cls, techno_name: str, year: int, is_available_at_year: bool = False):
        name_formatted = techno_name.replace(".", "_")
        name_formatted = name_formatted.lower()
        path_to_csv = os.path.join(cls.techno_production_historic_folder, name_formatted) + ".csv"
        df = pd.read_csv(path_to_csv)
        heavy_collected_data = HeavyCollectedData(
            value=path_to_csv,
            description="",
            unit=df["unit"].values[0],
            link="",
            source="",
            last_update_date=datetime.datetime.today(),
            critical_at_year_start=True,
            column_to_pick="production"
        )
        if is_available_at_year:
            return heavy_collected_data.is_available_at_year(year=year)

        out = heavy_collected_data.get_value_at_year(year=year)
        return out, heavy_collected_data


    techno_age_distrib_folder = join(Path(__file__).parents[1], "data_energy", "techno_factories_age")

    @classmethod
    def get_techno_age_distrib(cls, techno_name: str, year: int, is_available_at_year: bool = False):
        name_formatted = techno_name.replace(".", "_")
        name_formatted = name_formatted.lower()
        path_to_csv = os.path.join(cls.techno_age_distrib_folder, name_formatted) + ".csv"
        heavy_collected_data = HeavyCollectedData(
            value=path_to_csv,
            description="",
            unit="-",
            link="",
            source="",
            last_update_date=datetime.datetime.today(),
            critical_at_year_start=True,
            column_to_pick="growth_rate"
        )
        if is_available_at_year:
            return heavy_collected_data.is_available_at_year(year=year)

        out = heavy_collected_data.get_value_at_year(year=year)
        return out, heavy_collected_data

