import pydem as d
import pydem.dem as l
import pydem.simple_visualiser as v
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

def total_energy(data):
  # potential (from heights):
  pe = sum([e['position'][1]*e['mass'] for e in data['elements']]) * abs(data['params']['force_model']['gravity'][1])
  
  # TODO potential (from overlaps) (requires contact detection to be efficient for large systems...):
  
  # kinetic:
  ke = sum([sum([v_i ** 2 for v_i in e['velocity']]) * e['mass'] for e in data['elements']]) * 0.5
  # TODO rotational kinetic
  
  return ke + pe

limits = [50.0, 50.0]

elements = generate_elements(y_line=13.0, x_limit=limits[0])

data = {'elements':elements}

fm = {
  'type' : d.ForceModelType.HOOKIAN,
  'resitiution_coefficient' : 0.2,
  'max_overlap_ratio' : 0.1,
  'collision_time_ratio' : 100.0,
  'include_tangential_forces' : True,
  'container_height' : limits[1]
}

data['params'] = d.SimulationParams({
  'dimension' : 2,
  'x_limit' : limits[0],
  'y_limit' : limits[1],
  'max_particles_guess' : 200
}, fm, data)

s = l.Simulation(data)

r = v.SimulationRenderer(data, 20)

frame_rate = 50.0

frame_time = 1.0 / frame_rate

run_time = 0.0

while (run_time < 5.0):
  s.run_time(frame_time)
  run_time += frame_time
  r.render(data)

while len(data['elements']) < 500:
  print "ran successfully, now adding more elements"
  
  print "energy before adding new elements:", total_energy(data)
  
  s.add_particles(generate_elements(y_line=max([e['position'][1] for e in data['elements']])+3.0, x_limit=limits[0]))
  
  print "energy after adding new elements:", total_energy(data)
  
  run_time = 0.0
  
  while (run_time < 5.0):
    s.run_time(frame_time)
    run_time += frame_time
    r.render(data)

print "successfully ran time for even longer, final energy:", total_energy(data)
