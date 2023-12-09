#!/bin/bash

# Set the virtual environment path
venv_path="/home/raspberrypi/projects/metarmap/venv"

# Activate the virtual environment
source "$venv_path/bin/activate"

# Change to the project directory
cd /home/raspberrypi/projects/metarmap

# Run the Python module
/usr/bin/sudo venv/bin/python -m samples.rpi_example


