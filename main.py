import os


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
                    print(f"[{i}] Solar Arrangement {cellA}x{cellB}")
                    a.append([cellA, cellB])
    return a


if __name__ == "__main__":

    for col, row in list_types():
        print(f"{col}x{row}.cir")
        os.makedirs("Output", exist_ok=True)
        with open(f"Output/{col}x{row}.cir", "w+") as f:
            f.write("* Files designed by circuit-sim by Nate Ruppert\n")
            f.write(f"* Circuit Simulation of {col}x{row} Solar Cell Arrangement\n")
            # Required for project
            temp = 30  # TODO future support for changing temps
            f.write(".include cell_2.lib\n")
            f.write(f".option temp={temp}")
