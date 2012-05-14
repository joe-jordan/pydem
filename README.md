PYDEM
=====
 
*python bindings for granular DEM simulations.*

Basics
------

This is a nearly-stable set of python bindings for LAMMPS, built around the ctypes interface in LAMMPS/src/library.h. It currently requires a few small patches to the LAMMPS code, which I will provide as a patch file here until they are accepted into the stable lammps release.

All versions will operate in approximately the following way:

* allow you to `import` a normal python module
* allow you to initialise data (like interactions, particle positions, boundary conditions, etc) *in python*.
* allow you to run the simulation, and retrieve the data in memory afterwards,
* allow you to save and restore the particles in compressed form. *(support for lammps binary restart files will be added, too.)*

*in fact, it looks like the python/C++ data transfer will be encapsulated within ordinary operations on the interface, with fallback to manual controls if you're feeling technical.*

This Version
------------

**PROGRESS REPORT** Version 2 is nearly ready - most features are implemented - next job to debug a few physics issues using a visualiser which uses pygame. This will not be required in the final build - so no broken imports.

This is now Version 2, in alpha. We can run (and visualise in 2D) a granular simulation of polydisperse spheres, although there are some bugs still to be nailed down (see the TODO file for details).

Future Versions
---------------

*CANCELLED*
**Version 1** aims to implement this by generating very simple LAMMPS scripts, calling them using `os.system()`, and retrieving the data dump files and parsing them for you.
Since the ultimate aim is to avoid the domain speific LAMMPS language, this version will not support constraints, tests or loops in LAMMPS; it will run one granular simulation for a specified number of timesteps and then scoop up the data.

*NEW TARGET*
**Version 2** will use a simple C interface combined with Cython to expose a well defined set of functionality for passing data between Python and C++ land.
It will also provide an interface for using LAMMPS `compute` functionality, although the results of computes will be passed all the way out to Python for processing and mid-simulation logic, so that one can use rich language features to `if` and `elif`, loop and `raise`, `map` and `reduce`. Note that you'll still be able to do this in version 1, it'll just be a lot slower, and you'll have to implement your own `compute`s.

**Version 3** will support aspherical particles in a similar way to LIGGGHTS - i.e. via coupled/rigid sets of spheres.
