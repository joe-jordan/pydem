import pydem as d
import pydem.granular as g

# sample options for a monodisperse 3D simulation in a shallow square box.
#
# (note that monodispersity combined with this deposition method tends to give
# the system enough energy to crystallise in spite of tangential friction.)
demo_3d_pack_options = {
  'simulation_params' : {
    'dimension' : 3,
    'x_limit' : 100.0,
    'y_limit' : 100.0,
    'z_limit' : 30.0
  },
  'force_model_params' : {
    'type' : d.ForceModelType.HOOKIAN,
    'resitiution_coefficient' : 0.1,
    'max_overlap_ratio' : 0.1,
    'include_tangential_forces' : True,
    'tangential_ratio' : 0.7
  },
  'element_generation_params' : {
    'min_radius' : 1.0,
    'max_radius' : 1.0,
    'deposition_method' : g.DepositionMethod.RANDOM_SPACED_SHEETS,
    'separation_scaling' : 1.0
  }
}


# sample options for a 2D simulation in a square box.
demo_2d_pack_options = {
  'simulation_params' : {
    'dimension' : 2,
    'x_limit' : 50.0,
    'y_limit' : 50.0
  },
  'force_model_params' : {
    'type' : d.ForceModelType.HOOKIAN,
    'resitiution_coefficient' : 0.5,
    'max_overlap_ratio' : 0.01,
    'include_tangential_forces' : True,
    'tangential_ratio' : 0.9
  },
  'element_generation_params' : {
    'min_radius' : 0.5,
    'max_radius' : 1.0,
    'deposition_method' : g.DepositionMethod.RANDOM_SPACED_SHEETS,
    'separation_scaling' : 0.5
  }
}

print "generating 2d pack..."

system = g.generate_stable_pack(demo_2d_pack_options)

print "done! saving to disk."

d.save_system(system, 'stable_2d_pack')

print "exiting..."

