import pydem as d
import pydem.dem as l
import pprint, random, math

def rand_float(minimum, maximum):
  from_system = random.random()
  scale = maximum - minimum
  return minimum + scale * from_system


def generate_elements(min_radius=0.5, max_radius=1.0, y_line=6.0, x_limit=7.0, gap_scale=1.0):
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

limits = [100.0, 100.0]

elements = generate_elements(y_line=13.0, x_limit=limits[0])

print elements[0].to_json()

data = {'elements':elements}

fm = {
  'type' : d.ForceModelType.HOOKIAN,
  'resitiution_coefficient' : 0.2,
  'max_overlap_ratio' : 0.1,
  'collision_time_ratio' : 30.0,
  'include_tangential_forces' : True,
  'container_height' : limits[1]
}

data['params'] = d.SimulationParams({
  'dimension' : 2,
  'x_limit' : limits[0],
  'y_limit' : limits[1]
}, fm, data)


print l.run_simulation(data)


