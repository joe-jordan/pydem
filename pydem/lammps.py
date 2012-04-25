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
from pydem import ForceModelType

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

CREATE_STATEMENTS

SETUP_STATEMENTS

pair_style PARTICLE_PARTICLE_INTERACTIONS
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

# TODO don't generate this file until we have a 'step 2' script to restart from it, and then append more atoms.
#write_restart RESTART_FILENAME

"""

_create_template = """create_atoms ID single RX RY RZ
"""

_setup_template = """set atom ID mass MASS
set atom ID diameter DIAM
velocity ID set VX VY VZ
"""

_setup_angular_template = """set atom ID mass MASS
set atom ID diameter DIAM
set atom ID angmom LX LY LZ
velocity ID set VX VY VZ
"""

_pairwise_interactions_template = """SPRING_TYPE K_N K_T ETA_N ETA_T ROTATION_RATIO INCLUDE_TANGENTIAL_FRICTION
"""

_spring_types = {
  ForceModelType.HOOKIAN : 'gran/hooke',
  ForceModelType.HERZIAN : 'gran/hertz/history'
}

def run_simulation(data, timestep_limit=10000):
  temp_dir = tempfile.mkdtemp()
  lammps_script = generate_script(data, timestep_limit)
  
  f = open(os.path.join(temp_dir, _script_filename), 'w')
  f.write(output_script_text)
  f.close()
  
  _old_path = os.getcwd()
  
  os.chdir(temp_dir)
  
  os.system("lammps < %s > %s" % _script_filename, _stdout_filename)
  dump_lines = open(_dump_filename, 'r').readlines()
  new_data = lammps.parse_dump(dump_lines)
  
  os.chdir(_old_path)
  shutil.rmtree(_temp_dir)
  
  return new_data

def generate_script(data, timestep_limit):
  output_script_text = _script_template
  
  styles = set([e['style'] for e in data['elements']])
  styles_str = styles.pop() if len(styles) == 1 else 'hybrid ' + ' '.join(styles)
  
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
  
  create_statements = []
  setup_statements = []
  
  for i, e in enumerate(data['elements']):
    create_statements.append(_string_sub(_create_template, { 'ID' : str(i),
      'RX' : str(e['position'][0]),
      'RY' : str(e['position'][1]),
      'RZ' : str(e['position'][2]) if data['params']['dimension'] > 2 else '0.0'
    }))
    
    smap = { 'ID' : str(i),
      'MASS' : str(e['mass']),
      'DIAM' : str(2.0 * e['radius'])
    }
    
    try:
      smap['VX'] = str(e['velocity'][0])
      smap['VY'] = str(e['velocity'][1])
      smap['VZ'] = str(e['velocity'][2]) if data['params']['dimension'] > 2 else '0.0'
    except KeyError:
      smap['VX'] = '0.0'
      smap['VY'] = '0.0'
      smap['VZ'] = '0.0'
    
    local_setup_template = _setup_template
    if data['params']['force_model']['include_tangential_forces']:
      local_setup_template = _setup_angular_template
      try:
        smap['LX'] = str(e['angular_velocity'][0]) if data['params']['dimension'] > 2 else '0.0'
        smap['LY'] = str(e['angular_velocity'][1]) if data['params']['dimension'] > 2 else '0.0'
        smap['LZ'] = str(e['angular_velocity'][2]) if data['params']['dimension'] > 2 else str(e['angular_velocity'])
      except KeyError:
        smap['LX'] = '0.0'
        smap['LY'] = '0.0'
        smap['LZ'] = '0.0'
    
    setup_statements.append(_string_sub(local_setup_template, smap))
  
  output_script_text = output_script_text.replace('CREATE_STATEMENTS', '\n'.join(create_statements))
  
  output_script_text = output_script_text.replace('SETUP_STATEMENTS', '\n'.join(setup_statements))
  
  fm = data['params']['force_model']
  
  output_script_text = output_script_text.replace('PARTICLE_PARTICLE_INTERACTIONS',
    _string_sub(_pairwise_interaction_template, {
      'SPRING_TYPE' : _spring_types[fm['type']],
      'K_N' : str(fm['pairwise_constants']['spring_constant_norm']),
      'K_T' : str(fm['pairwise_constants']['spring_constant_tan']) if fm['include_tangential_forces'] else 'NULL',
      'ETA_N' : str(fm['pairwise_constants']['damping_norm']),
      'ETA_T' : str(fm['pairwise_constants']['damping_tan']) if fm['include_tangential_forces'] else 'NULL',
      'ROTATION_RATIO' : str(
        fm['pairwise_constants']['spring_constant_tan'] / fm['pairwise_constants']['spring_constant_norm']
      ) if fm['include_tangential_forces'] else '0.5',
      'INCLUDE_TANGENTIAL_FRICTION' : '1' if fm['include_tangential_forces'] else '0'
    }))
  
  # TODO gravity
  
  # TODO wall interactions
  
  # TODO timestep, data dump, restart file 
  
  return output_script_text


def _string_sub(string, params):
  for key, value in params.items():
    string = string.replace(key, value)
  return string

def parse_dump(dump_lines):
  # TODO deserialise output data from lammps
  return data





