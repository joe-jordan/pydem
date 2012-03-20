# 
# pydem/__init__.py : pydem's main entry points
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

import gzip, cjson, os, lammps, math

def vector_length(vector):
  """ arbitrary size cartesean vector length evaluation. """
  return math.sqrt(sum([v_i ** 2 for v_i in vector]))

class JsonContainer:
  def __getitem__(self, key):
    return self.json[key]
  
  def __setitem__(self, key, value):
    self.json[key] = value
    self.validate()
    
  def to_json(self):
    return self.json

class Endpoint:
  EQUILIBRIUM = 1
  TIMESTEP_LIMIT = 2

class ForceModelType:
  HOOKIAN = 1
  HERZIAN = 2

class ForceModel(JsonContainer):
  """A class encapsulating the hookian and hertzian intergranular force models.
     to build, specify the constants directly, or give proxies like the maximum
     acceptable particle overlap and restitution coefficient.
  """
  compulsory_keys_lazy = [
    'type',
    'resitiution_coefficient',
    'max_overlap_ratio',
    'collision_time_ratio',
    'include_tangential_forces',
    'gravity',
    'container_height'
  ]
  compulsory_keys_specific = [
    'type',
    'pairwise_constants',
    'boundary_constants',
    'timestep',
    'include_tangential_forces',
    'gravity'
  ]
  keys_for_constants = [
    'spring_constant_norm',
    'damping_norm',
    'spring_constant_tan',
    'damping_tan'
  ]
  
  def is_lazy(self, params):
    """simplistic test whether user is providing proxies or constants."""
    return 'restitution_coefficient' in params and not 'timestep' in params  
  
  def __init__(self, params, data):
    if not self.is_lazy(params):
      self.json = params
    else:
      self.initialise_lazy(params, data)
    
    self.validate(data)
  
  def initialise_lazy(self, params, data):
    if params['type'] == ForceModelType.HOOKIAN:
      self.initialise_lazy_hookian(params, data)
    else:
      raise Exception('hookian force model initialisation is the only type to have been implemented in the wrapper so far - you may specify your own herzian spring/damping values.')
  
  def initialise_lazy_hookian(self, params, data):
    
    self.json = {
      'type' : ForceModelType.HOOKIAN,
      'pairwise_constants' : {},
      'boundary_constants' : {},
      'include_tangential_forces' : 1,
      'gravity' : [0.0, -9.8]
    }
    
    # pairwise:
    pairwise_constants = {}
    max_mass = max([e['mass'] for e in data['elements']])
    
    # max_mass / 2.0 is the max reduced mass, and height * g is max velocity squared.
    pairwise_constants['spring_constant_norm'] = (
      (max_mass / 2.0) * (vector_length(params['gravity']) * params['container_height'])
    ) / (
      min([e['radius'] * 2.0 for e in data['elements']]) * params['max_overlap_ratio']
    ) ** 2
    
    pairwise_constants['spring_constant_tan'] = pairwise_constants['spring_constant_norm'] * 2.0 / 7.0
    
    # 4 reduced to 2, because again reduced mass.
    pairwise_constants['damping_norm'] = math.sqrt(
      (
        2.0 * pairwise_constants['spring_constant_norm'] * max_mass
      ) / (
        1.0 + ((math.log(params['resitiution_coefficient']))/(2.0 * math.pi)) ** 2
      )
    )
    
    pairwise_constants['damping_tan'] = pairwise_constants['damping_norm'] / 2.0
    
    # and boundary:
    boundary_constants = {}
    
    boundary_constants['spring_constant_norm'] = (
      (max_mass) * (vector_length(params['gravity']) * params['container_height'])
    ) / (
      min([e['radius'] * 2.0 for e in data['elements']]) * params['max_overlap_ratio']
    ) ** 2
    
    boundary_constants['spring_constant_tan'] = boundary_constants['spring_constant_norm'] * 2.0 / 7.0
    
    boundary_constants['damping_norm'] = math.sqrt(
      (
        4.0 * boundary_constants['spring_constant_norm'] * max_mass
      ) / (
        1.0 + ((math.log(params['resitiution_coefficient']))/(2.0 * math.pi)) ** 2
      )
    )
    
    boundary_constants['damping_tan'] = boundary_constants['damping_norm'] / 2.0
    
    # estimate shortest collision time, to set timestep to a suitable value.
    min_reduced_mass = min([e['mass'] for e in data['elements']]) / 2.0
    
    shortest_collision_time = math.pi / math.sqrt(
      pairwise_constants['spring_constant_norm'] / min_reduced_mass -
      pairwise_constants['damping_norm']**2 / (4.0 * min_reduced_mass**2)
    )
    
    # we use minimum 30 samples per collision. range 10-100 is acceptable.
    self.json['timestep'] = shortest_collision_time / 30.0
    
  
  def validate(self, data):
    pass

class SimulationParams(JsonContainer):
  """class which holds simulation-wide settings, like the force interactions
     and boundary conditions.
  """
  compulsory_keys = [
    'dimension',
    'x_limit',
    'y_limit',
    'force_model'
  ]
  optional_keys = [
    'z_limit'
  ]
  def __init__(self, params=None):
    self.json = params
    self.validate()
  
  def validate(self):
    local_compulsory = SimulationParams.compulsory_keys[:]
    if self.json['dimension'] > 2:
      local_compulsory.append('z_limit')
    
    for key in local_compulsory:
      try:
        self.json[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified.")
  


class InvalidArgumentError(ValueError):
  pass

class Particle(JsonContainer):
  """particles, forced to be spherical for now."""
  compulsory_keys = [
    'position',
    'radius',
    'mass'
  ]
  optional_keys = [
    'velocity',
    'angular_velocity'
  ]
  def __init__(self, params=None):
    self.json = {}
    if not params == None:
      self.initialise(params)
    
  def initialise(self, params):
    for key, value in params.items():
      self.json[key] = value
    self.validate()
  
  def validate(self):
    for key in Particle.compulsory_keys:
      try:
        self.json[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified.")
    

def open_system(filename):
  json_file = gzip.open(filename, 'rb')
  json_string = json_file.read()
  if json_string.find('\'') != -1:
    json_string = json_string.replace('\'', '\"')
  input_data = cjson.decode(json_string)
  json_file.close()
  data = {
    'params' : input_data['params'].to_json(),
    'elements' : [Particle(e) for e in input_data['elements']]
  }
  return data

def save_system(data, filename):
  output_data = {
    'params' : data['params'].to_json(),
    'elements' : [e.to_json() for e in data['elements']]
  }
  outfile = gzip.open(filename , 'wb')
  json_string = cjson.encode(output_data)
  outfile.write(json_string)
  outfile.close()




