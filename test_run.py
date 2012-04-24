import pydem as d
import pprint

elements = []
for i in xrange(0, 100):
  elements.append(d.Particle({
    'position' : [0.0, 0.0],
    'radius' : 1.0,
    'mass' : 1.0
  }))

data = {'elements':elements}

fm = d.ForceModel({
  'type' : d.ForceModelType.HOOKIAN,
  'resitiution_coefficient' : 0.5,
  'max_overlap_ratio' : 0.1,
  'collision_time_ratio' : 30.0,
  'include_tangential_forces' : True,
  'container_height' : 100.0
}, data)

print "force constants calculated: "
pprint.pprint(fm.json, indent=2)

print "\nexample atom:"
pprint.pprint(elements[0].json)
