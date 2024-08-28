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
from os.path import dirname, join

techno_dict_folder = dirname(__file__)
filename = "techno_dict_2024-07-14 Jul01_24technos_12streams.json"

#filename = "techno_dict_test.json"
def load_dict(filename: str):
    filepath = join(techno_dict_folder, filename)
    with open(filepath, 'r') as json_file:
        loaded_dict = json.load(json_file)
    return loaded_dict

techno_dict_midway = load_dict(filename)
