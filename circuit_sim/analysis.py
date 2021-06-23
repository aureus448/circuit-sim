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

import os
import pathlib
import re
import subprocess
import time
from queue import Queue
from subprocess import Popen

import ltspice
import pandas as pd

from circuit_sim.circuit_sim import logger


def run_ltspice(commands):
    procs = Queue()
    s = subprocess.STARTUPINFO(
        dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=subprocess.SW_HIDE
    )
    sleep = 0.3
    for i in range(len(commands)):
        procs.put((Popen(commands[i], startupinfo=s), time.time()))
        time.sleep(sleep)
        # Begins checking after at least X seconds has passed
        if not procs.empty() and sleep * i > 8:
            process = procs.get()
            if time.time() - process[1] > 8:
                process[0].terminate()
            else:
                procs.put(
                    process
                )  # not ready-put back in queue (at end) and continue looping
                continue

    while not procs.empty():
        process = procs.get()
        if time.time() - process[1] > 8:
            process[0].terminate()
        else:
            procs.put(process)  # not ready-put back in queue (at end)


def run_simulations(path: pathlib.PurePath, data_name):
    """Queues simulations to be run

    Args:
        name:

    Returns:

    """
    commands = []
    folders_to_check = ["1x10", "2x4", "2x5", "3x3", "4x2", "5x2", "10x1"]
    for dataset in os.scandir(path):
        if dataset.is_dir() and dataset.name in data_name:  # ensure directory not file
            logger.info(f"Running Data Analysis on {dataset.name}")
            for dir in os.scandir(dataset.path):
                if dir.is_dir():  # ensure directory not file
                    logger.info(f"Main Directory: {dataset.name}/{dir.name}")
                    for sub_dir in os.scandir(dir.path):
                        if (
                            sub_dir.is_dir() and sub_dir.name in folders_to_check
                        ):  # ensure directory not file
                            logger.info(
                                f"Sub Directory: {dataset.name}/{dir.name}/{sub_dir.name} [{dataset.name}]"
                            )
                            for file in os.scandir(sub_dir.path):
                                if file.is_file() and file.name.endswith("cir"):
                                    # Do not run again if data is complete already
                                    if not os.path.exists(
                                        file.path.replace(".cir", ".raw")
                                    ):
                                        logger.info(
                                            f"Queueing LTspiceXVII on {file.name} [{dataset.name}]"
                                        )
                                        commands.append(
                                            r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe -Run "
                                            f"{file.path}"
                                        )
                                    else:
                                        logger.debug(
                                            f"Skipping {file.name} - "
                                            f"{file.name.replace('.cir', '.raw')} already exists"
                                        )
    logger.info(
        f"{len(commands)} LTSpiceXVII runs have been queued - Expect a runtime of "
        f"{len(commands) * 0.3 + 8:.2f} seconds ({(len(commands) * 0.3 + 8) // 60:.0f} minutes, "
        f"{(len(commands) * 0.3 + 8) % 60:.2f} seconds)"
    )
    if len(commands) > 0:
        logger.info("Beginning run in 10 seconds...")
        time.sleep(10)
        run_ltspice(commands)


def data_analysis(path: pathlib.PurePath, data_name):
    for dataset in os.scandir(path):
        i = 1  # tracker of how many circuit(s) are run (total to support full set combination)
        if dataset.is_dir() and dataset.name in data_name:  # ensure directory not file
            logger.info(f"Running Data Analysis on {dataset.name}")
            for dir in os.scandir(dataset.path):
                if dir.is_dir():  # ensure directory not file
                    logger.info(f"Main Directory: {dataset.name}/{dir.name}")
                    gigantor = pd.DataFrame()
                    for sub_dir in os.scandir(dir.path):
                        if sub_dir.is_dir():  # ensure directory not file
                            logger.info(
                                f"Generating for: {dataset.name}/{dir.name}/{sub_dir.name} [{dataset.name}]"
                            )
                            for file in os.scandir(
                                sub_dir.path
                            ):  # rescan directory after modifying and creating .raw files
                                if file.is_file() and file.name.endswith("raw"):
                                    logger.debug(
                                        f"Creating Datasheet Output from {file.name}"
                                    )
                                    lt_data = ltspice.Ltspice(file.path)
                                    lt_data.parse()
                                    vbias = lt_data.get_data("vbias")
                                    I_Vbias = lt_data.get_data("I(vbias)")
                                    P_Vbias = vbias * I_Vbias

                                    out = pd.DataFrame()
                                    out["Voltage (V)"] = vbias
                                    out["Current (A)"] = I_Vbias
                                    out["Power (W)"] = P_Vbias

                                    filename = file.name.split(".")[0] + ".txt"
                                    rx = re.compile(r"-?\d+(?:\.\d+)?")
                                    rtemp = re.compile(r"\d+")
                                    contentList = list(map(int, rx.findall(filename)))
                                    cells = (
                                        contentList[2] if len(contentList) > 2 else 0
                                    )
                                    temp = list(map(int, rtemp.findall(dir.name)))[0]
                                    out["Full Voltage"] = dataset.name.split("-")[0]
                                    out["Shade Voltage"] = dataset.name.split("-")[1]
                                    out["Temperature"] = temp
                                    out["File Name"] = filename
                                    out["# Of Cells"] = contentList[0] * contentList[1]
                                    out["Series Cells"] = contentList[0]
                                    out["Parallel Cells"] = contentList[1]
                                    out["Shaded Cells"] = cells
                                    out[
                                        "Shading %"
                                    ] = f"{((cells / (contentList[0] * contentList[1])) * 100):.2f}"
                                    out["Solar Panel ID"] = i
                                    out["IsShade"] = 1 if cells > 0 else 0
                                    gigantor = gigantor.append(out, ignore_index=True)
                                    i += 1  # increment number of solar panels run on
                    os.makedirs(f"Output/Data/{dataset.name}/", exist_ok=True)
                    gigantor.to_csv(
                        f"Output/Data/{dataset.name}/{dataset.name}-{dir.name}.csv",
                        index=False,
                    )
