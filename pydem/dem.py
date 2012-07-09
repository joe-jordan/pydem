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
  
  TOTAL = 'totaleoutput'
  KINETIC = 'kineticeoutput'
  POTENTIAL = 'potentialeoutput'
  
  _init_commands = """atom_style sphere
units si

communicate single vel yes

dimension DIMENSION

boundary BOUNDARY

lattice LATTICE

region outer_box block SIMULATION_ZONE
region random_box block RANDOM_ZONE

create_box MAX_ATOM_GUESS outer_box

variable totaleoutput equal etotal
variable kineticeoutput equal ke
variable potentialeoutput equal pe"""
  
  # NOTE - we may wish to extend lammps to support 'blank' atoms through the
  # create_atom command, to save all the calls to the random libs.
  _create_atoms_template = "create_atoms 1 random NUM_ATOMS 1 random_box"
  
  _interaction_template = "SPRING_TYPE K_N K_T ETA_N ETA_T ROTATION_RATIO INCLUDE_TANGENTIAL_FRICTION"
  
  _fixes_template = """pair_style PARTICLE_PARTICLE_INTERACTIONS
pair_coeff * *

fix update_positions all nve/sphere

2D_FIX

GRAVITY

WALL_FIXES

timestep DELTA_T"""
  
  _gravity_fix = "fix grav all gravity GRAVITY_SIZE vector GRAVITY_X GRAVITY_Y GRAVITY_Z"
  
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
      args = ['-log', 'none']
      if not self.show_lammps_output:
        args.extend(['-screen', 'none'])
      self.lmp = lammps.lammps(args=args)
    
    commands = self.commands_from_script(self._build_init())
    
    self._run_commands(commands)
    
    self.add_particles(self.data['elements'], already_in_array=True)
    
    self.constants_modified()
    
    self.timesteps_run = [0]
    
  
  def __init__(self, data=None):
    """data can be provided here, in which case lammps in initialised for use
immidiately, or instance.initialise(data) can be called later.
lammps spits out a LOT to the command line, especially when running with the
simple visualiser. This is disabled by default, but you can pass
show_lammps_output=True
to this constructor to enable it."""
    self.show_lammps_output = False
    self.show_lammps_input = False
    self.renderer = None
    for option in ['show_lammps_output', 'show_lammps_input', 'renderer']:
      try:
        setattr(self, option, data['params'][option])
      except KeyError:
        pass
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
    
    output_commands = output_commands.replace('LATTICE', "sq 1.0" if p['dimension'] == 2 else "custom 1.0 a1 1.0 0.0 0.0 a2 0.0 1.0 0.0 a3 0.0 0.0 1.0 basis 0.0 0.0 0.0")
    
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
    ids_to_remove = [self.data['elements'].index(i) for i in defunct_particles]
    ids_as_strings = [str(i) for i in ids_to_remove]
    command = 'delete_atoms ids ' + ' '.join(ids_as_strings)
    self._run_commands([command])
    self.data['elements'] = [e for i, e in enumerate(self.data['elements']) if i not in ids_to_remove]
    self._sync_pointers(self.data['elements'], read_properties=True)
    
  
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
  
  def _generate_gravity_fix(self):
    g = self.data['params']['force_model']['gravity']
    g_length = vector_length(g)
    # if we are disabling gravity, we want to make sure the vector is nonzero.
    if g_length == 0.0:
      g = [1.0, 0.0, 0.0]
    return Simulation._gravity_fix.replace(
      'GRAVITY_SIZE', str(g_length) ).replace(
      'GRAVITY_X', str(g[0]) ).replace(
      'GRAVITY_Y', str(g[1]) ).replace(
      'GRAVITY_Z', str(g[2]) if self.data['params']['dimension'] == 3 else '0.0')
  
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
    
    script = script.replace('GRAVITY', self._generate_gravity_fix())
    
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
  
  def compute_energy(self, type=TOTAL):
    return self.lmp.extract_variable(type, None, 0)
  
  def _run_time_internal(self, timesteps_to_run):
    self._run_commands(['run ' + str(timesteps_to_run)])
    self.timesteps_run.append(timesteps_to_run)
    self._update_particles_from_lammps()
  
  def run_time(self, time, dont_render=False):
    """when a simulation is ready to run timesteps, call this function with the
number of timesteps to proceed by. You can also provide the number of 
in-universe seconds to run for, and this will be translated to timesteps for
you, although note that this MUST be a float:
  instance.run_time(5) => run 5 timesteps,
  instance.run_time(5.0) => run for 5 in-universe seconds."""
    if isinstance(time, numbers.Integral):
      how_many = time
      how_long = how_many * self.data['params']['force_model']['timestep']
    else:
      how_many = int(time / self.data['params']['force_model']['timestep'])
      how_long = time
    
    if self.renderer != None and not dont_render:
      frame_how_long = self.renderer.frame_time
      frames_to_render = int(round(how_long / frame_how_long))
      
      if frames_to_render > 0:
        frame_how_many = how_many / frames_to_render
        leftover_timesteps = how_many % frames_to_render
      else:
        leftover_timesteps = how_many
      
      for i in range(frames_to_render):
        self._run_time_internal(frame_how_many)
        self.renderer.render(self.data)
      if leftover_timesteps > 0:
        self._run_time_internal(leftover_timesteps)
        self.renderer.render(self.data)
      
    else:
      if how_many <= 0:
        return
      self._run_time_internal(how_many)
  
  def _update_particles_from_lammps(self):
    for e in self.data['elements']:
      e.update_from_lammps(self.timesteps_run[-1] * self.data['params']['force_model']['timestep'])
  
  def _update_lammps_from_python(self):
    for e in self.data['elements']:
      e.overwrite_lammps()
  
  def _run_commands(self, commands):
    for c in commands:
      if self.show_lammps_input:
        print "INPUT>",c
      self.lmp.command(c)
  
  def update_gravity(self, g):
    """allows you to change size/direction of gravity mid-simulation."""
    self._run_commands(['unfix grav'])
    self.data['params']['force_model']['gravity'] = g
    self._run_commands([self._generate_gravity_fix()])
  
  def limit_velocities(self, timestep_distance_limit):
    """can be used to bring the system into equilibrium at the end - limiting
velocities to very low values can reduce endless vibration."""
    self._run_commands([
      "unfix update_positions",
      "fix update_positions all nve/limit " + str(timestep_distance_limit)
    ])
  
  def delimit_velocities(self):
    self._run_commands([
      "unfix update_positions",
      "fix update_positions all nve/sphere"
    ])
  
  def close(self):
    """use this method if you want to instantiate a new simulation without
    restarting python."""
    self._run_commands(['clear'])
    self.lmp = None

def _string_sub(string, params):
  for key, value in params.items():
    string = string.replace(key, value)
  return string
