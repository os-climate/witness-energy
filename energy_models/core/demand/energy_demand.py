'''
Copyright 2022 Airbus SAS

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

import numpy as np
import pandas as pd

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.energy_mix.energy_mix import EnergyMix
from sostrades_core.tools.base_functions.s_curve import s_curve
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat

from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen


class EnergyDemand(object):
    '''
    Compute a constraint to respect energy demand for consumption/transport ....
    In the V0, only elec demand constraint is implemented
    '''
    name = 'Energy_demand'
    elec_prod_column = f"production electricity ({EnergyMix.stream_class_dict['electricity'].unit})"
    # energy_list_transport = [LiquidHydrogen.name,
    #                      LiquidFuel.name, hightemperatureheat.name, mediumtemperatureheat.name, lowtemperatureheat.name,
    #                          BioDiesel.name, Methane.name, BioGas.name , HydrotreatedOilFuel.name]
    energy_list_transport = [LiquidHydrogen.name,
                             LiquidFuel.name,
                             BioDiesel.name, Methane.name, BioGas.name, HydrotreatedOilFuel.name]

    def __init__(self, name):
        '''
        Constructor
        '''
        # -- Inputs attributes set from configure method
        self.name = name
        self.year_start = 2020  # year start
        self.year_end = 2100  # year end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.long_term_elec_machine_efficiency = 0.985
        self.initial_electricity_demand = 0.0
        self.energy_production_detailed = None
        self.demand_elec_constraint = None
        self.elec_demand = None
        self.transport_demand = None
        self.transport_demand_constraint = None
        self.eff_coeff = 0.2
        self.eff_x0 = 2015
        self.eff_y_min = 0.9

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure paramters at the init execution (Does not change during the execution)
        '''
        self.year_start = inputs_dict[GlossaryCore.YearStart]
        self.year_end = inputs_dict[GlossaryCore.YearEnd]
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.delta_years = self.year_end + 1 - self.year_start
        self.long_term_elec_machine_efficiency = inputs_dict['long_term_elec_machine_efficiency']
        self.initial_electricity_demand = inputs_dict['initial_electricity_demand']
        self.electricity_demand_constraint_ref = inputs_dict['electricity_demand_constraint_ref']
        self.transport_demand_constraint_ref = inputs_dict['transport_demand_constraint_ref']
        self.transport_demand_df = inputs_dict[GlossaryCore.TransportDemandValue]
        self.additional_demand_transport = inputs_dict['additional_demand_transport'] / 100.
        self.demand_elec_constraint = pd.DataFrame(
            {GlossaryCore.Years: self.years})
        self.elec_demand = pd.DataFrame(
            {GlossaryCore.Years: self.years})

    def configure_parameters_update(self, inputs_dict):
        '''
        Update parameters at each execution
        '''
        self.energy_production_detailed = inputs_dict[GlossaryCore.EnergyProductionDetailedValue]
        self.population_df = inputs_dict[GlossaryCore.PopulationDfValue]

    def compute(self):
        '''
        Compute the energy demand per mix
        '''

        self.compute_elec_demand_constraint()
        self.compute_transport_demand_constraint()

    def compute_elec_demand_constraint(self):
        '''
        The constraint is the difference between the prod of electricity computed by the energy mix and the actual demand computed in this model 
        '''
        self.elec_demand['elec_demand (TWh)'] = self.compute_elec_demand_with_efficiency(
        )
        self.demand_elec_constraint['elec_demand_constraint'] = (
                                                                        self.energy_production_detailed[
                                                                            self.elec_prod_column].values -
                                                                        self.elec_demand[
                                                                            'elec_demand (TWh)'].values) / self.electricity_demand_constraint_ref

    def compute_elec_demand_with_efficiency(self):
        '''
        The demand is decreasing due to increase of techno efficiency (division)
        and increasing due to increase of population (multiply)
        '''
        init_pop = self.population_df[GlossaryCore.PopulationValue].values[0]
        self.improved_efficiency_factor = self.compute_improved_efficiency_factor()
        pop_factor = self.population_df[GlossaryCore.PopulationValue].values / init_pop

        electricity_demand = (1. + self.additional_demand_transport) * self.initial_electricity_demand * \
                             pop_factor / self.improved_efficiency_factor

        return electricity_demand

    def compute_improved_efficiency_factor(self):
        '''
        Compute the effect of efficiency improvement based on a S-curve 
        Electrical machine efficiency started at y_min =0.7
        and long term efficiency is planned to be 0.985
        coeff and x0 have been tuned to fit y[2020]=0.95 and y[2025]=0.98 
        '''

        elec_machine_efficiency = self.electrical_machine_efficiency(
            self.years)

        return elec_machine_efficiency / elec_machine_efficiency[0]

    def electrical_machine_efficiency(self, years):

        return s_curve(
            years, coeff=self.eff_coeff, x0=self.eff_x0, y_min=self.eff_y_min,
            y_max=self.long_term_elec_machine_efficiency)

    def compute_transport_demand_constraint(self):
        '''
        Compute transport demand constraint
        '''

        sum_production_wo_elec = np.zeros(self.delta_years)
        for energy_name in self.energy_list_transport:

            energ_prod_column = f"production {energy_name} ({EnergyMix.stream_class_dict[energy_name].unit})"
            if energ_prod_column in self.energy_production_detailed.columns:
                sum_production_wo_elec = sum_production_wo_elec + self.energy_production_detailed[
                    energ_prod_column].values

        self.net_transport_production = sum_production_wo_elec
        self.transport_demand_constraint = (sum_production_wo_elec - self.transport_demand_df[
            GlossaryCore.TransportDemandValue].values) / self.transport_demand_constraint_ref

    def get_elec_demand_constraint(self):
        '''
        Getter for elec_demand_constraint
        '''
        return self.demand_elec_constraint

    def get_elec_demand(self):
        '''
        Getter for elec_demand_constraint
        '''
        return self.elec_demand

    def get_transport_demand_constraint(self):
        '''
        Getter for transport_demand_constraint
        '''
        return self.transport_demand_constraint

    def compute_delec_demand_constraint_delec_prod(self):
        '''
        Compute the gradient of elec_demand_contraint vs electricity net production
        '''

        return np.identity(self.delta_years) / self.electricity_demand_constraint_ref

    def compute_dtransport_demand_dprod(self):
        '''
        Compute the gradient of transport_demand_contraint vs any energy used for transport net production
        '''
        return np.identity(self.delta_years) / self.transport_demand_constraint_ref

    def compute_delec_demand_constraint_dpop(self):
        '''
        Compute the gradient of elec_demand_contraint vs population
        delec_demand_constraint/dpop = -delecdemand/dpop/ref/dt

        delec_demand/dpop = initial_demand/improved_eff_factor * grad

        grad[0,0] = 0
        grad[i,0] = -pop[i]/pop[0]**2

        elsewhere grad = 1/pop[0]
        '''
        pop0 = self.population_df[GlossaryCore.PopulationValue].values[0]
        grad = np.identity(self.delta_years) / pop0

        grad[:, 0] = -self.population_df[GlossaryCore.PopulationValue].values / pop0 ** 2
        grad[0, 0] = 0.0

        return -grad * (
                    1 + self.additional_demand_transport) * self.initial_electricity_demand / self.improved_efficiency_factor.reshape(
            self.delta_years, 1) / self.electricity_demand_constraint_ref
