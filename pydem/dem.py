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
from better_ctypes import PointerFromArray
import lammps

class Simulation:
  """a class to encapsulate the lifetime of a simulation, and marshal the
  lammps instance and associated ctypes and function calls.
  """
  
  _init_commands = """log none
atom_style sphere
units si

communicate single vel yes

dimension DIMENSION

boundary BOUNDARY

lattice sq 1.0

region outer_box block SIMULATION_ZONE
region random_box block RANDOM_ZONE

create_box MAX_ATOM_GUESS outer_box"""
  
  # NOTE - we may wish to extend lammps to support 'blank' atoms through the
  # create_atom command, to save all the calls to the random libs.
  _create_atoms_template = "create_atoms 1 random NUM_ATOMS 1 random_box"
  
  _interaction_template = "SPRING_TYPE K_N K_T ETA_N ETA_T ROTATION_RATIO INCLUDE_TANGENTIAL_FRICTION"
  
  _fixes_template = """pair_style PARTICLE_PARTICLE_INTERACTIONS
pair_coeff * *

fix update_positions all nve/sphere

2D_FIX

fix grav all gravity GRAVITY_SIZE vector GRAVITY_X GRAVITY_Y GRAVITY_Z

WALL_FIXES

timestep DELTA_T"""
  
  _2d_fix = "fix enforce_planar all enforce2d"
  
  _lammps_extracts = {
    'x' : lammps.LMPDPTRPTR,
    'v' : lammps.LMPDPTRPTR,
    'f' : lammps.LMPDPTRPTR,
    'rmass' : lammps.LMPDPTR,
    'radius' : lammps.LMPDPTR,
    'omega' : lammps.LMPDPTRPTR
  }
  
  _spring_types = {
    ForceModelType.HOOKIAN : 'gran/hooke',
    ForceModelType.HERZIAN : 'gran/hertz/history'
  }
  
  def commands_from_script(self, script):
    return [line for line in script.split("\n") if line != ""]
  
  def initialise(self, data):
    """builds a lammps instance, and sets up the simulation based on the data
provided - called automatically if data is provided to the constructor."""
    self.data = data
    
    if (self.lmp == None):
      self.lmp = lammps.lammps()
    
    commands = self.commands_from_script(self._build_init())
    
    self._run_commands(commands)
    
    self.add_particles(self.data['elements'], already_in_array=True)
    
    self.constants_modified()
  
  def __init__(self, data=None):
    """data can be provided here, in which case lammps in initialised for use
immidiately, or instance.initialise(data) can be called later."""
    self.fixes_applied = False
    self.atoms_created = 0
    self.lmp = None
    if data != None:
      self.initialise(data)
  
  def _build_init(self):
    output_commands = Simulation._init_commands
    
    p = self.data['params']
    
    # there is no 'atom_style' variable to replace, since we assume all spheres
    output_commands = output_commands.replace('DIMENSION', str(p['dimension']))
    
    # pydem does not endorse unphysical periodic boundary conditions in 
    # mechanically equilibriated granular systems.
    output_commands = output_commands.replace('BOUNDARY', 'f f p' if p['dimension'] == 2 else 'f f f')
    
    limits = [p['x_limit'], p['y_limit']]
    if p['dimension'] > 2:
      limits.append(p['z_limit'])
    delta = max(limits) * 0.05
    
    lower = str(-1.0 * delta)
    
    # assume lower bound is zero.
    zone_str = ' '.join([
      lower, str(p['x_limit'] + delta),
      lower, str(p['y_limit'] + delta),
      lower, str(p['z_limit'] + delta) if p['dimension'] > 2 else str(delta)
    ])
    
    output_commands = output_commands.replace('SIMULATION_ZONE', zone_str)
    
    random_zone_str = ' '.join([
      str(delta), str(p['x_limit'] - delta),
      str(delta), str(p['y_limit'] - delta),
      str(delta) if p['dimension'] > 2 else lower, str(p['z_limit'] - delta) if p['dimension'] > 2 else str(delta)
    ])
    
    output_commands = output_commands.replace('RANDOM_ZONE', random_zone_str)
    
    output_commands = output_commands.replace('MAX_ATOM_GUESS', str(p['max_particles_guess']))
    
    return output_commands
  
  def _sync_pointers(self, particles, start_index=0, write_properties=False, read_properties=False):
    # TODO make particles store their lammps ID, so when particles are removed 
    # the IDs here need not be a contiguous block.
    print "_sync_pointers called with start_index", start_index
    vars = {}
    for var, ptrtype in Simulation._lammps_extracts.items():
      vars[var] = self.lmp.extract_atom(var, ptrtype)
    for i, e in enumerate(particles):
      params = {}
      for key, value in vars.items():
        try:
          if Simulation._lammps_extracts[key] == lammps.LMPDPTR:
            params[key] = PointerFromArray(value, start_index + i)
          else:
            # PTRPTRs are fine, as we get a new PTR from the subscript call.
            params[key] = value[start_index + i]
        except:
          print "error from key", key
          raise
      e.init_lammps(params, write_properties=write_properties, read_properties=read_properties)
  
  def add_particles(self, new_particles, already_in_array=False):
    """use this to add particles to lammps safely - do not simply add to
instance.data['elements'], as lammps will not be notified."""
    self._run_commands([
      Simulation._create_atoms_template.replace('NUM_ATOMS', str(len(new_particles)))
    ])
    
    self._sync_pointers(new_particles, start_index=self.atoms_created, write_properties=True)
    
    self.atoms_created += len(new_particles)
    
    if not already_in_array:
      self.data['elements'].extend(new_particles)
  
  def remove_particles(self, defunct_particles):
    """use this to safely remove particles from the simulation. The particles
will be automatically removed from data['elements'] after they are removed from
lammps."""
    raise Exception("warning, remove_particles not yet implemented.")
  
  def particles_modified(self):
    """always call this method when elements' python properties have been
changed that require persisting to lammps, e.g. when position or velocity are
manually assigned. This function is automatically called by the add and remove
functions."""
    self._sync_pointers(self.data['elements'], write_properties=True)
      
  
  def constants_modified(self):
    """always call this method when simulation params' python properties have
been changed that require persisting to lammps, e.g. when the force constants
or damping have been manually assigned."""
    if self.fixes_applied:
      self._remove_fixes()
      self.fixes_applied = False
    
    commands = self.commands_from_script(self._generate_fixes())
    
    self._run_commands(commands)
    
    self.fixes_applied = True
  
  def _remove_fixes(self):
    pass
  
  def _generate_fixes(self):
    fm = self.data['params']['force_model']
    
    script = Simulation._fixes_template.replace('PARTICLE_PARTICLE_INTERACTIONS',
      _string_sub(Simulation._interaction_template, {
        'SPRING_TYPE' : Simulation._spring_types[fm['type']],
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
    if self.data['params']['dimension'] == 2:
      d2fix = Simulation._2d_fix
    script = script.replace('2D_FIX', d2fix)
    
    script = script.replace(
      'GRAVITY_SIZE', str(vector_length(fm['gravity'])) ).replace(
      'GRAVITY_X', str(fm['gravity'][0]) ).replace(
      'GRAVITY_Y', str(fm['gravity'][1]) ).replace(
      'GRAVITY_Z', str(fm['gravity'][2]) if self.data['params']['dimension'] == 3 else '0.0')
    
    wall_physics = _string_sub(Simulation._interaction_template, {
      'SPRING_TYPE' : "wall/gran",
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
      'fix xwalls all ' + wall_physics + ' xplane 0.0 ' + str(self.data['params']['x_limit']),
      'fix ywalls all ' + wall_physics + ' yplane 0.0 ' + str(self.data['params']['y_limit'])
    ]
    
    if self.data['params']['dimension'] == 3:
      wall_fixes.append('fix zwalls all ' + wall_physics + ' zplane 0.0 ' + str(self.data['params']['z_limit']))
    
    script = script.replace('WALL_FIXES', '\n'.join(wall_fixes))
    
    return script.replace('DELTA_T', str(fm['timestep']))
  
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
    
    self._update_particles_from_lammps()
  
  def _update_particles_from_lammps(self):
    for e in self.data['elements']:
      e.update_from_lammps()
  
  def _update_lammps_from_python(self):
    for e in self.data['elements']:
      e.overwrite_lammps()
  
  def _run_commands(self, commands):
    for c in commands:
      print "running commend:", c
      self.lmp.command(c)

def _string_sub(string, params):
  for key, value in params.items():
    string = string.replace(key, value)
  return string
