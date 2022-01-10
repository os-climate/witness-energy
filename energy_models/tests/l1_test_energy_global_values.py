'''
mode: python; py-indent-offset: 4; tab-width: 4; coding: utf-8
Copyright (C) 2020 Airbus SAS
'''
import unittest

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import Study as Study_open


class TestGlobalEnergyValues(unittest.TestCase):
    """
    This test class has the objective to test order of magnitude of some key values in energy models in 2020
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.dirs_to_del = []
        self.namespace = 'MyCase'
        self.study_name = f'{self.namespace}'
        self.name = 'Test'
        self.energymixname = 'EnergyMix'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')
        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_open(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

    def test_01_check_global_production_values(self):
        '''
        Test order of magnitude of energy production with values from ourworldindata
        https://ourworldindata.org/energy-mix?country=

        '''
        self.ee.execute()

        # These emissions are in Gt
        energy_production = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.energy_production_brut_detailed')

        '''
        Theory in 2019 from ourwolrdindata  expressed in TWh (2020 is a covid year)
        '''
        oil_production = 53620.
        wind_production = 1590.19  # in 2020
        nuclear_production = 2616.61
        hydropower_production = 4355.
        trad_biomass_production = 11111.
        other_renew_production = 1614.
        modern_biofuels_production = 1043.  # in 2020
        # in 2020
        # https://ourworldindata.org/renewable-energy#solar-energy-generation
        solar_production = 844.37
        coal_production = 43752.
        gas_production = 39893.
        total_production = 166824.

        '''
        Oil production
        '''

        computed_oil_production = energy_production['production liquid_fuel (TWh)'].loc[
            energy_production['years'] == 2020].values[0]

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_oil_production,
                             oil_production * 1.1)
        self.assertGreaterEqual(
            computed_oil_production, oil_production * 0.9)

        '''
        Gas production
        '''
        fossil_gas_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.methane.FossilGas.techno_production')
        computed_gas_production = fossil_gas_prod['methane (TWh)'].loc[
            fossil_gas_prod['years'] == 2020].values[0] * 1000.0

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_gas_production,
                             gas_production * 1.1)
        self.assertGreaterEqual(
            computed_gas_production, gas_production * 0.9)

        '''
        Coal production
        '''
        coal_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.solid_fuel.CoalExtraction.techno_production')
        computed_coal_production = coal_prod['solid_fuel (TWh)'].loc[
            coal_prod['years'] == 2020].values[0] * 1000.0

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_coal_production,
                             coal_production * 1.1)
        self.assertGreaterEqual(
            computed_coal_production, coal_production * 0.9)

        '''
        Biomass production , the value is traditional biomass consumption , but we know that we do not consume all the biomass that we can produce 
        Waiting for a specific value to compare
        '''
#
#         computed_biomass_production = energy_production['production biomass_dry (TWh)'].loc[
#             energy_production['years'] == 2020].values[0]
#
#         # we compare in TWh and must be near 10% of error
#         self.assertLessEqual(computed_biomass_production,
#                              trad_biomass_production * 1.1)
#         self.assertGreaterEqual(
#             computed_biomass_production, trad_biomass_production * 0.9)

        '''
        Biofuel production
        '''

        computed_biodiesel_production = energy_production['production biodiesel (TWh)'].loc[
            energy_production['years'] == 2020].values[0]

        computed_biogas_production = energy_production['production biogas (TWh)'].loc[
            energy_production['years'] == 2020].values[0]

        computed_biofuel_production = computed_biodiesel_production + \
            computed_biogas_production
        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_biofuel_production,
                             modern_biofuels_production * 1.1)
        # we compare in TWh and must be near 30% of error because some biofuels
        # are missing
        self.assertGreaterEqual(
            computed_biofuel_production, modern_biofuels_production * 0.7)

        '''
        Solar production
        '''
        elec_solar_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.SolarPv.techno_production')

        elec_solarth_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.SolarThermal.techno_production')

        computed_solar_production = elec_solar_prod['electricity (TWh)'].loc[
            elec_solar_prod['years'] == 2020].values[0] * 1000.0 + \
            elec_solarth_prod['electricity (TWh)'].loc[
            elec_solarth_prod['years'] == 2020].values[0] * 1000.0

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_solar_production,
                             solar_production * 1.1)
        self.assertGreaterEqual(
            computed_solar_production, solar_production * 0.9)

        '''
        Wind production
        '''
        elec_windonshore_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.WindOnshore.techno_production')
        elec_windoffshore_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.WindOffshore.techno_production')

        computed_wind_production = elec_windonshore_prod['electricity (TWh)'].loc[
            elec_windonshore_prod['years'] == 2020].values[0] * 1000.0 + \
            elec_windoffshore_prod['electricity (TWh)'].loc[
            elec_windoffshore_prod['years'] == 2020].values[0] * 1000.0

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_wind_production,
                             wind_production * 1.1)
        self.assertGreaterEqual(
            computed_wind_production, wind_production * 0.9)

        '''
        Nuclear production
        '''
        elec_nuclear_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.Nuclear.techno_production')

        computed_nuclear_production = elec_nuclear_prod['electricity (TWh)'].loc[
            elec_nuclear_prod['years'] == 2020].values[0] * 1000.0

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_nuclear_production,
                             nuclear_production * 1.1)
        self.assertGreaterEqual(
            computed_nuclear_production, nuclear_production * 0.9)

        '''
        Hydropower production
        '''
        elec_hydropower_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.Hydropower.techno_production')

        computed_hydropower_production = elec_hydropower_prod['electricity (TWh)'].loc[
            elec_hydropower_prod['years'] == 2020].values[0] * 1000

        # we compare in TWh and must be near 10% of error
        self.assertLessEqual(computed_hydropower_production,
                             hydropower_production * 1.1)
        self.assertGreaterEqual(
            computed_hydropower_production, hydropower_production * 0.9)

    def test_02_check_global_co2_emissions_values(self):
        '''
        Test order of magnitude of co2 emissions with values from ourworldindata
        https://ourworldindata.org/emissions-by-fuel

        '''
        self.ee.execute()

        # These emissions are in Gt
        co2_emissions = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.co2_emissions')
        co2_emissions_by_energy = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.co2_emissions_by_energy')

        '''
        Theory in 2020 from ourwolrdindata  expressed in Mt
        '''
        oil_co2_emissions = 11.07e3  # expressed in Mt
        coal_co2_emissions = 13.97e3  # expressed in Mt
        gas_co2_emissions = 7.4e3  # expressed in Mt
        total_co2_emissions = 34.81e3  # billions tonnes

        '''
        Methane CO2 emissions are emissions from methane energy + gasturbine from electricity
        '''
        elec_gt_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.GasTurbine.techno_detailed_production')
        elec_cgt_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.CombinedCycleGasTurbine.techno_detailed_production')

        computed_methane_co2_emissions = co2_emissions_by_energy['methane'].loc[co2_emissions_by_energy['years'] == 2020].values[0] + \
            elec_gt_prod['CO2 from Flue Gas (Mt)'].loc[elec_gt_prod['years']
                                                       == 2020].values[0] +\
            elec_cgt_prod['CO2 from Flue Gas (Mt)'].loc[elec_gt_prod['years']
                                                        == 2020].values[0]

        # we compare in Mt and must be near 10% of error
        self.assertLessEqual(computed_methane_co2_emissions,
                             gas_co2_emissions * 1.1)
        self.assertGreaterEqual(
            computed_methane_co2_emissions, gas_co2_emissions * 0.9)

        '''
        Coal CO2 emissions are emissions from coal energy + CoalGeneration from electricity
        '''
        elec_coal_prod = self.ee.dm.get_value(
            f'{self.name}.{self.energymixname}.electricity.CoalGen.techno_detailed_production')

        computed_coal_co2_emissions = co2_emissions_by_energy['solid_fuel'].loc[co2_emissions_by_energy['years'] == 2020].values[0] + \
            elec_coal_prod['CO2 from Flue Gas (Mt)'].loc[elec_coal_prod['years']
                                                         == 2020].values[0]
        # we compare in Mt and must be near 10% of error
        self.assertLessEqual(computed_coal_co2_emissions,
                             coal_co2_emissions * 1.1)
        self.assertGreaterEqual(
            computed_coal_co2_emissions, coal_co2_emissions * 0.9)

        '''
        Oil CO2 emissions are emissions from oil energy 
        '''

        computed_oil_co2_emissions = co2_emissions_by_energy['liquid_fuel'].loc[
            co2_emissions_by_energy['years'] == 2020].values[0]
        # we compare in Mt and must be near 10% of error
        self.assertLessEqual(computed_oil_co2_emissions,
                             oil_co2_emissions * 1.1)
        self.assertGreaterEqual(
            computed_oil_co2_emissions, oil_co2_emissions * 0.9)

        '''
        Total CO2 emissions are emissions from oil energy 
        '''

        computed_total_co2_emissions = co2_emissions[
            'Total CO2 emissions'].loc[co2_emissions['years'] == 2020].values[0]
        # we compare in Mt and must be near 10% of error
        self.assertLessEqual(computed_total_co2_emissions,
                             total_co2_emissions * 1.1)
        self.assertGreaterEqual(
            computed_total_co2_emissions, total_co2_emissions * 0.9)


if '__main__' == __name__:
    cls = TestGlobalEnergyValues()
    cls.setUp()
    cls.test_02_check_global_co2_emissions_values()
