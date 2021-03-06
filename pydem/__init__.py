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

import gzip, cjson, os, math

def vector_length(vector):
  """ arbitrary size cartesean vector length evaluation. """
  return math.sqrt(sum([v_i ** 2 for v_i in vector]))

class JsonContainer:
  def __getitem__(self, key):
    return self.json[key]
  
  def __setitem__(self, key, value):
    self.json[key] = value
    self.validate()
  
  def __delitem__(self, key):
    del self.json[key]
  
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
    'container_height',
    'min_radius',
    'max_mass',
    'min_mass'
  ]
  compulsory_keys = [
    'type',
    'pairwise_constants',
    'boundary_constants',
    'timestep',
    'include_tangential_forces',
    'gravity'
  ]
  keys_for_constants = [
    'spring_constant_norm',
    'damping_norm'
  ]
  keys_for_constants_tangential_only = [
    'spring_constant_tan',
    'damping_tan'
  ]
  
  def is_lazy(self, params):
    """simplistic test whether user is providing proxies or constants."""
    return 'resitiution_coefficient' in params and not 'timestep' in params  
  
  def __init__(self, params):
    self.json = params
    
    if self.is_lazy(params):
      self.validate_lazy(params)
      self.initialise_lazy(params)
    
    self.validate()
  
  def validate_lazy(self, params):
    for key in ForceModel.compulsory_keys_lazy:
      try:
        params[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified.")
  
  def initialise_lazy(self, params):
    if params['type'] == ForceModelType.HOOKIAN:
      self.initialise_lazy_hookian(params)
    else:
      s = """hookian force model initialisation is the only type to have been
      implemented in the wrapper so far - you may specify your own herzian 
      spring/damping values."""
      raise Exception(s)
  
  def initialise_lazy_hookian(self, params):
    self.json['type'] = ForceModelType.HOOKIAN
    
    if 'gravity' not in params:
      self.json['gravity'] = [0.0, -9.8]
    
    self.json['tangential_ratio'] = params['tangential_ratio'] if 'tangential_ratio' in params.keys() else 2.0 / 7.0
    
    # pairwise:
    pairwise_constants = {}
    max_mass = params['max_mass']
    min_mass = params['min_mass']
    
    max_velocity_sq = vector_length(self.json['gravity']) * params['container_height']
    
    self.json['include_drag_force'] = 0
    if params['include_drag_force']:
      max_velocity_sq = max_velocity_sq * (params['terminal_velocity_ratio'] ** 2)
      self.json['include_drag_force'] = 1
      self.json['drag_force_gamma'] = max_mass * vector_length(self.json['gravity']) / math.sqrt(max_velocity_sq)
    
    # max_mass / 2.0 is the max reduced mass
    pairwise_constants['spring_constant_norm'] = (
      (max_mass / 2.0) * max_velocity_sq
    ) / (
      params['min_radius'] * 2.0 * params['max_overlap_ratio']
    ) ** 2
    
    if (params['include_tangential_forces']):
      pairwise_constants['spring_constant_tan'] = pairwise_constants['spring_constant_norm'] * self.json['tangential_ratio']
    
    # 4 reduced to 2, because again reduced mass.
    pairwise_constants['damping_norm'] = math.sqrt(
      (
        2.0 * pairwise_constants['spring_constant_norm'] * min_mass
      ) / (
        1.0 + ((math.log(params['resitiution_coefficient']))/(2.0 * math.pi)) ** 2
      )
    )
    
    if (params['include_tangential_forces']):
      pairwise_constants['damping_tan'] = pairwise_constants['damping_norm'] / 2.0
    
    self.json['pairwise_constants'] = pairwise_constants
    
    # and boundary:
    boundary_constants = {}
    
    boundary_constants['spring_constant_norm'] = (
      (max_mass) * (vector_length(self.json['gravity']) * params['container_height'])
    ) / (
      params['min_radius'] * 2.0 * params['max_overlap_ratio']
    ) ** 2
    
    if (params['include_tangential_forces']):
      boundary_constants['spring_constant_tan'] = boundary_constants['spring_constant_norm'] * self.json['tangential_ratio']
    
    boundary_constants['damping_norm'] = math.sqrt(
      (
        4.0 * boundary_constants['spring_constant_norm'] * min_mass
      ) / (
        1.0 + ((math.log(params['resitiution_coefficient']))/(2.0 * math.pi)) ** 2
      )
    )
    
    if (params['include_tangential_forces']):
      boundary_constants['damping_tan'] = boundary_constants['damping_norm'] / 2.0
    
    self.json['boundary_constants'] = boundary_constants
    
    # estimate shortest collision time, to set timestep to a suitable value.
    min_reduced_mass = min_mass / 2.0
    
    shortest_collision_time = math.pi / math.sqrt(
      pairwise_constants['spring_constant_norm'] / min_reduced_mass -
      (pairwise_constants['damping_norm'] / 2.0 / min_reduced_mass)**2
    )
    
    # we use minimum 30 samples per collision. range 10-100 is acceptable.
    self.json['timestep'] = shortest_collision_time / params['collision_time_ratio']
    
  
  def validate(self):
    for key in ForceModel.compulsory_keys:
      try:
        self.json[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified, or has not been derived.")
    
    compulsory_constants = ForceModel.keys_for_constants[:]
    if self['include_tangential_forces']:
      compulsory_constants.extend(ForceModel.keys_for_constants_tangential_only)
    
    for key in compulsory_constants:
      try:
        self['pairwise_constants'][key]
        self['boundary_constants'][key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' (on force constants) was not specified, or has not been derived.")
        
    

class SimulationParams(JsonContainer):
  """class which holds simulation-wide settings, like the force interactions
     and boundary conditions.
  """
  compulsory_keys = [
    'dimension',
    'x_limit',
    'y_limit',
    'force_model',
    'max_particles_guess'
  ]
  optional_keys = [
    'z_limit'
  ]
  def __init__(self, params=None, force_model_params=None, data=None):
    if 'force_model' not in params and force_model_params != None:
      if 'gravity' not in force_model_params and params['dimension'] == 3:
        force_model_params['gravity'] = [0.0, 0.0, -9.8]
      params['force_model'] = ForceModel(force_model_params)
    self.json = params
    self.json['type'] = 'granular'
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
  
  def to_json(self):
    j = self.json.copy()
    j['force_model'] = j['force_model'].to_json()
    return j


class InvalidArgumentError(ValueError):
  pass

class Particle(JsonContainer):
  """particles, forced to be spherical for now."""
  compulsory_keys = [
    'position',
    'radius',
    'mass',
    'style'
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
    if 'style' not in params:
      self.json['style'] = 'sphere'
    self.validate()
  
  def init_lammps(self, params, write_properties=False, read_properties=False):
    self.lammps = params
    if write_properties:
      self.overwrite_lammps()
    elif read_properties:
      self.update_from_lammps()
  
  def overwrite_lammps(self):
    dimension = len(self.json['position'])
    
    # compulsory keys:
    
    self.lammps['x'][0] = self.json['position'][0]
    self.lammps['x'][1] = self.json['position'][1]
    if dimension > 2:
      self.lammps['x'][2] = self.json['position'][2]
    
    # the two PointerFromArray instances:
    self.lammps['rmass'].assign(self.json['mass'])
    self.lammps['radius'].assign(self.json['radius'])
    
    # optional keys, surrounded by try/excepts:
    
    try:
      self.lammps['v'][0] = self.json['velocity'][0]
      self.lammps['v'][1] = self.json['velocity'][1]
      if dimension > 2:
        self.lammps['v'][2] = self.json['velocity'][2]
    except KeyError:
      self.json['velocity'] = [0.0, 0.0]
      if dimension > 2:
        self.json['velocity'].append(0.0)
      
    
    try:
      if dimension == 2:
        self.lammps['omega'][2] = self.json['angular_velocity']
      else:
        self.lammps['omega'][0] = self.json['angular_velocity'][0]
        self.lammps['omega'][1] = self.json['angular_velocity'][1]
        self.lammps['omega'][2] = self.json['angular_velocity'][2]
    except KeyError:
      self.json['angular_velocity'] = 0.0
      if dimension > 2:
        self.json['angular_velocity'] = [0.0, 0.0, 0.0]
  
  def update_from_lammps(self, delta_t = 0.0):
    dimension = len(self.json['position'])
    
    self.json['position'] = [
      self.lammps['x'][0],
      self.lammps['x'][1]
    ]
    if dimension > 2:
      self.json['position'].append(self.lammps['x'][2])
    
    self.json['velocity'] = [
      self.lammps['v'][0],
      self.lammps['v'][1]
    ]
    if dimension > 2:
      self.json['velocity'].append(self.lammps['v'][2])
    
    self.json['force'] = [
      self.lammps['f'][0],
      self.lammps['f'][1]
    ]
    if dimension > 2:
      self.json['force'].append(self.lammps['f'][2])
    
    # the two PointerFromArray instances:
    self.json['mass'] = self.lammps['rmass'].read()
    self.json['radius'] = self.lammps['radius'].read()
    
    if dimension == 2:
      try:
        new_omega = self.lammps['omega'][2]
        
        average_omega = (self.json['angular_velocity'] + new_omega) / 2.0
        
        self.json['theta'] += delta_t * average_omega
      except KeyError:
        self.json['theta'] = 0.0
      self.json['angular_velocity'] = new_omega 
    else:
      self.json['angular_velocity'] = [
        self.lammps['omega'][0],
        self.lammps['omega'][1],
        self.lammps['omega'][2]
      ]
  
  def validate(self):
    for key in Particle.compulsory_keys:
      try:
        self.json[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified.")
    

def open_system(filename):
  """opens a gzipped json file, in the format created by this library."""
  json_file = gzip.open(filename, 'rb')
  json_string = json_file.read()
  
  # checking for old invalid ' instead of " should be unnecessary, but we leave
  # it in as it's a pain when it prevents a system from loading.
  if json_string.find('\'') != -1:
    json_string = json_string.replace('\'', '\"')
  input_data = cjson.decode(json_string)
  json_file.close()
  
  fm_params = input_data['params']['force_model']
  del input_data['params']['force_model']
  data = {
    'params' : SimulationParams(input_data['params'], fm_params),
    'elements' : [Particle(e) for e in input_data['elements']]
  }
  
  return data

def save_system(data, filename):
  """saves the system in 'data' to a gzipped json format that can be
  restored using open_system.
  """
  if not filename.endswith('.json.gz'):
    filename = filename + '.json.gz'
  
  output_data = {
    'params' : data['params'].to_json(),
    'elements' : [e.to_json() for e in data['elements']]
  }
  outfile = gzip.open(filename , 'wb')
  json_string = cjson.encode(output_data)
  outfile.write(json_string)
  outfile.close()




