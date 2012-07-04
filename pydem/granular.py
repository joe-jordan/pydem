# 
# pydem/granular.py : tools for generating stable granular packs.
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

import pydem as d
import pydem.dem as l
import random, time, math, os

class DepositionMethod:
  RANDOM_SPACED_SHEETS = 0

class Dispersity:
  POLYDISPERSE = 0  
  MONODISPERSE = 1
  BIDISPERSE = 2
  
  def validate(self):
    if not self.d in [
      Dispersity.POLYDISPERSE,
      Dispersity.MONODISPERSE,
      Dispersity.BIDISPERSE
    ]:
      raise Exception('not a recognised dispersity.')
  
  def __init__(self, element_generation_params):
    self.d = element_generation_params['dispersity']
    self.min_r = element_generation_params['min_radius']
    self.max_r = element_generation_params['max_radius']
    
    self.validate()
    
    if self.d == Dispersity.POLYDISPERSE:
      self.generate_radius = self._p
    elif self.d == Dispersity.MONODISPERSE:
      self.generate_radius = self._m
    elif self.d == Dispersity.BIDISPERSE:
      self.generate_radius = self._b
  
  def _p(self):
    return rand_float(self.min_r, self.max_r)
  
  def _m(self):
    return self.min_r
  
  def _b(self):
    if random.randint(0, 1):
      return self.max_r
    return self.min_r

def rand_float(minimum, maximum):
  from_system = random.random()
  scale = maximum - minimum
  return minimum + scale * from_system


def generate_element_line(options, simulation_options, existing_elements):
  min_radius = options['min_radius']
  max_radius = options['max_radius']
  
  y_line = max_radius * 3.0
  if len(existing_elements) > 0:
    y_line += max([e['position'][1] for e in existing_elements])
  
  
  x_limit = simulation_options['x_limit']
  gap_scale = options['separation_scaling']
  
  x_pos = 0.0
  previous_radius = 0.0
  
  new_elements = []
  
  while True:
    new_radius = rand_float(min_radius, max_radius)
    gap_width = gap_scale * rand_float(max_radius / 5.0, max_radius)
    
    if (x_pos + previous_radius + (2.0 * new_radius) + gap_width) < x_limit:
      x_pos += previous_radius + new_radius + gap_width
      new_elements.append(d.Particle({
        'position': [x_pos, y_line],
        'radius': new_radius,
        'mass' : (math.pi * new_radius ** 2)
      }))
      previous_radius = new_radius
    else:
      break
  
  return new_elements

def generate_element_sheet(options, simulation_options, existing_elements):
  min_radius = options['min_radius']
  max_radius = options['max_radius']
  
  z_line = max_radius * 3.0
  if len(existing_elements) > 0:
    z_line += max([e['position'][2] for e in existing_elements])
  
  x_limit = simulation_options['x_limit']
  row_separation = max_radius * 3.0
  y_limit = simulation_options['y_limit']
  gap_scale = options['separation_scaling']
  
  y_line = 0.0
  previous_radius = 0.0
  
  new_elements = []
  
  while True:
    y_line += row_separation
    x_pos = 0.0
    
    if y_line + row_separation > y_limit:
      break
    
    while True:
      new_radius = rand_float(min_radius, max_radius)
      gap_width = gap_scale * rand_float(max_radius / 5.0, max_radius)
      
      if (x_pos + previous_radius + (2.0 * new_radius) + gap_width) < x_limit:
        x_pos += previous_radius + new_radius + gap_width
        new_elements.append(d.Particle({
          'position': [x_pos, y_line, z_line],
          'radius': new_radius,
          'mass' : (math.pi * new_radius ** 2)
        }))
        previous_radius = new_radius
      else:
        break
  
  return new_elements

def generate_elements(options, simulation_options, existing_elements):
  if options['deposition_method'] == DepositionMethod.RANDOM_SPACED_SHEETS:
    if simulation_options['dimension'] == 2:
      return generate_element_line(options, simulation_options, existing_elements)
    else:
      return generate_element_sheet(options, simulation_options, existing_elements)
  else:
    raise Error('cannot use unknown deposition method.')

def fill_criterion(data):
  vertical = 1
  key = 'y_limit'
  if data['params']['dimension'] == 3:
    vertical = 2
    key = 'z_limit'
  return max([e['position'][vertical] for e in data['elements']]) + 4.0 > data['params'][key]

def modulus(v):
  return math.sqrt(sum([i**2 for i in v]))

