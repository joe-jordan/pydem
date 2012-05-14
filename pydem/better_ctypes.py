# 
# pydem/better_ctypes.py : wrapper class for handling global c arrays.
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

class PointerFromArray:
  """it is seemingly impossible to store a pointer(c_int) from an arbitrary
existing position in a heap array passed from a c library via ctypes - 
by using ptr[index] one retrieves the value, not the pointer, and even if one
could store the pointer, assigning to it would overwrite with a new python
object. This class is a rather inelegant solution to this problem."""
  def __init__(self, ctypes_array, index):
    self.array_ptr = ctypes_array
    self.array_index = index
  
  def assign(self, value):
    self.array_ptr[self.array_index] = value
  
  def read(self):
    return self.array_ptr[self.array_index]