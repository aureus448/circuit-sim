import configparser
import os
import pathlib


def list_types():
    max_cells = [8, 9, 10]
    a = []
    sets_to_make = ["1x10", "2x4", "2x5", "3x3", "4x2", "5x2", "10x1"]
    for i in max_cells:
        solar_cell = [x for x in range(1, i + 1) if (i % x == 0 and x <= i)]
        for cellA in solar_cell:
            for cellB in solar_cell:
                if cellA == cellB and cellA * cellB != i:
                    continue
                elif cellA * cellB == i:
                    if f"{cellA}x{cellB}" not in sets_to_make:
                        continue
                    print(f"[{i}] Will Design Solar Arrangement {cellA}x{cellB}")
                    a.append([cellA, cellB])
    return a


def create_file(path, row, col, shade, full_val, shade_val, temp):
    with open(
        f"{path}/{row}x{col}_{shade if shade != 0 else 'No'}_Shading.cir", "w+"
    ) as f:
        f.write("* Files designed by circuit-sim by Nate Ruppert\n")
        f.write(
            f"* Circuit Simulation of {row} Series x {col} Parallel Solar Cell Arrangement\n"
        )
        f.write(f"* {shade} Shade {row * col - shade} No-Shade File\n")
        # Required for project
        f.write(".include cell_2.lib\n")
        f.write(f".option temp={temp}")
        f.write("\n")  # <br>

        # Adds data for each cell depending on how many cells to add
        for i in range(col):
            f.write(f"\n*** Start of Column {i + 1:02d}\n\n")

            for j in range(1, row + 1):
                # Define Start

                start = f"{i}{j}"

                # Define End
                end = f"{i}{j + 1}"
                # Cell A and Cell B design
                # xcell_01_12 12 01 1201
                # xcell_12_00 0  12 0012
                # virrad_11_12  1201  12 dc 1000
                # virrad_12_00  0012  0  dc 1000
                # Formats similar to above - sorta
                f.write(f"** Cell {j:02d} [Col {i + 1:02d}]\n")
                f.write(
                    f'xcell_{start}_{end} {end if j != row else "0"} {start if j != 1 else "01"} '
                    f"{end}{start} cell_2 params:area=49  j0=16E-20 j02=1.2E-12\n"
                )
                f.write("+ jsc=30.5E-3 rs=28e-3 rsh=100000\n")
                # Voltage changed to use shade
                if (i + 1) * j <= shade:  # Shade number indicates how many to shade
                    f.write(
                        f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {shade_val}\n'
                    )
                else:
                    f.write(
                        f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {full_val}\n'
                    )
                f.write("\n")  # <br>
        f.write("\nvbias 01 0 dc 0\n")  # Add voltage probe
        f.write(".plot dc i(vbias)\n")  # Plot current based on voltage probe
        f.write(
            f".dc vbias 0 {1.05 * row} 0.01\n"
        )  # Indicate voltage probe voltage characteristics
        f.write(".probe\n.end\n")  # End file


def create_special_file(
    path, row, col, shade, full_val, shade_val, temp, type, type_num
):
    with open(f"{path}/{row}x{col}_{type_num}_{type.capitalize()}.cir", "w+") as f:
        f.write("* Files designed by circuit-sim by Nate Ruppert\n")
        f.write(
            f"* Circuit Simulation of {row} Series x {col} Parallel Solar Cell Arrangement\n"
        )
        f.write(f"* {type_num} {type} {row * col - type_num} No-{type} File\n")
        # Required for project
        f.write(".include cell_2.lib\n")
        f.write(f".option temp={temp}")
        f.write("\n")  # <br>

        # Adds data for each cell depending on how many cells to add
        for i in range(col):
            f.write(f"\n*** Start of Column {i + 1:02d}\n\n")
            # For open circuits, we simply skip creating data for a column
            if type == "open" and i >= col - type_num:
                f.write("* Column Skipped due to Open Circuit\n")
                continue
            for j in range(1, row + 1):
                # Define Start

                start = f"{i}{j}"

                # Define End
                end = f"{i}{j + 1}"
                # Cell A and Cell B design
                # xcell_01_12 12 01 1201
                # xcell_12_00 0  12 0012
                # virrad_11_12  1201  12 dc 1000
                # virrad_12_00  0012  0  dc 1000
                # Formats similar to above - sorta
                f.write(f"** Cell {j:02d} [Col {i + 1:02d}]\n")
                f.write(
                    f'xcell_{start}_{end} {end if j != row else "0"} {start if j != 1 else "01"} '
                    f"{end}{start} cell_2 params:area=49  j0=16E-20 j02=1.2E-12\n"
                )
                f.write("+ jsc=30.5E-3 rs=28e-3 rsh=100000\n")
                # Voltage changed to use shade
                f.write(
                    f'virrad_{start}_{end}  {end}{start} {end if j != row else "0"} dc {full_val}\n'
                )
                if type == "short" and j == row and i + 1 > col - type_num:
                    # (j*i+1) > (col*row)-type_num:
                    f.write(f"is_{start}_{end} {start} 0 dc 0\n")
                f.write("\n")  # <br>
        f.write("\nvbias 01 0 dc 0\n")  # Add voltage probe
        f.write(".plot dc i(vbias)\n")  # Plot current based on voltage probe
        f.write(
            f".dc vbias 0 {1.05 * row} 0.01\n"
        )  # Indicate voltage probe voltage characteristics
        f.write(".probe\n.end\n")  # End file


def main():
    config = configparser.ConfigParser()
    config.read("data_sets.ini")

    data_sets = [
        [key, config[key]["temps"]] for key in config.keys() if key != "DEFAULT"
    ]
    file_sets = list_types()

    for set, temps in data_sets:

        # Step 1: Collect Temperatures to Run
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
        print(f"Generating {set} for temperatures: {temp_sets}")
        for temp in temp_sets:
            for row, col in file_sets:
                high, low = map(int, set.split("-"))
                filepath = f"Output/{high}-{low}/Temp{temp}/{row}x{col}"
                os.makedirs(
                    pathlib.PurePath(filepath),
                    exist_ok=True,
                )
                with open("cell_2.lib", "r") as file_r, open(
                    filepath + "/cell_2.lib", "w"
                ) as f:
                    f.write(file_r.read())  # write out the file to correct pathing
                for num in range(row * col + 1):
                    create_file(
                        filepath,
                        row,
                        col,
                        num,
                        high,
                        low,
                        temp,
                    )
                    if num > 0:
                        if num < col:
                            create_special_file(
                                filepath,
                                row,
                                col,
                                0,
                                high,
                                low,
                                temp,
                                "open",
                                num,
                            )
                        if num <= col:
                            create_special_file(
                                filepath,
                                row,
                                col,
                                0,
                                high,
                                low,
                                temp,
                                "short",
                                num,
                            )


if __name__ == "__main__":
    main()
