
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import LowHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.models.heat.low.electric_boiler.electric_boiler import ElectricBoilerHeat


class LowTemperatureHeatDiscipline(LowHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Electric Boiler Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = 'ElectricBoiler'
    energy_name = LowTemperatureHeat.name

    # Conversions
    pound_to_kg = 0.45359237
    gallon_to_m3 = 0.00378541
    liter_per_gallon = 3.78541178

    # Heat Producer [Online]
    #https://www.google.com/search?q=electric+boiler+maximum+heat+temperature+in+degree+celcius&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEdf5IN3xbJw5uB3tC7-M-5nvtg8TKg%3A1683626939090&ei=uxtaZNOCBYWeseMP6ZuEwAM&ved=0ahUKEwiTzI2N_-f-AhUFT2wGHekNATgQ4dUDCA8&uact=5&oq=electric+boiler+maximum+heat+temperature+in+degree+celcius&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCCEQoAEyBQghEKABMgUIIRCgATIFCCEQoAE6CwgAEIoFEIYDELADOggIIRAWEB4QHToHCCEQoAEQCjoECCEQFUoECEEYAVDPB1izUGDqoQVoAXAAeACAAZ0BiAGUBJIBAzAuNJgBAKABAcgBA8ABAQ&sclient=gws-wiz-serp
    #https://www.google.com/search?q=electric+boiler+lifetime&rlz=1C1UEAD_enIN1000IN1000&oq=electric+boiler+lifetime&aqs=chrome..69i57j0i22i30l4j0i390i650l4.14155j0j7&sourceid=chrome&ie=UTF-8
    lifetime = 45          # years

    construction_delay = 2  # years

    techno_infos_dict_default = {

        'Capex_init': 150,           #https://www.google.com/search?q=capex+of+electric+boiler&rlz=1C1UEAD_enIN1000IN1000&oq=capeHow%20much%20does%20an%20electric%20boiler%20capital%20cost?The%20costs%20of%20an%20electric%20boiler%20installation%20can%20range%20from%20a%C2%A0minimum%20$6,469%20to%20$11,885%C2%A0in%20total%20price.
        'Capex_init_unit': '$/kW',    # $ per kW of electricity
        'Opex_percentage': 1.6,       #https://www.google.com/search?q=+OPEX+%25+of+an+electric+boiler&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEddXq4YjX58191BnDyTZd08c2VWtJw%3A1683713517747&ei=7W1bZJqaLaicseMP_pSKkAQ&ved=0ahUKEwjaxIPRwer-AhUoTmwGHX6KAkIQ4dUDCA8&uact=5&oq=+OPEX+%25+of+an+electric+boiler&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCAAQogQyBQgAEKIEMgUIABCiBDIFCAAQogQ6BQghEKABSgQIQRgAUABYxSdggjFoAHAAeACAAZYBiAGuA5IBAzIuMpgBAKABAcABAQ&sclient=gws-wiz-serp
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 1,            # consumptions and productions already have efficiency included
        'elec_demand': 10,          #https://billswiz.com/electric-boiler-electricity-use
        'elec_demand_unit': 'kWh/h',
        'water_demand': 1.13,         #https://www.google.com/search?q=water+required+in+electric+boiler&rlz=1C1UEAD_enIN1000IN1000&oq=water+required+in+electric+boiler+&aqs=chrome..69i57j33i160j33i22i29i30.14095j0j7&sourceid=chrome&ie=UTF-8
        'water_demand_unit': 'm3/h',  #https://www.xconvert.com/unit-converter/gallons-per-minute-to-cubic-meters-per-hour
        'learning_rate': 0.56,
        'full_load_hours': 8760.0,
        'WACC': 0.062,
        'techno_evo_eff': 'no',
    }

    # production in 2019: 29330 million gallons
    # in TWh
    initial_production = 29330

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
               3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0,
               2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
               1.0, 1.0, 1.0, 1.0,
               ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    # Renewable Methane Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': 1.95 * liter_per_gallon * np.array([0, 29.330 - 28.630])})

    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(LowHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = LowHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectricBoilerHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
