#!/usr/bin/env python

"""
setup.py file for pydem LAMMPS bindings.
"""

from distutils.core import setup

setup(name = "pydem",
      version = "2Jun2012",
      author = "Joe Jordan",
      author_email = "joe.jordan@imperial.ac.uk",
      url = "https://github.com/joe-jordan/pydem",
      description = """DEM simulations in python, using the LAMMPS python interface.""",
      packages = ["pydem"]
      )