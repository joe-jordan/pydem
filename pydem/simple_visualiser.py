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
  
  def __init__(self, data, pixel_density=80):
    if SimulationRenderer.instance != None:
      print "err, you tried to create a second SimulationRenderer - pygame only supports one display at a time."
      return
    
    self.pixel_density = pixel_density
    
    SimulationRenderer.instance = self
    
    pygame.init()
    pygame.display.init()
    
    self.white = pygame.Color('#FFFFFF')
    self.black = pygame.Color('#000000')
    
    self.render_surface = pygame.display.set_mode(
      (
        self.pixel_density * int(math.ceil(data['params']['x_limit'])),
        self.pixel_density * int(math.ceil(data['params']['y_limit']))
      )
    )
    
    self.last_rendered = 0
    
    self.render(data)
    
  def render(self, data):
    
    elements = data['elements']
    y_limit = data['params']['y_limit']
    
    current_radius = 0.0
    current_x = 0.0
    current_y = 0.0
    
    try:
      self.render_surface.fill(self.white)
    
      # note, y coords on screen are upside down.
      for e in elements:
        current_radius = int(round(self.pixel_density * e.json["radius"]))
        current_x = int(round(self.pixel_density * e["position"][0]))
        current_y = int(round(self.pixel_density * (y_limit - e["position"][1])))
        pygame.gfxdraw.aacircle(
          self.render_surface,
          current_x,
          current_y,
          current_radius,
          self.black
        )
    
      pygame.display.flip()
      self.last_rendered = pygame.time.get_ticks()
      
    except:
      #just give up on rendering this frame...
      print "caught a rendering exception, on radius " + str(current_radius) + " and x " + str(current_x) + " and y " + str(current_y)
      raise
