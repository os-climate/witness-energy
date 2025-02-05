'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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
import logging

from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_core.tools.post_processing.tables.instanciated_table import (
    InstanciatedTable,
)
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_capture.direct_air_capture.amine_scrubbing.amine_scrubbing_disc import (
    AmineScrubbingDiscipline,
)
from energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc import (
    CalciumPotassiumScrubbingDiscipline,
)
from energy_models.models.carbon_capture.direct_air_capture.direct_air_capture_techno.direct_air_capture_techno_disc import (
    DirectAirCaptureTechnoDiscipline,
)
from energy_models.models.electricity.coal_gen.coal_gen_disc import CoalGenDiscipline
from energy_models.models.electricity.gas.combined_cycle_gas_turbine.combined_cycle_gas_turbine_disc import (
    CombinedCycleGasTurbineDiscipline,
)
from energy_models.models.electricity.gas.gas_turbine.gas_turbine_disc import (
    GasTurbineDiscipline,
)
from energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc import (
    FossilSimpleTechnoDiscipline,
)
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc import (
    WaterGasShiftDiscipline,
)
from energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc import (
    FischerTropschDiscipline,
)
from energy_models.models.liquid_fuel.refinery.refinery_disc import RefineryDiscipline
from energy_models.models.methane.fossil_gas.fossil_gas_disc import FossilGasDiscipline
from energy_models.models.solid_fuel.pelletizing.pelletizing_disc import (
    PelletizingDiscipline,
)
from energy_models.models.syngas.coal_gasification.coal_gasification_disc import (
    CoalGasificationDiscipline,
)
from energy_models.models.syngas.pyrolysis.pyrolysis_disc import PyrolysisDiscipline


class FlueGasDiscipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        'label': 'Flue Gas Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cloud fa-fw',
        'version': '',
    }
    unit = "Mt"

    POSSIBLE_FLUE_GAS_TECHNOS = {f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}': CoalGenDiscipline.FLUE_GAS_RATIO,
                                 #f'{GlossaryEnergy.electricity}.{GlossaryEnergy.GasTurbine}': GasTurbineDiscipline.FLUE_GAS_RATIO,
                                 #f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CombinedCycleGasTurbine}': CombinedCycleGasTurbineDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}': WaterGasShiftDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}.{GlossaryEnergy.FischerTropsch}': FischerTropschDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}.{GlossaryEnergy.Refinery}': RefineryDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.methane}.{GlossaryEnergy.FossilGas}': FossilGasDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.solid_fuel}.{GlossaryEnergy.Pelletizing}': PelletizingDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.syngas}.{GlossaryEnergy.CoalGasification}': CoalGasificationDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.syngas}.{GlossaryEnergy.Pyrolysis}': PyrolysisDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.fossil}.{GlossaryEnergy.FossilSimpleTechno}': FossilSimpleTechnoDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}': AmineScrubbingDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.CalciumPotassiumScrubbing}': CalciumPotassiumScrubbingDiscipline.FLUE_GAS_RATIO,
                                 f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}': DirectAirCaptureTechnoDiscipline.FLUE_GAS_RATIO
                                 }

    DESC_IN = {GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': list(POSSIBLE_FLUE_GAS_TECHNOS.keys()),
                                            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_flue_gas',
                                            'structuring': True, 'unit': '-'},
               }

    stream_name = FlueGas.name

    DESC_OUT = {GlossaryEnergy.FlueGasMean: {'type': 'dataframe',
                                             'visibility': SoSWrapp.SHARED_VISIBILITY,
                                             'namespace': 'ns_flue_gas', 'unit': '%',
                                             AutodifferentiedDisc.GRADIENTS: True},
                GlossaryEnergy.StreamProductionValue: {'type': 'dataframe',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': 'ns_flue_gas', 'unit': 'Mt', AutodifferentiedDisc.GRADIENTS: True},
                GlossaryEnergy.StreamProductionDetailedValue: {'type': 'dataframe',
                                                       'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                       'namespace': 'ns_flue_gas', 'unit': 'Mt'},
                'techno_mix': {'type': 'dataframe',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': 'ns_flue_gas', 'unit': '%'}}

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        super().init_execution()
        self.model = FlueGas(self.stream_name)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}

        if GlossaryEnergy.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

            if techno_list is not None:
                for techno in techno_list:
                    # check if techno not in ccs_list, namespace is
                    # ns_energy_mix
                    ns_variable = GlossaryEnergy.NS_ENERGY_MIX


                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': ns_variable,
                        AutodifferentiedDisc.GRADIENTS: True,
                        'dataframe_descriptor': {
                            GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": ('float', None, False),
                            }
                    }

                    # dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoCapitalDfValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoCapitalDf)
                    dynamic_inputs[f'{techno}.flue_gas_co2_ratio'] = {'type': 'array',
                                                                      'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                      AutodifferentiedDisc.GRADIENTS: True,
                                                                      'namespace': ns_variable, 'unit': '',
                                                                      'default': self.POSSIBLE_FLUE_GAS_TECHNOS[techno]}

        self.add_inputs(dynamic_inputs)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Average CO2 concentration in Flue gases',
                      'Technologies CO2 concentration',
                      'Flue gas production']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'Flue gas production' in charts:
            new_chart = self.get_flue_gas_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Average CO2 concentration in Flue gases' in charts:
            new_chart = self.get_chart_average_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Technologies CO2 concentration' in charts:
            new_chart = self.get_table_technology_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_flue_gas_production(self):
        flue_gas_total = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionValue)[f'{self.stream_name} ({self.unit})']
        flue_gas_total_prod_breakdown_df = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionDetailedValue)
        years = flue_gas_total_prod_breakdown_df[GlossaryEnergy.Years]
        chart_name = 'Flue gas emissions by technology'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, f'Flue gas emissions [{self.unit}]', chart_name=chart_name, stacked_bar=True)

        for techno in self.get_sosdisc_inputs(GlossaryEnergy.techno_list):
            flue_gas_prod_by_techno = flue_gas_total_prod_breakdown_df[f"{techno} ({self.unit})"]
            serie = InstanciatedSeries(years, flue_gas_prod_by_techno, techno, 'bar')
            new_chart.series.append(serie)

        serie = InstanciatedSeries(years, flue_gas_total, 'Total', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_average_co2_concentration(self):
        flue_gas_co2_concentration = self.get_sosdisc_outputs(GlossaryEnergy.FlueGasMean)

        chart_name = 'Average CO2 concentration in Flue gases'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 concentration [%]', chart_name=chart_name)

        serie = InstanciatedSeries(
            flue_gas_co2_concentration[GlossaryEnergy.Years],
            flue_gas_co2_concentration[GlossaryEnergy.FlueGasMean] * 100., 'CO2 concentration', 'lines')

        new_chart.series.append(serie)
        return new_chart

    def get_table_technology_co2_concentration(self):
        table_name = 'Concentration of CO2 in all flue gas streams'
        technologies_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        headers = ['Technology', 'CO2 concentration']
        cells = []
        cells.append(technologies_list)

        col_data = []
        for techno in technologies_list:
            val_co2 = round(self.get_sosdisc_inputs(
                f'{techno}.flue_gas_co2_ratio')[0] * 100, 2)
            col_data.append([f'{val_co2} %'])
        cells.append(col_data)

        new_table = InstanciatedTable(table_name, headers, cells)

        return new_table
