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

import configparser
import os
import pathlib
from typing import List


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
                    print(f"[{i}] Will Design Solar Arrangement {cellA}x{cellB}")
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

    Notes:
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
    with open(
        f"{file_path}/{row}x{col}_{num_shade if num_shade != 0 else 'No'}_Shading.cir",
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
    """Creates a LTSpiceXVII simulation file

    Takes in several arguments, all required for producing the output as expected. Depending on ``file_type`` provided,
    the program will either short cell(s) by adding a 0 value dc source across the cell terminals, or open cell
    column(s) by removing all cells in a column from file circuit creation.

    Notes:
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


def main(path: str):
    """Given a config file ``data_sets.ini`` develops all requested datasets for run via LTSpiceXVII"""
    config = configparser.ConfigParser()
    config.read(
        pathlib.PurePath(__file__).parent.joinpath(pathlib.PurePath("data_sets.ini"))
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
        print(f"Generating {dataset} for temperatures: {temp_sets}")
        for temp in temp_sets:
            for row, col in file_sets:
                local = pathlib.PurePath(path)
                high, low = map(int, dataset.split("-"))
                filepath = local.joinpath(
                    pathlib.PurePath(f"../Output/{high}-{low}/Temp{temp}/{row}x{col}")
                )
                os.makedirs(
                    local.joinpath(filepath),
                    exist_ok=True,
                )
                with open(
                    pathlib.PurePath(__file__).parent.joinpath(
                        pathlib.PurePath("cell_2.lib")
                    ),
                    "r",
                ) as file_r, open(filepath.joinpath("cell_2.lib"), "w") as f:
                    f.write(file_r.read())  # write out the file to correct pathing
                for num in range(row * col + 1):
                    create_file(filepath, row, col, num, high, low, temp)
                    if num > 0:
                        if num < col:
                            create_special_file(
                                filepath, row, col, high, temp, "open", num
                            )
                        if num <= col:
                            create_special_file(
                                filepath, row, col, high, temp, "short", num
                            )


if __name__ == "__main__":
    main(".")
