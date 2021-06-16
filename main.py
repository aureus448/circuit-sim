import os
import pathlib


def list_types():
    max_cells = [8, 9, 10]
    a = []
    for i in max_cells:
        solar_cell = [x for x in range(1, i + 1) if (i % x == 0 and x <= i)]
        for cellA in solar_cell:
            for cellB in solar_cell:
                if cellA == cellB and cellA * cellB != i:
                    continue
                elif cellA * cellB == i:
                    print(f"[{i}] Will Design Solar Arrangement {cellA}x{cellB}")
                    a.append([cellA, cellB])
    return a


def create_file(path, row, col, shade, full_val, shade_val):
    with open(
        f"{path}/{row}x{col}_{shade if shade != 0 else 'No'}_Shading.cir", "w+"
    ) as f:
        f.write("* Files designed by circuit-sim by Nate Ruppert\n")
        f.write(
            f"* Circuit Simulation of {row} Series x {col} Parallel Solar Cell Arrangement\n"
        )
        # Required for project
        temp = 30  # TODO future support for changing temps
        f.write(".include cell_2.lib\n")
        f.write(f".option temp={temp}")
        f.write("\n")  # <br>

        # Adds data for each cell depending on how many cells to add
        for i in range(col):
            f.write(f"\n*** Start of Column {i+1:02d}\n\n")

            for j in range(1, row + 1):
                # Define Start

                start = f"{i}{j}"

                # Define End
                end = f"{i}{j+1}"
                # Cell A and Cell B design
                # xcell_01_12 12 01 1201
                # xcell_12_00 0  12 0012
                # virrad_11_12  1201  12 dc 1000
                # virrad_12_00  0012  0  dc 1000
                # Formats similar to above - sorta
                f.write(f"** Cell {j:02d} [Col {i+1:02d}]\n")
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
            f".dc vbias 0 {1.05*row} 0.01\n"
        )  # Indicate voltage probe voltage characteristics
        f.write(".probe\n.end\n")  # End file


if __name__ == "__main__":

    for row, col in list_types():

        # TODO code designed to develop shade/no-shade (default case 1000-900)
        full = 1000
        shade_val = 900

        for n_shade in range(row * col + 1):
            os.makedirs(
                pathlib.PurePath(f"Output/{full}-{shade_val}/{row}x{col}"),
                exist_ok=True,
            )
            create_file(
                f"Output/{full}-{shade_val}/{row}x{col}",
                row,
                col,
                n_shade,
                full,
                shade_val,
            )
