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
import logging

# import _paths  # noqa: W0611
import circuit_sim


def test_create_files():
    """No supported variability in main yet - if successful run mark test pass"""
    circuit_sim.create_files(".")


def test_create_files_exists():
    """No supported variability in main yet - if successful run mark test pass"""
    circuit_sim.create_files(".")


def test_logger():
    logger = circuit_sim.set_logger(logging.getLogger(__file__), "circuit_sim.log")
    assert type(logger) == logging.Logger
