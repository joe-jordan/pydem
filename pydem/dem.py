# 
# pydem/dem.py : lammps interface
#
# V2 - a wrapper around the lammps C interface.
#   This library interacts with lammps using the lammps C interface at
#   lammps/python/lammps.py and lammps/src/library.h or cpp .
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
#
# NOTE: results received from the lammps lib calls are strange c-pointer
# objects - even if they are "arrays", they are NOT python lists.
# DO NOTE ITERATE using 'for item in lammps.extract_atom('x',..)
# it will loop infinitely over two pointer things. always use x[0].
#

import os, os.path, shutil, numbers
from pydem import ForceModelType, vector_length
import lammps

class Simulation:
  """a class to encapsulate the lifetime of a simulation, and marshal the
  lammps instance and associated ctypes and function calls.
  """
  
  _init_commands = """atom_style ATOMSTYLE
units si

communicate single vel yes

dimension DIMENSION

boundary BOUNDARY

lattice sq 1.0

region outer_box block SIMULATION_ZONE

create_box NUM_ATOMS outer_box"""
  
  def initialise(self, data):
    """builds a lammps instance, and sets up the simulation based on the data
provided - called automatically if data is provided to the constructor."""
    self.data = data
    
    if (lammps_instance == None):
      self.lmp = lammps.lammps()
    
    commands = [line for line in self._build_init().split("\n") if line != ""]
    
    self._run_commands(commands)
    
    # TODO add particles
    
    # TODO setup fixes and timestep data
  
  def __init__(self, data=None):
    """data can be provided here, in which case lammps in initialised for use
immidiately, or instance.initialise(data) can be called later."""
    self.fixes_applied = False
    if datas != None:
      self.initialise(data)
  
  def _build_init(self):
    output_commands = Simulation._init_commands
    
    styles = set([e['style'] for e in self.data['elements']])
    print styles
    styles_str = styles.pop() if len(styles) == 1 else 'hybrid ' + ' '.join(styles)
    
    output_commands = output_commands.replace('ATOMSTYLE', styles_str)
    output_commands = output_commands.replace('DIMENSION', '%i' % self.data['params']['dimension'])
    
    # pydem does not endorse unphysical periodic boundary conditions in 
    # mechanically equilibriated granular systems.
    output_commands = output_commands.replace('BOUNDARY', 'f f p' if self.data['params']['dimension'] == 2 else 'f f f')
    
    # assume lower bound is zero.
    zone_str = ' '.join([
      '-1.0', str(self.data['params']['x_limit'] + 1.0),
      '-1.0', str(self.data['params']['y_limit'] + 1.0),
      '-1.0', str(self.data['params']['z_limit'] + 1.0) if self.data['params']['dimension'] > 2 else '1.0'
    ])
    
    output_commands = output_commands.replace('SIMULATION_ZONE', zone_str)
    output_commands = output_commands.replace('NUM_ATOMS', str(len(self.data['elements'])))
    
    return output_commands
  
  def add_particles(self, new_particles):
    """use this to add particles to lammps safely - do not simply add to
data['elements'], as lammps will not be notified."""
    pass
  
  def remove_particles(self, defunct_particles):
    """use this to safely remove particles from the simulation. The particles
will be automatically removed from data['elements'] after they are removed from
lammps."""
    pass
  
  def particles_modified(self):
    """always call this method when elements' python properties have been
changed that require persisting to lammps, e.g. when position or velocity are
manually assigned. This function is automatically called by the add and remove
functions."""
    pass
  
  def constants_modified(self):
    """always call this method when simulation params' python properties have
been changed that require persisting to lammps, e.g. when the force constants
or damping have been manually assigned."""
    if self.fixes_applied:
      self._remove_fixes()
      self.fixes_applied = False
    
    commands = self._generate_fixes()
    
    self._run_commands(commands)
    
    self.fixes_applied = True
  
  def _remove_fixes(self):
    pass
  
  def _generate_fixes(self):
    pass
  
  def run_time(self, how_long):
    """when a simulation is ready to run timesteps, call this function with the
number of timesteps to proceed by. You can also provide the number of 
in-universe seconds to run for, and this will be translated to timesteps for
you, although note that this MUST be a float:
  instance.run_time(5) => run 5 timesteps,
  instance.run_time(5.0) => run for 5 in-universe seconds."""
    if not isinstance(how_long, numbers.Integral):
      how_long = int(how_long / self.data['params']['force_model']['timestep'])
    
    if how_long <= 0:
      return
    
    self.lmp.command('run ' + str(how_long))
  
  def _run_commands(self, commands):
    for c in commands:
      self.lmp.command(c)




