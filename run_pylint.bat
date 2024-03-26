@echo off
TITLE Pylint Witness Energy

@echo off
echo running pylint...
pylint --disable=E1101,E1135,E1133,E0203 --errors-only energy_models
pause