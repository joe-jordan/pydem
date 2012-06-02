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

class DepositionMethod:
  RANDOM_SPACED_SHEETS = 0


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


def generate_stable_pack(params=None):
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
  if params:
    for paramset in options.keys():
      for key, value in params[paramset].items():
        options[paramset][key] = value
  
  dimension = options['simulation_params']['dimension']
  
  # update the force model's container_height from simulation params:
  options['force_model_params']['container_height'] = options['simulation_params']['y_limit'] if dimension == 2 else options['simulation_params']['z_limit']
  
  # generate the first row/layer of grains:
  elements = generate_elements(options['element_generation_params'], options['simulation_params'], [])
  data = {'elements' : elements}
  
  # construct the simulation params instance and the force model in one fell swoop.
  data['params'] = d.SimulationParams(options['simulation_params'], options['force_model_params'], data)
  
  s = l.Simulation(data)
  
  # TODO.
  
  
  
  
  
  
  
  
  
  
  
  
  
  
