# Circuit Simulation for LTSpiceXVII
[![codecov](https://codecov.io/gh/aureus448/cuddly-disco/branch/main/graph/badge.svg?token=M7ZPP0ODE6)](https://codecov.io/gh/aureus448/cuddly-disco)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Check Code Base](https://github.com/aureus448/cuddly-disco/actions/workflows/check_code.yml/badge.svg)](https://github.com/aureus448/cuddly-disco/actions/workflows/check_code.yml)

A circuit simulation library designed to perform the following tasks:

- Design LTSpiceXVII `*.cir` files based on provided configuration files (`data_sets.ini`)
- Run LTSpiceXVII on each provided `*.cir` file *automatically* without user interaction
- Collect LTSpiceXVII `*.raw` files using the Python `ltpsice` library and use Pandas for data analysis on outputs of simulation runs

This library is being designed and developed specifically for a research project I participate in for CSUF related to Solar Drone cell design and implementation testing, and therefore is highly specific to my use case. However, the library is provided as-is for future developers to modify and use for their own circuit design purposes potentially. For example, the library's ability to simulate LTSpiceXVII files concurrently could be used separately from all other library uses.

However you intend to use it, enjoy.
