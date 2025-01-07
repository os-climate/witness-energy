from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class heattechno(TechnoType):
    def compute(self):
        super(heattechno, self).compute()
        self.compute_heat_flux()

    def compute_heat_flux(self):
        heat_flux = self.inputs['flux_input_dict']['land_rate'] / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:energy_and_resources_costs']
        self.outputs[f'heat_flux:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'heat_flux:heat_flux'] = heat_flux

    def compute_transport(self):
        # Electricity has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        transport_cost = self.inputs[f'{GlossaryEnergy.TransportCostValue}:transport'] * \
                         self.inputs[f'{GlossaryEnergy.TransportMarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0

        return transport_cost