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

import gzip, cjson, os, lammps

class Endpoint:
  EQUILIBRIUM = 1
  TIMESTEP_LIMIT = 2

class SimulationParams:
  """note that you must either provide a dict object force model with your parameters, or
     the overlap, restitution and collision ratio parameters.
  """
  compulsory_keys = [
    'dimension',
    'x_limit',
    'y_limit'
  ]
  optional_keys = [
    'z_limit',
    'force_model',
    'resitiution_coefficient',
    'max_overlap_ratio',
    'collision_time_ratio'
  ]
  def __init__(self, params=None):
    self.json = {}
    if not params == None:
      self.initialise(params)
      self.validate()
    
  def initialise(self, params):
    # TODO - set up internal data.
    pass
  
  def __getitem__(self, key):
    return self.json[key]
  
  def __setitem__(self, key, value):
    self.json[key] = value
    self.validate()
  
  def validate(self):
    # TODO adjust compulsory and optional keys on the basis of complex dependency rules.
    for key in SimulationParams.compulsory_keys:
      try:
        self.json[key]
      except KeyError:
        raise InvalidArgumentError("Compulsory property '" + key + "' was not specified.")
  
  def to_json(self):
    return self.json


class InvalidArgumentError(ValueError):
  pass

class Particle:
  """particles, assumed to be spherical for now."""
  compulsory_keys = [
    'position',
    'radius'
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
  
  def to_json(self):
    return self.json
    

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