_script_filename = 'script.lammps'
_stdout_filename = 'stdout.out'
_dump_filename = 'output.txt'
_binary_restart_filename = 'output.bin'

_script_template = """
atom_style ATOMSTYLE
units si

communicate single vel yes

dimension DIMENSION

boundary BOUNDARY

lattice sq 1.0

region outer_box block SIMULATION_ZONE

create_box NUM_ATOMS outer_box

CREATE_STATEMENTS

SETUP_STATEMENTS

pair_style PARTICLE_PARTICLE_INTERACTIONS
pair_coeff * *

fix update_positions all nve/sphere

2D_FIX

fix grav all gravity GRAVITY_SIZE vector GRAVITY_X GRAVITY_Y GRAVITY_Z

WALL_FIXES

timestep DELTA_T

dump data all custom 100 DUMP_FILENAME id radius mass x y z vx vy vz omegax omegay omegaz

run TIMESTEP_LIMIT

# TODO don't generate this file until we have a 'step 2' script to restart from it, and then append more atoms.
#write_restart RESTART_FILENAME

"""

_create_template = """create_atoms ID single RX RY RZ
group ID id ID
"""

_setup_template = """set atom ID mass MASS
set atom ID diameter DIAM
velocity ID set VX VY VZ
group ID delete
"""

# broken.
_setup_angular_template = """set atom ID mass MASS
set atom ID diameter DIAM
velocity ID set LX LY LZ rot yes
velocity ID set VX VY VZ
"""

# TODO.
_setup_aspherical_angular_template = """set atom ID mass MASS
set atom ID diameter DIAM
set atom ID angmom LX LY LZ
velocity ID set VX VY VZ
"""

_interaction_template = "SPRING_TYPE K_N K_T ETA_N ETA_T ROTATION_RATIO INCLUDE_TANGENTIAL_FRICTION"

_2d_fix = "fix enforce_planar all enforce2d"

_spring_types = {
  ForceModelType.HOOKIAN : 'gran/hooke',
  ForceModelType.HERZIAN : 'gran/hertz/history'
}

_wall_type = "wall/gran"

lammps_sphere_properties = [
  'x',
  'v',
  'f',
  'rmass',
  'radius',
  'omega'
]

lammps_extracts = {
  'x' : lammps.LMPDPTRPTR,
  'v' : lammps.LMPDPTRPTR,
  'f' : lammps.LMPDPTRPTR,
  'rmass' : lammps.LMPDPTR,
  'radius' : lammps.LMPDPTR,
  'omega' : lammps.LMPDPTRPTR,
  # angmom and torque are for ellipsoids. (TODO shape and quat)
  'angmom' : lammps.LMPDPTRPTR,
  'torque' : lammps.LMPDPTRPTR
}

def run_simulation(data, lammps_instance=None, timestep_limit=10000):
  lammps_script = generate_script(data, timestep_limit)
  
  commands = [line for line in lammps_script.split("\n") if line != ""]
  
  if (lammps_instance == None):
    lammps_instance = lammps.lammps()
  
  for c in commands:
    print c
    lammps_instance.command(c)
  
  init_python_from_lammps(data, lammps_instance)
  
  print "from extract_atom:"
  for req in ['x', 'v', 'omega']:
    x = lammps_instance.extract_atom(req, lammps.LMPDPTRPTR)
    
    print req, x[0][0], x[0][1], x[0][2], x[1][0], x[1][1], x[1][2]
  
  update_python_from_lammps(data, lammps_instance)
  
  #TODO tidy up lammps instance.

def init_python_from_lammps(data, lammps_instance):
  vars = {}
  for var in lammps_sphere_properties:
    vars[var] = lammps_instance.extract_atom(var, lammps_extracts[var])
  for i, e in enumerate(data['elements']):
    params = {}
    for key, value in vars.items():
      try:
        params[key] = value[i]
      except:
        print "error from key", key
        raise
    e.init_lammps(params)

def update_python_from_lammps(data, lammps_instance):
  for e in data['elements']:
    e.update_from_lammps()

