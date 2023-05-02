
from abc import abstractmethod

from energy_models.core.stream_type.energy_models.heat import HighTemperatureHeat
from energy_models.core.stream_type.energy_models.heat import MediumTemperatureHeat
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.techno_type import TechnoType


class HighHeatTechno(TechnoType):

    energy_name = HighTemperatureHeat.name



    #def compute_transport(self):
        # Heat has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        # transport_cost = self.transport_cost['transport'] * \
        #     self.transport_margin['margin'] / 100.0
        #
        # return transport_cost

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''
    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0


class MediumHeatTechno(TechnoType):

    energy_name = MediumTemperatureHeat.name



    #def compute_transport(self):
        # Heat has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        # transport_cost = self.transport_cost['transport'] * \
        #     self.transport_margin['margin'] / 100.0
        #
        # return transport_cost

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''
    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0


class LowHeatTechno(TechnoType):

    energy_name = LowTemperatureHeat.name



    #def compute_transport(self):
        # Heat has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        # transport_cost = self.transport_cost['transport'] * \
        #     self.transport_margin['margin'] / 100.0
        #
        # return transport_cost

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''
    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0
