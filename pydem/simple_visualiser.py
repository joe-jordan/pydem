# 
# pydem/simple_visualiser.py : pygame based 2D granular visualiser.
# 
# This implementation Copyright (c) Joe Jordan 2011
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

import math
import pygame
import pygame.draw
import pygame.gfxdraw
import pygame.surface
import pygame.display
import pygame.time

class SimulationRenderer:
  instance = None
  vertical = ['y_limit', 1]
  
  def __init__(self, data, pixel_density=80, zoom=None):
    if SimulationRenderer.instance != None:
      print "err, you tried to create a second SimulationRenderer - pygame only supports one display at a time."
      return
    
    self.pixel_density = pixel_density
    
    if zoom != None:
      self.zoom = zoom
    
    SimulationRenderer.instance = self
    
    if data['params']['dimension'] != 2:
      SimulationRenderer.vertical = ['z_limit', 2]
    
    pygame.init()
    pygame.display.init()
    
    self.white = pygame.Color('#FFFFFF')
    self.black = pygame.Color('#000000')
    self.red = pygame.Color('#FF0000')
    
    self.mode = {
      'x' : self.pixel_density * int(math.ceil(data['params']['x_limit'])),
      'y' : self.pixel_density * int(math.ceil(data['params'][SimulationRenderer.vertical[0]]))
    }
    
    self.render_surface = pygame.display.set_mode(
      (
        self.mode['x'],
        self.mode['y']
      )
    )
    
    self.last_rendered = 0
    
    self.render(data)
    
  def render(self, data):
    
    r_scale = 1.0
    x_offset = 0.0
    y_offset = 0.0
    
    try:
      r_scale = data['params']['x_limit'] / self.zoom['width']
      x_offset = self.zoom['x']
      y_offset = self.zoom['y']
    except:
      # we don't mind if self.zoom is not defined.
      pass
    
    elements = data['elements']
    y_limit = data['params'][SimulationRenderer.vertical[0]]
    
    current_radius = 0.0
    current_x = 0.0
    current_y = 0.0
    current_id = 0
    
    try:
      self.render_surface.fill(self.white)
      
      # initialise in case of error on first run.
      current_id = -1
      float_r = -1.0
      float_x = -1.0
      float_y = -1.0
      
      # note, y coords on screen are upside down.
      for i, e in enumerate(elements):
        current_id = i
        float_r = self.pixel_density * e.json["radius"] * r_scale
        current_radius = int(round(float_r))
        float_x = self.pixel_density * (e["position"][0] - x_offset) * r_scale
        current_x = int(round(float_x))
        float_y = self.pixel_density * ((y_limit - e["position"][SimulationRenderer.vertical[1]]) - y_offset) * r_scale
        current_y = int(round(float_y))
        
        # do not draw if zooming and off the screen.
        if hasattr(self, 'zoom') and (
           current_x < -1.0 * current_radius or
           current_y < -1.0 * current_radius or
           current_x > self.mode['x'] + current_radius or
           current_y > self.mode['y'] + current_radius):
          continue
        
        color = self.black
        try:
          if e['different']:
            color = self.red
        except KeyError:
          pass
        
        pygame.gfxdraw.aacircle(
          self.render_surface,
          current_x,
          current_y,
          current_radius,
          color
        )
        
        try:
          e.json['theta']
          pygame.gfxdraw.line(
            self.render_surface,
            current_x,
            current_y,
            int(round(float_x + float_r * math.cos(e.json['theta']))),
            int(round(float_y + float_r * math.sin(e.json['theta']))),
            color
          )
        except KeyError:
          pass
      
      # now draw an arrow indicating the direction of gravity:
      gravity_arrow_length = 50
      g = data['params']['force_model']['gravity']
      theta = math.atan2(-g[1], g[0])
      #arrowhead_rotation = math.degrees(theta)
      
      centre = (self.mode['x'] / 2, self.mode['y'] / 2)
      end = (
        self.mode['x'] / 2 + gravity_arrow_length * math.cos(theta),
        self.mode['y'] / 2 + gravity_arrow_length * math.sin(theta)
      )
      
      pygame.draw.line(self.render_surface, self.black, centre, end, 3)
      
      pygame.display.flip()
      self.last_rendered = pygame.time.get_ticks()
      
    except:
      #just give up on rendering this frame...
      print "caught a rendering exception, on radius", float_r, "and x", float_x, "and y", float_y, "and id", current_id, "and element json:", elements[current_id].json
      print "current number of elements is", len(elements) 
      raise
