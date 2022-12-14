# EnergyModels


## Description
EnergyModels is the Python package containing few models for energy production technologies, carbon capture, usage and storage (CCUS) technologies, and the processes to combine them into a single energy mix.

## Prerequisite
In order to satisfy dependencies, following prerequisites need to be satisfied:
* deployment of sos\_trade\_core\_package and its requirements (see requirements.txt of sos\_trade\_core\_package package)
* libraries in requirements.txt

The following command can be used to install the package listed in requirements.txt
$$pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org$$


## Overview

This package contains the following main disciplines categories:
* 60 technologies, models the various technologies for energy production or CCUS. (e.g. electrolysis, coal_generation, nuclear, ...)
* 22 streams, models the types of streams coming out of the technologies. (e.g. electricity, gaseous_hydrogen, ...)
* investment, to dispatch the investment into the technologies.
* energy_mix, model to combine the streams together. (this is used to make the interface with the climate economic models in WITNESS)

For more information, please look at the documentation associated.

The technologies are in the models folder. Most of the technology models logic is generic and is thus implemented in the 
mother classes *techno type* and *techno disc*.
The streams are in the core/stream_type folder. They similarly rely on mother class.

Associated tests are in tests folder.
l0 tests are unitary tests. They are used for stand alone disciplines and models.
l1 tests are used to test gradient computation of disciplines and usecases.
l2 tests are used to test gradient computation of processes.
To run a test, run test.py file as Python unit-test.
To run all test, use the command *nose2* .


## Contributing

## Communicating with the SoSTrades team

## Looking at the future

### Implementing new models

There are more technolgies that could be implemented in the energy models, either new emerging technologies or fringe technologies that haven't been implemented yet.

### Improve existing models

Each technology can be improved further, for example by updating the data used to parameterized it or by implementing more complex mechanisms.

## License
The witness-energy source code is distributed under the Apache License Version 2.0.
A copy of it can be found in the LICENSE file.

The witness-energy product depends on other software which have various licenses.
The list of dependencies with their licenses is given in the CREDITS.rst file.