def run_to_equilibrium(simulation, system):
  """now run to equilibrium by limiting particle velocities allow the system to
relax."""
  vertical_key = 'y_limit'
  if system['params']['dimension'] == 3:
    vertical_key = 'z_limit'
  
  theoretical_max_velocity = math.sqrt(2.0 * modulus(system['params']['force_model']['gravity']) * system['params'][vertical_key])
  
  current_max_velocity = max([modulus(e['velocity']) for e in system['elements']])
  travel_limit =  current_max_velocity / 10.0 * system['params']['force_model']['timestep']
  
  # our exist condition is that the travel limit (based on the current system KE)
  # is equivalent to 10^-15 of the velocity obtained by dropping from the top of
  # the container; the max possible in the system. 
  while travel_limit > theoretical_max_velocity * (10.0 ** -15) * system['params']['force_model']['timestep']:
    simulation.limit_velocities(travel_limit)
    simulation.run_time(1)
    initial_kinetic_energy = starting_kinetic_energy = simulation.compute_energy(l.Simulation.KINETIC)
    
    while True:
      simulation.run_time(3.0)
      new_kinetic_energy = simulation.compute_energy(l.Simulation.KINETIC)
      
      # when the rate of energy loss starts slowing, drop the velocity limit more. 
      if abs(starting_kinetic_energy - new_kinetic_energy) < (initial_kinetic_energy / 100):
        break
      
      starting_kinetic_energy = new_kinetic_energy
    
    current_max_velocity = max([modulus(e['velocity']) for e in system['elements']])
    
    travel_limit =  current_max_velocity / 10.0 * system['params']['force_model']['timestep']


def generate_params(inputs=None):
  options = {
    'simulation_params' : {
      'dimension' : 3,
      'x_limit' : 50.0,
      'y_limit' : 50.0,
      'z_limit' : 50.0,
      'max_particles_guess' : 200
    },
    'force_model_params' : {
      'type' : d.ForceModelType.HOOKIAN,
      'resitiution_coefficient' : 0.1,
      'max_overlap_ratio' : 0.1,
      'collision_time_ratio' : 100.0,
      'include_tangential_forces' : True,
      'tangential_ratio' : 0.7
    },
    'element_generation_params' : {
      'min_radius' : 0.5,
      'max_radius' : 1.0,
      'deposition_method' : DepositionMethod.RANDOM_SPACED_SHEETS,
      'separation_scaling' : 1.0
    }
  }
  
  # update options from what was passed in by caller:
  if inputs:
    for paramset in options.keys():
      for key, value in inputs[paramset].items():
        options[paramset][key] = value
  
  dimension = options['simulation_params']['dimension']
  vertical_index = 1
  vertical_key = 'y_limit'
  
  if dimension == 3:
    vertical_index = 2
    vertical_key = 'z_limit'
  else:
    del options['simulation_params']['z_limit']
  
  options['force_model_params']['min_radius'] = options['element_generation_params']['min_radius']
  options['force_model_params']['max_mass'] = math.pi * options['element_generation_params']['max_radius'] ** 2 
  options['force_model_params']['min_mass'] = math.pi * options['element_generation_params']['min_radius'] ** 2
  
  # update the force model's container_height from simulation params:
  options['force_model_params']['container_height'] = options['simulation_params'][vertical_key]
  
  return d.SimulationParams(options['simulation_params'], options['force_model_params'])
  


def generate_stable_pack(params=None):
  """Generates a granular pack in equilibrium. arguments:
  params = a dict of options for the simulation. read the source to see what
           defaults are there to override - there are lots, all at the top.
this function *returns* the new system - the caller must save it to disk. 
"""
  system = {
    'params' : generate_params(params),
    'elements' : generate_elements(params['element_generation_params'], params['simulation_params'], []) 
  }
  
  simulation = l.Simulation(system)
  
  start = time.clock()
  simulation.run_time(5.0)
  
  # fill the box
  while not fill_criterion(system):
    # TODO update generate call.
    simulation.add_particles(generate_elements(params['element_generation_params'], params['simulation_params'], system['elements']))
    simulation.run_time(5.0)
  
  # now allow to settle to low velocities (note the comparison is on v^2..):
  while max([sum([val ** 2 for val in e['velocity']]) for e in system['elements']]) > 0.000001:
    simulation.run_time(20.0)
  
  run_to_equilibrium(simulation, system)
  
  end = time.clock()
  
  system['params']['time_to_completion'] = end - start
  
  return system
