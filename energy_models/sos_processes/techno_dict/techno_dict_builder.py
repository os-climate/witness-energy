'''
Copyright 2024 Capgemini
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
import json
import os
from datetime import datetime

from energy_models.glossaryenergy import GlossaryEnergy

# Define the energies and technologies
techno_infos = {
    'T1': {'consumes': ['E1'], 'produces': 'E2'},
    'T2': {'consumes': ['E2'], 'produces': 'E1'},
    'T3': {'consumes': ['E3'], 'produces': 'E1'},
}


def techno_dict_builder(techno_infos: dict, initial_selection: list[str],
                        minimal_techno_number: int = 0,
                        minimal_stream_number: int = 0,
                        technos_to_avoid: list[str] = [],
                        streams_to_avoid: list[str] = [],
                        streams_to_have: list[str] = [],
                        max_carbon_storage_technos: int = 10):
    """
    :param techno_infos: expect something like this :

    technologies = {
    'T1': {'consumes': ['E1'], 'produces': 'E2'},
    'T2': {'consumes': ['E2'], 'produces': 'E1'},
    'T3': {'consumes': ['E3'], 'produces': 'E1'},
    }
    :type techno_infos:
    :return:
    :rtype:
    """

    import pulp

    # The initially selected technologies
    energy_to_producing_technos = {}

    # Iterate through the technologies dictionary
    for tech, details in techno_infos.items():
        produced_energy = details['produces']
        if produced_energy not in energy_to_producing_technos:
            energy_to_producing_technos[produced_energy] = []
        energy_to_producing_technos[produced_energy].append(tech)

    # Initialize a set to store unique energy values
    energy_values = set()

    # Iterate through the technologies dictionary
    for tech, details in techno_infos.items():
        # Add consumed energies to the set
        for consumed in details['consumes']:
            energy_values.add(consumed)
        # Add produced energy to the set
        energy_values.add(details['produces'])

    # Convert the set to a list
    all_streams = list(energy_values)
    for stream in all_streams:
        if stream not in energy_to_producing_technos:
            energy_to_producing_technos[stream] = []

    # Print the list of unique energy values

    # Create the problem
    prob = pulp.LpProblem("Minimal_Technology_Selection", pulp.LpMinimize)

    # Define binary decision variables for each technology
    tech_vars = pulp.LpVariable.dicts(name="Tech", indices=techno_infos.keys(), lowBound=0, upBound=1, cat=pulp.LpBinary)

    # Add the initial selection constraints (these technologies must be selected)
    for initially_selected_tech in initial_selection:
        prob.addConstraint(constraint=tech_vars[initially_selected_tech] == 1, name=f"SelectionInitiale{initially_selected_tech}")

    for t in technos_to_avoid:
        prob.addConstraint(constraint=tech_vars[t] == 0, name=f"AvoidedTechno{t}")

    # Ensure that all selected technologies receive the energies they consume
    stream_produced_vars = pulp.LpVariable.dicts(name="NumberOfTechnoProducingStream", indices=all_streams, lowBound=0, upBound=None, cat=pulp.LpInteger)
    M = 10000
    bool_stream_produced_vars = pulp.LpVariable.dicts(name="IsStreamProduced", indices=all_streams, lowBound=0, upBound=1, cat=pulp.LpBinary)

    for s in streams_to_avoid:
        prob.addConstraint(constraint=bool_stream_produced_vars[s] == 0, name=f"AvoidedStreamProduced{s}")
    for s in streams_to_have:
        prob.addConstraint(constraint=bool_stream_produced_vars[s] == 1, name=f"StreamsToHave{s}")

    # For each energy, add constraints to ensure that if it is consumed, it must be produced by some technology
    for tech in tech_vars:
        # Constraint to ensure each energy consumed must be produced
        streams_consumed_by_tech = techno_infos[tech]['consumes']
        for stream in streams_consumed_by_tech:
            prob.addConstraint(stream_produced_vars[stream] >= tech_vars[tech], name=f"{stream}_produced_if_{tech}_selected")

        stream_produced_by_tech = techno_infos[tech]['produces']
        prob.addConstraint(stream_produced_vars[stream_produced_by_tech] >= tech_vars[tech], name=f"stream_{stream_produced_by_tech}_produced_if_{tech}_selected")
    prob.addConstraint(stream_produced_vars[GlossaryEnergy.carbon_storage] <= max_carbon_storage_technos, name="max_selected_carbon_storage_techno")

    if minimal_stream_number:
        if minimal_stream_number > len(all_streams):
            raise ValueError(f"There is a total of {len(all_streams)} streams available, please lower the mininimal_stream_number constraint value")
        for stream in all_streams:
            prob.addConstraint(
                M * bool_stream_produced_vars[stream] >= stream_produced_vars[stream],
                name=f"stream_{stream}_is_produced_1")
            prob.addConstraint(
                bool_stream_produced_vars[stream] <= stream_produced_vars[stream],
                name=f"stream_{stream}_is_produced_2")

            prob += pulp.lpSum([bool_stream_produced_vars[s] for s in all_streams]) >= minimal_stream_number

    for stream in all_streams:
        techno_producing_stream = energy_to_producing_technos[stream]
        name = f"{stream}=" + 'or'.join(techno_producing_stream)
        prob.addConstraint(constraint=pulp.lpSum([tech_vars[t] for t in techno_producing_stream]) == stream_produced_vars[stream],
                           name=name)

    if minimal_techno_number > len(techno_infos):
        raise ValueError(f"There is a total of {len(techno_infos)} technos available, please lower the minimal_techno_number constraint value")
    prob += pulp.lpSum([tech_vars[t] for t in techno_infos]) >= minimal_techno_number

    # Objective: Minimize the number of additional technologies selected
    prob += pulp.lpSum([tech_vars[t] for t in techno_infos])

    # Solve the problem
    prob.solve()

    def show_infos():
        print("Energy to Technologies Dictionary:", energy_to_producing_technos)

        print("\nDecision Variable Values:")
        for tech in techno_infos.keys():
            print(f"{tech}: {pulp.value(tech_vars[tech])}")
        print("")
        for stream in all_streams:
            print(f"{stream}: {pulp.value(stream_produced_vars[stream])}")

        print("\nConstraint Statuses:")
        for name, constraint in prob.constraints.items():
            lhs_value = pulp.value(constraint)
            rhs_value = constraint.constant
            print(f"{name}: LHS = {lhs_value}, RHS = {rhs_value}, Status = {lhs_value == rhs_value}")

    # Print the selected technologies
    selected_technologies = [t for t in techno_infos if pulp.value(tech_vars[t]) == 1]
    selected_streams = [s for s in all_streams if pulp.value(bool_stream_produced_vars[s]) == 1]
    print('=' * 100)
    print('=' * 100)
    print('=' * 100)
    print(f"\n\nInitially Selected Technologies ({len(initial_selection)}):".upper(), initial_selection)
    for selected_techno in initial_selection:
        print(selected_techno, techno_infos[selected_techno])
    added_technos = list(filter(lambda x: x not in initial_selection, selected_technologies))
    print(f"\nAdded Technologies ({len(added_technos)}):".upper(), added_technos)
    for selected_techno in added_technos:
        print(selected_techno, techno_infos[selected_techno])
    print(f"\n\nSelected STREAMS ({len(selected_streams)}):".upper(), selected_streams)
    print('=' * 100)

    n_technos = len(selected_technologies)
    n_streams = len(selected_streams)
    techno_dict_for_witness = {}

    for selected_techno in selected_technologies:
        energy_produced_by_techno = techno_infos[selected_techno]['produces']
        if energy_produced_by_techno not in techno_dict_for_witness:
            techno_dict_for_witness[energy_produced_by_techno] = {GlossaryEnergy.stream_type: GlossaryEnergy.stream_to_type_mapper[energy_produced_by_techno],
                                                                  GlossaryEnergy.value: []}
        techno_dict_for_witness[energy_produced_by_techno][GlossaryEnergy.value].append(selected_techno)

    return techno_dict_for_witness, n_technos, n_streams


# techno_dict_builder(technologies_test)

def build_techno_infos(stream_used_by_technos: dict, stream_produced_by_techno: dict):
    out = {}
    for techno, stream_produced in stream_produced_by_techno.items():
        out[techno] = {"consumes": [],
                       'produces': stream_produced}

    for techno, stream_used in stream_used_by_technos.items():
        if techno not in out:
            pass
        else:
            out[techno]["consumes"] = stream_used

    return out


techno_info_dict = build_techno_infos(GlossaryEnergy.TechnoStreamsUsedDict, GlossaryEnergy.TechnoStreamProducedDict)

inital_selection = [
    GlossaryEnergy.HefaDecarboxylation,
    GlossaryEnergy.FischerTropsch,
    # f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.FlueGasTechno}",
    # f"{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}",
]

technos_to_avoid = [
GlossaryEnergy.BiomassFermentation,
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.MonoEthanolAmine}",  # remove
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.ChilledAmmoniaProcess}",  # remove
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CO2Membranes}",  # remove
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PressureSwingAdsorption}",  # remove
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}",  # remove
f"{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PiperazineProcess}",  # remove
GlossaryEnergy.BiomassBuryingFossilization,
GlossaryEnergy.PureCarbonSolidStorage,
GlossaryEnergy.FossilSimpleTechno,
GlossaryEnergy.CleanEnergySimpleTechno,

GlossaryEnergy.RWGS,
# GlossaryEnergy.FischerTropsch
]
streams_to_avoid = [
GlossaryEnergy.hightemperatureheat_energyname,
GlossaryEnergy.mediumtemperatureheat_energyname,
GlossaryEnergy.lowtemperatureheat_energyname,
GlossaryEnergy.biomass_dry,
# GlossaryEnergy.syngas,
# f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}',
]
streams_to_have = [
    GlossaryEnergy.carbon_captured,
    GlossaryEnergy.carbon_storage,
]


if __name__ == '__main__':
    sub_techno_dict, n_technos, n_streams = techno_dict_builder(
        techno_infos=techno_info_dict,
        initial_selection=inital_selection,
        minimal_stream_number=11,
        minimal_techno_number=30,
        streams_to_avoid=streams_to_avoid,
        streams_to_have=streams_to_have,
        technos_to_avoid=technos_to_avoid,
        max_carbon_storage_technos=3)

    ts = datetime.now().strftime("%Y-%m-%d %h%M")
    curdir = os.path.dirname(__file__)
    filename = os.path.join(curdir, "data", f"techno_dict_{ts}_{n_technos}technos_{n_streams}streams.json")
    filename = os.path.join(curdir, "data", "techno_dict_test.json")
    with open(filename, 'w') as json_file:
        json.dump(sub_techno_dict, json_file, indent=4)
    techno_dict_midway = sub_techno_dict
    from energy_models.sos_processes.energy.MDO.energy_mix_optim_process.usecase_with_utilization_ratio import (
        Study,
    )
    study = Study(run_usecase=True)
    study.load_data()
    study.run()
