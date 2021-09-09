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
"""
Analysis functions for LTspiceXVII simulation running and analysis

Functions within this file are used to simulate the files using ``LTspiceXVII.exe``.
It is expected that LTspiceXVII is installed normally and not in a different directory
from a normal installation, otherwise this script will not work.
"""
import logging
import os
import pathlib

# import re
import subprocess
import time
from queue import Queue
from subprocess import Popen
from typing import List

import ltspice
import pandas as pd


def run_ltspice(commands: List[str]) -> None:
    """Runs LTspiceXVII based on a list of commands provided

    Warning:
        No warranty is expressed or implied. This function directly accesses the os shell,
        and therefore will run anything sent in the list regardless of expected privilege.
        There is no raise for privileges, so is executed on a user-level (non-sudo) only.

    Args:
        commands (list of strings): Shell-executable commands to run

            This function should be run only through run_simulations, but can be run
            outside of run_simulations if that is desired for testing purposes or forced
            shell command execution.
    """
    procs: Queue = Queue()
    s = subprocess.STARTUPINFO(
        dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=subprocess.SW_HIDE
    )
    sleep = 0.1
    for i in range(len(commands)):
        procs.put((Popen(commands[i], startupinfo=s), time.time()))
        time.sleep(sleep)
        # # Begins checking after at least X seconds has passed
        # if not procs.empty() and sleep * i > 8:
        #     process = procs.get()
        #     if time.time() - process[1] > 8:
        #         process[0].terminate()
        #     else:
        #         procs.put(
        #             process
        #         )  # not ready-put back in queue (at end) and continue looping
        #         continue

    # while not procs.empty():
    #     process = procs.get()
    #     if time.time() - process[1] > 8:
    #         process[0].terminate()
    #     else:
    #         procs.put(process)  # not ready-put back in queue (at end)


def run_simulations(path: pathlib.PurePath, data_name: List[str]) -> None:
    """Queues simulations to be run based off of a given path

    The path is expected to contain several simulation files ``*.cir`` and is best run
    on files created by its sister function ``create_files``.

    Args:
        path (OS Path-like object): Directory path to simulation files
        data_name (list of strings): List of directory names containing simulation data to check

            The format of directory paths expected is similar to what is created by function
            ``create_files``.
    """
    commands = []
    folders_to_check = ["1x10", "2x4", "2x5", "1x9", "3x3", "9x1", "4x2", "5x2", "10x1"]
    for dataset in os.scandir(path):
        if dataset.is_dir() and dataset.name in data_name:  # ensure directory not file
            logging.info(f"Running Run Check on {dataset.name}")
            for dir in os.scandir(dataset.path):
                if dir.is_dir():  # ensure directory not file
                    logging.debug(f"Main Directory: {dataset.name}/{dir.name}")
                    for sub_dir in os.scandir(dir.path):
                        if (
                            sub_dir.is_dir() and sub_dir.name in folders_to_check
                        ):  # ensure directory not file
                            logging.debug(
                                f"Sub Directory: {dataset.name}/{dir.name}/{sub_dir.name} [{dataset.name}]"
                            )
                            for file in os.scandir(sub_dir.path):
                                if file.is_file() and file.name.endswith("cir"):
                                    # Do not run again if data is complete already
                                    if not os.path.exists(
                                        file.path.replace(".cir", ".raw")
                                    ):
                                        logging.info(
                                            f"Queueing LTspiceXVII on {file.name} [{dataset.name}]"
                                        )
                                        commands.append(
                                            r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe -b -Run "
                                            f"{file.path}"
                                        )
                                    else:
                                        logging.debug(
                                            f"Skipping {file.name} - "
                                            f"{file.name.replace('.cir', '.raw')} already exists"
                                        )
    logging.info(
        f"{len(commands)} LTSpiceXVII runs have been queued - Expect a runtime of "
        f"{len(commands) * 0.1:.2f} seconds ({(len(commands) * 0.1) // 60:.0f} minutes, "
        f"{(len(commands) * 0.1) % 60:.2f} seconds)"
    )
    if len(commands) > 0:
        # logging.info("Beginning run in 10 seconds...")
        # time.sleep(10)
        start = time.perf_counter()
        run_ltspice(commands)
        logging.info(f"Done in {time.perf_counter() - start:.2f}s")


