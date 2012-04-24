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

import tempfile, os, os.path, shutil

#_temp_dir
#_old_path

_script_filename = 'script.lammps'
_stdout_filename = 'stdout.out'
_dump_filename = 'output.txt'
_binary_restart_filename = 'output.bin'

_script_template = """
atom_style ATOMSTYLE
units lj

dimension DIMENSION

boundary BOUNDARY

lattice sq 0.1

region outer_box block SIMULATION_ZONE

create_box NUM_ATOMS outer_box

#############################################
# TODO: create atoms script...

create_atoms 1 random 400 29875 my_box
create_atoms 2 random 400 98207 my_box


communicate single vel yes
run_style verlet


#############################################
# TODO: create atoms script...
# set up a sensible bidisperse granular system:
set type 1 diameter 0.9
set type 2 diameter 0.6

set type 1 density 3.0
set type 2 density 3.0



# K_N K_T ETA_N ETA_T ROTATION_RATIO INCLUDE_TANGENTIAL_FRICTION
pair_style gran/hooke PARTICLE_PARTICLE_INTERACTIONS
pair_coeff * *

fix 1 all nve/sphere

fix 2 all enforce2d
fix 3 all gravity GRAVITY_SIZE vector GRAVITY_X GRAVITY_Y GRAVITY_Z

# K_N_WALL K_T_WALL ETA_N_WALL ETA_T_WALL ROTATION_RATIO_WALL INCLUDE_TANGENTIAL_FRICTION
fix 4 all wall/gran PARTICLE_WALL_INTERACTIONS xplane 0.0 X_LIMIT
fix 5 all wall/gran PARTICLE_WALL_INTERACTIONS yplane 0.0 Y_LIMIT

timestep DELTA_T

dump data all custom TIMESTEP_LIMIT DUMP_FILENAME radius mass x y z vx vy vz omegax omegay omegaz

run TIMESTEP_LIMIT

write_restart RESTART_FILENAME

"""

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
  
  output_script_text = _script_template
  
  styles = set([e['shape'] for e in data['elements']])
  styles_str = styles[0] if len(styles) == 1 else 'hybrid ' + ' '.join(styles)
  
  output_script_text = output_script_text.replace('ATOMSTYLE', styles_str)
  output_script_text = output_script_text.replace('DIMENSION', '%i' % data['params']['dimension'])
  
  # pydem does not endorse unphysical periodic boundary conditions in 
  # mechanically equilibriated granular systems.
  output_script_text = output_script_text.replace('BOUNDARY', 'f f p' if data['params']['dimension'] > 2 else 'f f f')
  
  # assume lower bound is zero.
  zone_str = ' '.join([
    '-1.0', str(data['params']['x_limit'] + 1.0),
    '-1.0', str(data['params']['y_limit'] + 1.0),
    '-1.0', str(data['params']['z_limit'] + 1.0) if data['params']['dimension'] > 2 else '1.0'
  ])
  
  output_script_text = output_script_text.replace('SIMULATION_ZONE', zone_str)
  output_script_text = output_script_text.replace('NUM_ATOMS', str(len(data['elements'])))
  
  # TODO...
  
  f = open(os.path.join(_temp_dir, _script_filename), 'w')
  f.write(output_script_text)
  f.close()
  
  return _temp_dir


def parse_dump(dump_lines):
  # TODO deserialise output data from lammps
  return data





