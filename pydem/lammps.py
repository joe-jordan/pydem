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


def generate_script(data, timestep_limit):
  # TODO - write two temp files and define the location for a third.
  return temp_file, stdout_file, dump_file


def parse_dump(dump_lines):
  # TODO deserialise output data from lammps
  return data





