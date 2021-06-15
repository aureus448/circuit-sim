def list_types():
    max_cells = [8, 9, 10]
    for i in max_cells:
        solar_cell = [x for x in range(1, i + 1) if (i % x == 0 and x <= i)]
        for cellA in solar_cell:
            for cellB in solar_cell:
                if cellA == cellB and cellA * cellB != i:
                    continue
                elif cellA * cellB == i:
                    print(f'[{i}] Solar Arrangement {cellA}x{cellB}')


if __name__ == '__main__':
    list_types()
