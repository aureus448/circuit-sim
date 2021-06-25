#  Copyright (c) 2021 Nate Ruppert
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import configparser
import logging
import os
import pathlib

import circuit_sim

if __name__ == "__main__":
    logger = circuit_sim.set_logger(logging.getLogger(), "circuit_sim.log")
    logging.info("Beginning Circuit Simulation [1.0.0]")
    # Creates dataset (skips if dataset complete)
    circuit_sim.create_files(".")
    logging.info("Dataset generation complete - Beginning Simulations")
    # Read in datasets to make
    config = configparser.ConfigParser()
    config.read("data_sets.ini")
    data_name = [key for key in config.keys() if key != "DEFAULT"]
    # Run this script right next to Spice Simulation folder
    path = pathlib.PurePath("Output/")
    print(os.path.abspath(path))
    # Run LTSpiceXVII on all files (if not already generated)
    circuit_sim.run_simulations(path, data_name)
    # Perform data analysis on all files
    circuit_sim.data_analysis(path, data_name)
