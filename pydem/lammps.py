# 
# pydem/lammps.py : lammps interface
#
# V1 - VERY PRIMITIVE.
#   This library interacts with lammps using temp files for
#   communication. It is anticipated that more advanced python
#   bindings will make this obsolete, hopefully quickly!
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

import tempfile, os, shutil

_temp_dir
_old_path

_script_filename = 'script.lammps'
_stdout_filename = 'stdout.out'
_dump_filename = 'output.txt'



def run_simulation(data, timestep_limit=10000):
  temp_dir = lammps.generate_script(data, timestep_limit)
  _old_path = os.getcwd()
  
  os.chdir(temp_dir)
  
  os.system("lammps < %s > %s" % _script_filename, _stdout_filename)
  dump_lines = open(_dump_filename, 'r').readlines()
  new_data = lammps.parse_dump(dump_lines)
  
  os.chdir(_old_path)
  shutil.rmtree(_temp_dir)
  
  return new_data

def generate_script(data, timestep_limit):
  _temp_dir = tempfile.mkdtemp()
  
  # TODO generate the script text in response to the data.
  
  return _temp_dir


def parse_dump(dump_lines):
  # TODO deserialise output data from lammps
  return data