def data_analysis(path: pathlib.PurePath, data_name) -> None:
    """Performs data analysis of LTspiceXVII simulation results

    Expects ``*.raw`` files produced by running of LTspiceXVII either manually
    or through sister function ``run_simulations``.

    Note:
        All analysis files are produced in a folder ``Output/`` within the respective folder structure
        of the input files. At the end of all folder analysis, a final file called ``mothership.csv``
        is produced containing all data of the previous files.

    Args:
        path (OS Path-like object): Directory path to simulation results
        data_name (list of strings): List of directory names containing simulation data to check

            The format of directory paths expected is similar to what is created by function
            ``create_files``.
    """
    cell_identifier = 1  # tracker of how many circuit(s) are run (total to support full set combination)
    dataframe_list = []
    dataframe_list_special = []
    name_list = []
    bad_data = False
    for dataset in os.scandir(path):
        if dataset.is_dir() and dataset.name in data_name:
            # used for each file later
            full, shade = map(int, dataset.name.split("-"))

            logging.info(f"Running Data Analysis on {dataset.name}")
            temp_list = []
            temp_list_special = []
            for directory in os.scandir(dataset.path):
                if directory.is_dir():
                    # used for each file later
                    temperature = int(directory.name.split("Temp")[-1])

                    logging.debug(f"Main Directory: {dataset.name}/{directory.name}")
                    start = time.perf_counter()
                    logging.info(
                        f"Generating data analysis for: {dataset.name} [{directory.name}]"
                    )
                    gigantor = []  # normal
                    specialdf = []  # special
                    # check for special as that is last file created for each set
                    # if os.path.exists(
                    #     f"Output/Data/{dataset.name}-{directory.name}-Special.csv"
                    # ):
                    #     logging.debug(
                    #         f"Data for set {dataset.name}-{directory.name} already exists"
                    #     )
                    #     continue  # skip already done sets
                    for sub_dir in os.scandir(directory.path):
                        if sub_dir.is_dir():
                            # Variables used for each file
                            series, parallel = map(int, sub_dir.name.split("x"))
                            cell_num = series * parallel

                            logging.debug(
                                f"Generating for: {dataset.name}/{directory.name}/{sub_dir.name} [{dataset.name}]"
                            )
                            for file in os.scandir(
                                sub_dir.path
                            ):  # rescan directory after modifying and creating .raw files
                                if file.is_file() and file.name.endswith("raw"):
                                    # start_file = time.perf_counter()
                                    special = False
                                    special_num = 0
                                    if "Shading" not in file.name:
                                        special = True
                                        special_num = int(file.name.split("_")[1])

                                    logging.debug(
                                        f"Creating Datasheet Output from {file.name}"
                                    )

                                    # err = False
                                    try:
                                        lt_data = ltspice.Ltspice(file.path)
                                        lt_data.parse()
                                    except (
                                        ltspice.FileSizeNotMatchException,
                                        IndexError,
                                    ):  # Both are corrupted file
                                        logging.error(
                                            f"File {file.name} needs to be re-simulated "
                                            f"- Re-run simulation code"
                                        )
                                        os.remove(file.path)
                                        bad_data = True  # don't create final report and warn user
                                        continue

                                    # logging.info(
                                    #     f'File load took {(time.perf_counter() - start_file) * 1000:.2f} milliseconds'
                                    # )
                                    # start_file = time.perf_counter()
                                    vbias = lt_data.get_data("vbias")

                                    # Totals for full array combined (Thevenins)
                                    I_Vbias = lt_data.get_data("I(vbias)")
                                    P_Vbias = vbias * I_Vbias

                                    # Cell-level data
                                    # [_ for _ in lt_data.getVariableNames() if 'Virrad' in _]
                                    # Individual current for each cell?
                                    # This current matches Ivbias [_ for _ in lt_data.getVariableNames() if ':300' in _]

                                    type = (
                                        "Open"
                                        if "Open" in file.name
                                        else "Short"
                                        if special
                                        else "Shaded"
                                    )
                                    frame = {
                                        "Voltage (V)": vbias.round(2),
                                        "Current (A)": I_Vbias.round(2),
                                        "Power (W)": P_Vbias.round(2),
                                        "Full Voltage": full,
                                        "Shade Voltage": shade,
                                        "Temperature": temperature,
                                        "File Name": file.name.split(".")[0],
                                        "# Of Cells": cell_num,
                                        "Series Cells": series,
                                        "Parallel Cells": parallel,
                                        "Type": type,
                                        "Solar Panel ID": cell_identifier,
                                    }

                                    # Per-cell data collection
                                    for i in range(parallel):
                                        # print(f'Parallel: {i+1}')
                                        # For each column we write to the file each cell
                                        for j in range(1, series + 1):
                                            # print(f'\tSeries: {j}')
                                            cell_n = (
                                                i * series + j
                                            )  # current cell out of all cells
                                            if (
                                                type == "Open"
                                                and (i + 1) > parallel - special_num
                                            ):
                                                frame[
                                                    f"Cell {cell_n} Power"
                                                ] = 0.00  # open cell = 0 power
                                                continue
                                            # short has no issues - only open
                                            # elif type =='Short' and cell_n > (parallel*series-special_num):
                                            #     frame[f'Cell {cell_n} Power'] = 0.00 # short cell = 0 power
                                            #     continue

                                            # collection of current data logic
                                            cell_a = f"{i}{j}"
                                            cell_b = f"{i}{j + 1}"

                                            # collection of voltage data logic
                                            volt_a = f"{cell_a if j != 1 else '01'}"
                                            volt_b = (
                                                f"{i}{j + 1}" if cell_n < series else ""
                                            )

                                            # format for grab from ltspice library
                                            prim = f"V({volt_a})"  # guarantees proper zfill
                                            sec = (
                                                f"V({volt_b})"
                                                if cell_n < series
                                                else ""
                                            )
                                            cell = f"Ix(cell_{cell_a}_{cell_b}:300)"  # 300 is correct port for diode
                                            # print(prim, sec)
                                            if sec:
                                                # print(f'\t\tCell {j}: = {prim}-{sec}'
                                                #       f'*{cell}')
                                                v_in = lt_data.get_data(f"{prim}")
                                                v_out = lt_data.get_data(f"{sec}")
                                                cell_data = lt_data.get_data(f"{cell}")
                                                result = (v_in - v_out) * cell_data
                                                # print('done')
                                            else:
                                                # print(
                                                #     f'\t\tCell {j}: = {prim}'
                                                #     f'*{cell}'
                                                # )
                                                v_in = lt_data.get_data(f"{prim}")
                                                cell_data = lt_data.get_data(f"{cell}")
                                                result = (
                                                    v_in * cell_data
                                                )  # vout is ground - not needed in equation

                                            # frame[f'Cell {cell_n} Current'] = cell_data.round(2) - equivalent to Ith
                                            frame[
                                                f"Cell {cell_n} Power"
                                            ] = result.round(2)

                                    out = pd.DataFrame(data=frame)

                                    # logging.info(
                                    #     f'File derivation took '
                                    #     f'{(time.perf_counter() - start_file) * 1000:.2f} milliseconds'
                                    # )
                                    # start_file = time.perf_counter()
                                    if special:
                                        specialdf.append(out)
                                    else:
                                        gigantor.append(out)
                                    # logging.info(f'File took '
                                    #              f'{(time.perf_counter()-start_file)*1000:.2f} milliseconds')
                                    # increment number of solar panels run on
                                    cell_identifier += 1
                    os.makedirs(f"Output/Data/{dataset.name}/", exist_ok=True)

                    logging.debug(f"Creating file {dataset.name}-{directory.name}.csv")

                    # defined as lists
                    gigantor = pd.concat(gigantor, ignore_index=True)
                    specialdf = pd.concat(specialdf, ignore_index=True)
                    # For some unknown reason pandas removes rounding
                    # (OOM? Read from original np array?)
                    # .round(2) returns this rounding
                    pd.concat([gigantor, specialdf], ignore_index=True).round(2).to_csv(
                        f"Output/Data/{dataset.name}/{dataset.name}-{directory.name}.csv",
                        index=False,
                    )
                    logging.debug(f"Took {time.perf_counter() - start:.2f} seconds")
                    # gigantor.to_csv(
                    #     f"Output/Data/{dataset.name}/{dataset.name}-{directory.name}-Shaded.csv",
                    #     index=False,
                    # )
                    # specialdf.to_csv(
                    #     f"Output/Data/{dataset.name}/{dataset.name}-{directory.name}-Special.csv",
                    #     index=False,
                    # )
                    temp_list.append(gigantor)
                    temp_list_special.append(specialdf)

            if len(temp_list) > 0:
                logging.info(f"Creating set dataframe for: {dataset.name}")
                start_create = time.perf_counter()
                mega_set = pd.concat(temp_list, ignore_index=True, copy=True)
                mega_set.round(2).to_csv(
                    f"Output/Data/{dataset.name}-Shading.csv", index=False
                )
                mega_set_special = pd.concat(
                    temp_list_special, ignore_index=True, copy=True
                )
                mega_set_special.round(2).to_csv(
                    f"Output/Data/{dataset.name}-Special.csv", index=False
                )
                dataframe_list.append(mega_set)
                dataframe_list_special.append(mega_set_special)
                name_list.append(f"{dataset.name}")
                # Create subset xlsx - takes way too long I gave up
                # wb = Workbook()
                # data_norm = [mega_set.columns.to_list()] + mega_set.values.tolist()
                # data_spec = [mega_set_special.columns.to_list()] + mega_set_special.values.tolist()
                # ws = wb.new_sheet(f"{dataset.name}-Shading", data=data_norm)
                # ws = wb.new_sheet(f"{dataset.name}-Special", data=data_spec)
                # wb.save(f"Output/Data/{dataset.name}.xlsx")
                # with pd.ExcelWriter(f"Output/Data/{dataset.name}.xlsx") as writer:
                #     mega_set.to_excel(writer, sheet_name=f"{dataset.name}-Shading")
                #     mega_set_special.to_excel(
                #         writer, sheet_name=f"{dataset.name}-Special"
                #     )
                logging.info(
                    f"Dataset output took {time.perf_counter() - start_create:.2f} seconds"
                )
            elif os.path.exists(f"Output/Data/{dataset.name}-Special.csv"):
                mega_set = pd.read_csv(f"Output/Data/{dataset.name}-Shading.csv")
                mega_set_special = pd.read_csv(
                    f"Output/Data/{dataset.name}-Special.csv"
                )
                dataframe_list.append(mega_set)
                dataframe_list_special.append(mega_set_special)
                name_list.append(f"{dataset.name}")
            else:
                logging.error("Dataset missing! Something is wrong!")
                bad_data = True

    if bad_data:
        logging.error(
            "Issues were encountered while collecting simulation data - No final report will be generated. "
            "Please re-run the tool to re-simulate the error data."
        )
        return
    logging.info("Creating complete dataframes - this will take a bit")
    # Concatenate everything
    mega_set = pd.concat(dataframe_list, ignore_index=True, copy=False)
    mega_set.round(2).to_csv("Output/all_cell_data_shading.csv", index=False)
    mega_set_special = pd.concat(dataframe_list_special, ignore_index=True, copy=False)
    mega_set_special.round(2).to_csv("Output/all_cell_data_special.csv", index=False)
    pd.concat([mega_set, mega_set_special], ignore_index=True, copy=False).round(
        2
    ).to_csv("Output/all_cell_data_combined.csv", index=False)
    # print(name_list)
    # print(dataframe_list)
    # with pd.ExcelWriter("Output/all_cell_data.xlsx") as writer: - takes wayyyyyy to long I give up
    #     for i in range(len(dataframe_list)):
    #         print("Running on", name_list[i])
    #         dataframe_list[i].to_excel(writer, sheet_name=f"{name_list[i]}-Shading")
    #         dataframe_list_special[i].to_excel(
    #             writer, sheet_name=f"{name_list[i]}-Special"
    #         )
    logging.info("Dataframe finished - Analysis complete")
