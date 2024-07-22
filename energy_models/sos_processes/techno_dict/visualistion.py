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
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

# Define the technologies and their energy connections
technologies = {
    'T1': {'consumes': ['E1'], 'produces': 'E2'},
    'T2': {'consumes': ['E2'], 'produces': 'E1'},
    'T3': {'consumes': ['E1', 'E2'], 'produces': 'E3'},
    'T4': {'consumes': ['E3'], 'produces': 'E4'},
    'T5': {'consumes': ['E4'], 'produces': 'E1'}
}



def generate_color_mapping(strings):
    # Get a list of all available colors
    colors = list(mcolors.CSS4_COLORS.keys())

    # If there are more strings than available colors, raise an error
    if len(strings) > len(colors):
        raise ValueError("Too many strings for the available unique colors.")

    # Shuffle the colors to get a diverse set
    np.random.shuffle(colors)

    # Map each string to a unique color
    color_mapping = {string: colors[i] for i, string in enumerate(strings)}

    cmap = plt.get_cmap('tab20')
    num_colors = cmap.N

    # If there are more strings than available colors, repeat colors
    colors = [cmap(i % num_colors) for i in range(len(strings))]

    # Map each string to a unique color
    color_mapping = {string: mcolors.to_hex(colors[i]) for i, string in enumerate(strings)}

    return color_mapping

def visualize(technologies):
    # Initialize the directed graph
    import re

    import networkx as nx
    def improve_string(ss):
        ss = ss.replace('.','\n').replace('_',' ')
        ss = re.sub(r'(?<!^)(?=[A-Z])', ' ', ss)
        ss = ss.replace('S O E C','SOEC')
        ss = ss.replace(' P E M', 'PEM')
        ss = ss.replace(' A W E', 'AWE')
        ss = ss.replace(' C O', 'CO')
        return ss

    stream_produces = list(set([v["produces"] for v in technologies.values()]))
    color_mapping_nodes = generate_color_mapping(list(stream_produces))
    node_colors = [color_mapping_nodes[tech['produces']] for tech in technologies.values()]
    G = nx.DiGraph()

    # Add nodes for each technology
    for tech in technologies.keys():
        G.add_node(improve_string(tech))

    # Add edges based on energy connections
    edges_colors = []
    for tech, details in technologies.items():
        for consumed_energy in details['consumes']:
            for provider_tech, provider_details in technologies.items():
                if provider_details['produces'] == consumed_energy:
                    G.add_edge(improve_string(provider_tech), improve_string(tech))
                    edges_colors.append(color_mapping_nodes[consumed_energy])

    # Draw the graph
    pos = nx.spring_layout(G, k=600.5, iterations=1500)
    size= 70
    plt.figure(figsize=(size, size))
    # Define edge labels (using consumed energy for this example)
    edge_labels = {(improve_string(provider_tech), improve_string(tech)): improve_string(consumed_energy)
                   for tech, details in technologies.items()
                   for consumed_energy in details['consumes']
                   for provider_tech, provider_details in technologies.items()
                   if provider_details['produces'] == consumed_energy}

    # Draw the edge labels on the graph
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='red', rotate=False)

    nx.draw(G, pos, with_labels=True, node_size=3000, font_size=10, font_weight="bold", arrowsize=20, node_color=node_colors, edge_color=edges_colors)
    #plt.title("Interconnections Between Technologies")
    plt.show()