def generate_script(data, timestep_limit):
  output_script_text = _script_template
  
  styles = set([e['style'] for e in data['elements']])
  print styles
  styles_str = styles.pop() if len(styles) == 1 else 'hybrid ' + ' '.join(styles)
  
  output_script_text = output_script_text.replace('ATOMSTYLE', styles_str)
  output_script_text = output_script_text.replace('DIMENSION', '%i' % data['params']['dimension'])
  
  # pydem does not endorse unphysical periodic boundary conditions in 
  # mechanically equilibriated granular systems.
  output_script_text = output_script_text.replace('BOUNDARY', 'f f p' if data['params']['dimension'] == 2 else 'f f f')
  
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
    create_statements.append(_string_sub(_create_template, { 'ID' : str(i+1),
      'RX' : str(e['position'][0]),
      'RY' : str(e['position'][1]),
      'RZ' : str(e['position'][2]) if data['params']['dimension'] > 2 else '0.0'
    }))
    
    smap = { 'ID' : str(i+1),
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
    # TODO - allow initialisation of angular speed, requires lammps extension.
    #if data['params']['force_model']['include_tangential_forces']:
    #  local_setup_template = _setup_angular_template
    #  try:
    #    smap['LX'] = str(e['angular_velocity'][0]) if data['params']['dimension'] > 2 else '0.0'
    #    smap['LY'] = str(e['angular_velocity'][1]) if data['params']['dimension'] > 2 else '0.0'
    #    smap['LZ'] = str(e['angular_velocity'][2]) if data['params']['dimension'] > 2 else str(e['angular_velocity'])
    #  except KeyError:
    #    smap['LX'] = '0.0'
    #    smap['LY'] = '0.0'
    #    smap['LZ'] = '0.0'
    
    # watch out!
    create_statements.append(_string_sub(local_setup_template, smap))
  
  output_script_text = output_script_text.replace('CREATE_STATEMENTS', '\n'.join(create_statements))
  
  output_script_text = output_script_text.replace('SETUP_STATEMENTS', '\n'.join(setup_statements))
  
  fm = data['params']['force_model']
  
  output_script_text = output_script_text.replace('PARTICLE_PARTICLE_INTERACTIONS',
    _string_sub(_interaction_template, {
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
  
  d2fix = ""
  if data['params']['dimension'] == 2:
    d2fix = _2d_fix
  output_script_text = output_script_text.replace('2D_FIX', d2fix)
  
  output_script_text = output_script_text.replace(
    'GRAVITY_SIZE', str(vector_length(fm['gravity'])) ).replace(
    'GRAVITY_X', str(fm['gravity'][0]) ).replace(
    'GRAVITY_Y', str(fm['gravity'][1]) ).replace(
    'GRAVITY_Z', str(fm['gravity'][2]) if data['params']['dimension'] == 3 else '0.0')
  
  wall_physics = _string_sub(_interaction_template, {
    'SPRING_TYPE' : _wall_type,
    'K_N' : str(fm['boundary_constants']['spring_constant_norm']),
    'K_T' : str(fm['boundary_constants']['spring_constant_tan']) if fm['include_tangential_forces'] else 'NULL',
    'ETA_N' : str(fm['boundary_constants']['damping_norm']),
    'ETA_T' : str(fm['boundary_constants']['damping_tan']) if fm['include_tangential_forces'] else 'NULL',
    'ROTATION_RATIO' : str(
      fm['boundary_constants']['spring_constant_tan'] / fm['boundary_constants']['spring_constant_norm']
    ) if fm['include_tangential_forces'] else '0.5',
    'INCLUDE_TANGENTIAL_FRICTION' : '1' if fm['include_tangential_forces'] else '0'
  })
  
  wall_fixes = [
    'fix xwalls all ' + wall_physics + ' xplane 0.0 ' + str(data['params']['x_limit']),
    'fix ywalls all ' + wall_physics + ' yplane 0.0 ' + str(data['params']['y_limit'])
  ]
  
  if data['params']['dimension'] == 3:
    wall_fixes.append('fix zwalls all ' + wall_physics + ' zplane 0.0 ' + str(data['params']['z_limit']))
  
  output_script_text = output_script_text.replace('WALL_FIXES', '\n'.join(wall_fixes))
  
  output_script_text = output_script_text.replace('DELTA_T', str(fm['timestep']))
  
  output_script_text = output_script_text.replace('TIMESTEP_LIMIT', str(timestep_limit))
  
  output_script_text = output_script_text.replace('DUMP_FILENAME', _dump_filename)
  
  # TODO restart file, when we've written a restart script template.
  
  return output_script_text


def _string_sub(string, params):
  for key, value in params.items():
    string = string.replace(key, value)
  return string

def parse_dump(dump_lines):
  # TODO deserialise output data from lammps
  return data





