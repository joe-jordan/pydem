#!/usr/local/bin/python

"""
setup_serial.py file for pydem LAMMPS bindings.
"""

from distutils.core import setup

setup(name = "pydem",
      version = "14May2012",
      author = "Joe Jordan",
      author_email = "joe.jordan@imperial.ac.uk",
      url = "https://github.com/joe-jordan/pydem",
      description = """DEM simulations in python, using the LAMMPS python interface.""",
      packages = ["pydem"]
      )