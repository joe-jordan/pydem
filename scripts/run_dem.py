#! /usr/bin/python
# 
# pydem/run_dem.py : executible to run a dem simulation
# 
# Copyright (C) 2012  Joe Jordan
# <joe.jordan@imperial.ac.uk>
# <tehwalrus@h2j9k.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

import sys, pydem

def print_usage():
  print """
  run_dem.py - a program to run a DEM simulation from the command line.
  (distributed under GPLv2, and uses components (LAMMPS) which are also GPLv2.)
  
  USAGE:
  
  run_dem.py system_file
  
  where 'system_file' refers to a .json.gz file containing the physics model,
  boundary conditions and granular particle properties. 
"""

if __name__ == "__main__":
  
  if len(sys.argv) < 2:
    print_usage()
    exit()
  
  data = pydem.open_system(sys.argv[1])
  
  new_data = pydem.run_simulation(
    data,
    endpoint=pydem.Endpoint.EQUILIBRIUM
  )
  
  pydem.save_system(new_data, sys.argv[1])
  
  