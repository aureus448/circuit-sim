#  Copyright (c) 2021 Nate Ruppert
#  This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Main script for circuit_sim allowing for circuit creation, simulation and analysis

Supports the creation of circuit simulation files based upon a provided ``data_sets.ini``
file and is designed for development of a very specific circuit for use in a research project
I am apart of at CSUF.

Please see the provided __main__ function for usage of this program/library, or use ``simulate_module.py``,
another file that directly follows the __main__ function but is designed to use this script and the analysis
script together as a library (circuit_sim).
"""
import configparser
import logging
import os
import pathlib
from typing import List

from circuit_sim.analysis import data_analysis, run_simulations


def set_logger(log: logging.Logger, name: str):
    """Set up of logging program based on a provided logging.Logger

    Args:
        log (logging.Logger): Logger object to add handlers to
        name (str): Output file name

    Returns:

    """
    log.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    fh = logging.FileHandler(name, mode="w")
    sh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%d/%m/%Y | %H:%M:%S"
    )
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(sh)
    return log


def list_types(max_cells: List[int], sets_to_make=None) -> List[List[int]]:
    """Lists possible sets given a max cells limit

    Includes optional support for specifying only a subset of the sets to be made,
    which are supported through pass-through of sets_to_make

    Args:
        max_cells (list): List of integers indicating max cells that are allowed for each cell set
        sets_to_make (list): Semi-Optional list of sets to make that defaults to everything if None

    Returns:
        sets (list): Sets in format of [Row, Column]
    """
    sets: List[List[int]] = []

    for i in max_cells:
        solar_cell = [x for x in range(1, i + 1) if (i % x == 0 and x <= i)]
        for cellA in solar_cell:
            for cellB in solar_cell:
                if cellA == cellB and cellA * cellB != i:
                    continue
                elif cellA * cellB == i:
                    if f"{cellA}x{cellB}" not in sets_to_make and sets_to_make:
                        continue
                    logging.info(f"[{i}] Will Design Solar Arrangement {cellA}x{cellB}")
                    sets.append([cellA, cellB])
    return sets


def create_file(
    file_path: pathlib.PurePath,
    row: int,
    col: int,
    num_shade: int,
    full_volt: int,
    shade_volt: int,
    temp: int,
) -> None:
    """Creates a LTSpiceXVII simulation file

    Takes in several arguments, all required for producing the output as expected.

    Note:
        "Full" and "Shade" intensity refer to whether the cell is considered to be in full view
        of sunlight (Highest possible efficiency) or in the shade (Lower efficiency than Highest but not 0).

    Args:
        file_path (pathlib.PurePath): Location of where the file will be placed
        row (int): Number of cells per column
        col (int): Number of columns per circuit
        num_shade (int): Number of shaded cells in circuit
        full_volt (int): Value (voltage) of "Full" intensity
        shade_volt (int): Value (voltage) of "Shade" intensity
        temp (int): Temperature of circuit
    """
    # Do not duplicate work
    if os.path.exists(f"{file_path}/{row}x{col}_{num_shade}_Shading.cir"):
        logging.debug(
            f"File {row}x{col}_{num_shade}_Shading.cir already exists - Skipping"
        )
        return
    logging.debug(f"Beginning creation of {row}x{col}_{num_shade}_Shading.cir")
    with open(
        f"{file_path}/{row}x{col}_{num_shade}_Shading.cir",
        "w+",
    ) as f:
        # Write of information of how files were made and what they do
        f.write("* Files designed by circuit-sim by Nate Ruppert\n")
        f.write(
            f"* Circuit Simulation of {row} Series x {col} Parallel Solar Cell Arrangement\n"
        )
        f.write(f"* {num_shade} Shade {row * col - num_shade} No-Shade File\n")

        # Required data to simulate the solar cells
        f.write(".include cell_2.lib\n")
        f.write(f".option temp={temp}")
        f.write("\n")  # <br>

        # Adds data for each cell depending on how many cells to add
        for i in range(col):
            f.write(f"\n*** Start of Column {i + 1:02d}\n\n")
            # For each column we write to the file each cell
            for j in range(1, row + 1):
                """
                Example of cell: 2x1 (2 cells in series, 1 cell-block in parallel)

                The logic below would find {start} and {end} which would be ``01``
                and ``02`` for the first cell, ``02`` and ``03`` for the second.

                It also formats the xcell using start and end based on how LTSpiceXVII
                expects the nodes to be named and supplied.
                """
                start = f"{i}{j}"
                end = f"{i}{j + 1}"
                f.write(f"** Cell {j:02d} [Col {i + 1:02d}]\n")
                f.write(
                    f'xcell_{start}_{end} {end if j != row else "0"} {start if j != 1 else "01"} '
                    f"{end}{start} cell_2 params:area=49  j0=16E-20 j02=1.2E-12\n"
                )
                f.write("+ jsc=30.5E-3 rs=28e-3 rsh=100000\n")

                # Determines whether to add a shaded cell or full cell to the file
                if (i + 1) * j <= num_shade:
                    f.write(
                        f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {shade_volt}\n'
                    )
                else:
                    f.write(
                        f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {full_volt}\n'
                    )
                f.write("\n")  # <br>

        # Required final data for files
        f.write("\nvbias 01 0 dc 0\n")  # Add voltage probe
        f.write(".plot dc i(vbias)\n")  # Plot current based on voltage probe
        f.write(
            f".dc vbias 0 {1.05 * row} 0.01\n"
        )  # Indicate voltage probe voltage characteristics
        f.write(".probe\n.end\n")  # End file


def create_special_file(
    file_path: pathlib.PurePath,
    row: int,
    col: int,
    full_volt: int,
    temp: int,
    file_type: str,
    type_num: int,
) -> None:
    """Creates a 'special' LTSpiceXVII simulation file

    Takes in several arguments, all required for producing the output as expected.

    Note:
        "Full" and "Shade" intensity refer to whether the cell is considered to be in full view
        of sunlight (Highest possible efficiency) or in the shade (Lower efficiency than Highest but not 0).

    Warning:
        Logic on amount of file_type (``Short`` or ``Open`` circuit) must be determined programmatically before
        calling of this function. This function will create files that shouldn't exist or are duplicative of
        previous results otherwise.

        Example:
            Providing a 1x10 [``1 Series x 10 parallel``] file any "short"
            file type would short the entire circuit and produce useless results

    Args:
        file_path (pathlib.PurePath): Location of where the file will be placed
        row (int): Number of cells per column
        col (int): Number of columns per circuit
        full_volt (int): Value (voltage) of "Full" intensity
        temp (int): Temperature of circuit
        file_type (str): Type of file being produced - allowed to be one of two values: "open" or "short"
        type_num (int): Amount of the ``file_type`` provided to create
    """
    # Do not duplicate work
    if os.path.exists(
        f"{file_path}/{row}x{col}_{type_num}_{file_type.capitalize()}.cir"
    ):
        logging.debug(
            f"File {row}x{col}_{type_num}_{file_type.capitalize()}.cir already exists - Skipping"
        )
        return
    logging.debug(
        f"Beginning creation of {row}x{col}_{type_num}_{file_type.capitalize()}.cir"
    )
    """Creates a LTSpiceXVII simulation file

    Takes in several arguments, all required for producing the output as expected. Depending on ``file_type`` provided,
    the program will either short cell(s) by adding a 0 value dc source across the cell terminals, or open cell
    column(s) by removing all cells in a column from file circuit creation.

    Note:
        "Full" and "Shade" intensity refer to whether the cell is considered to be in full view
            of sunlight (Highest possible efficiency) or in the shade (Lower efficiency than Highest but not 0).
            "Shade" is not used for special file creation.

    Warnings:
        ``type_num`` is not checked for validity, meaning it is up to the user to use proper logic to determine
            the expected maximum for the value. (For example, supplying 5 short when the circuit supports a max of 3
            shorted devices will not crash the program. Instead, during simulation via LTSpiceXVII, you will notice
            that the circuit is shorted from Vdd to Ground as the program shorted two of the columns to ground directly
            as requested by the user

    Args:
        file_path (pathlib.PurePath): Location of where the file will be placed
        row (int): Number of cells per column
        col (int): Number of columns per circuit
        full_volt (int): Value (voltage) of "Full" intensity
        temp (int): Temperature of circuit
        file_type (str): Type of file to create (Supports either "open" or "short" case-sensitive
        type_num (int): Number of open/short cases to perform
    """
    with open(
        f"{file_path}/{row}x{col}_{type_num}_{file_type.capitalize()}.cir", "w+"
    ) as f:
        f.write("* Files designed by circuit-sim by Nate Ruppert\n")
        f.write(
            f"* Circuit Simulation of {row} Series x {col} Parallel Solar Cell Arrangement\n"
        )
        f.write(
            f"* {type_num} {file_type} {row * col - type_num} No-{file_type} File\n"
        )
        # Required for project
        f.write(".include cell_2.lib\n")
        f.write(f".option temp={temp}")
        f.write("\n")  # <br>

        # Adds data for each cell depending on how many cells to add
        for i in range(col):
            f.write(f"\n*** Start of Column {i + 1:02d}\n\n")

            # For open circuits, we simply skip creating data for a column
            if file_type == "open" and i >= col - type_num:
                f.write("* Column Skipped due to Open Circuit\n")
                continue

            for j in range(1, row + 1):
                start = f"{i}{j}"
                end = f"{i}{j + 1}"
                f.write(f"** Cell {j:02d} [Col {i + 1:02d}]\n")
                f.write(
                    f'xcell_{start}_{end} {end if j != row else "0"} {start if j != 1 else "01"} '
                    f"{end}{start} cell_2 params:area=49  j0=16E-20 j02=1.2E-12\n"
                )
                f.write("+ jsc=30.5E-3 rs=28e-3 rsh=100000\n")

                # Unlike for regular file creation, there is no shade logic
                f.write(
                    f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {full_volt}\n'
                )
                # If designing a short file, shorts the cell connection with a 0 value dc source
                if file_type == "short" and j == row and i + 1 > col - type_num:
                    f.write(f"r_{start}_{end} {start} 0 0.0001\n")
                f.write("\n")  # <br>

        # Required final data for files
        f.write("\nvbias 01 0 dc 0\n")  # Add voltage probe
        f.write(".plot dc i(vbias)\n")  # Plot current based on voltage probe
        f.write(
            f".dc vbias 0 {1.05 * row} 0.01\n"
        )  # Indicate voltage probe voltage characteristics
        f.write(".probe\n.end\n")  # End file


def create_files(path: str = "."):
    """Given a config file ``data_sets.ini`` develops all requested datasets for run via LTSpiceXVII

    Args:
        path (str): Path to output files (Defaults to exactly where command is run)
    """
    config = configparser.ConfigParser()
    config.read(
        pathlib.PurePath(__file__).parent.joinpath(pathlib.PurePath("../data_sets.ini"))
    )

    # Reads config file ``data_sets.ini`` and provides the requested data sets for set creation
    data_sets = [
        [key, config[key]["temps"]] for key in config.keys() if key != "DEFAULT"
    ]
    # Collects the sets that will be performed based on passed parameters
    file_sets = list_types(
        [8, 9, 10], ["1x10", "2x4", "2x5", "3x3", "4x2", "5x2", "10x1"]
    )

    for dataset, temps in data_sets:

        # Collect Temperatures to Run
        if not temps:
            temp_sets = [27, 30, 35, 40, 45, 50]
        else:
            var_sets = temps.split(", ")
            temp_sets = []
            for val in var_sets:
                if "-" in val:
                    lower, upper = val.split("-")
                    results = [x for x in range(int(lower), int(upper) + 1)]
                else:
                    results = [int(val)]
                temp_sets += results

        # Begins set creation
        logging.info(f"Generating dataset {dataset} for temperatures: {temp_sets}")
        for temp in temp_sets:
            for row, col in file_sets:
                local = pathlib.PurePath(path)
                high, low = map(int, dataset.split("-"))
                filepath = local.joinpath(
                    pathlib.PurePath(f"Output/{high}-{low}/Temp{temp}/{row}x{col}")
                )
                os.makedirs(
                    filepath,
                    exist_ok=True,
                )
                with open(
                    pathlib.PurePath(__file__).parent.joinpath(
                        pathlib.PurePath("cell_2.lib")
                    ),
                    "r",
                ) as file_r, open(filepath.joinpath("cell_2.lib"), "w+") as f:
                    f.write(file_r.read())  # write out the file to correct pathing
                for num in range(row * col + 1):
                    create_file(filepath, row, col, num, high, low, temp)
                    if num > 0:
                        # Open tracks: m - 1 where m [col] is cells in parallel
                        if num < col:
                            create_special_file(
                                filepath, row, col, high, temp, "open", num
                            )
                        # Short tracks: m*n-m where m [col] is cells in parallel and n [row] is cells in series
                        if num <= row * col - col:
                            create_special_file(
                                filepath, row, col, high, temp, "short", num
                            )


if __name__ == "__main__":
    logger = set_logger(logging.getLogger(), "circuit_sim.log")
    logging.info("Beginning Circuit Simulation [1.0.0]")
    # Creates dataset (skips if dataset complete)
    create_files("..")
    logging.info("Dataset generation complete - Beginning Simulations")
    # Read in datasets to make
    config = configparser.ConfigParser()
    config.read("data_sets.ini")
    data_name = [key for key in config.keys() if key != "DEFAULT"]
    # Run this script right next to Spice Simulation folder
    path = pathlib.PurePath("Output/")
    # Run LTSpiceXVII on all files (if not already generated)
    run_simulations(path, data_name)
    # Perform data analysis on all files
    data_analysis(path, data_name)
