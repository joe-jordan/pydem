PYDEM
=====
 
*python bindings for granular DEM simulations.*

Basics
------

This is an as-yet-unstable set of python bindings for LAMMPS, created because I couldn't get the ctypes-based python to work, and because ultimately I want a better interface than that!

All versions will operate in approximately the following way:

* allow you to `import` a normal python module
* allow you to initialise data (like interactions, particle positions, boundary conditions, etc) *in python*.
* allow you to run the simulation, and retrieve the data in memory afterwards,
* allow you to save and restore the particles in compressed form.

*in fact, it looks like the python/C++ data transfer will be encapsulated within ordinary operations on the interface, with fallback to manual controls if you're feeling technical.*

This Version
------------

We are currently at VERSION 0 - that is, version 1 isn't finished yet. Version 0 doesn't work at all. It's just a plan of the interface and some broken methods.

**UPDATE** In fact, we're skipping version one and jumping straight to a sort of version 2. We are still generating a lammps script, but we're pushing it through a line at a time into the programmatic command interface, and we're setting atom data using pointers passed out of the C++, rather than either lammps commands or data files.

Future Versions
---------------

*CANCELLED*
**Version 1** aims to implement this by generating very simple LAMMPS scripts, calling them using `os.system()`, and retrieving the data dump files and parsing them for you.
Since the ultimate aim is to avoid the domain speific LAMMPS language, this version will not support constraints, tests or loops in LAMMPS; it will run one granular simulation for a specified number of timesteps and then scoop up the data.

*NEW TARGET*
**Version 2** will use a simple C interface combined with Cython to expose a well defined set of functionality for passing data between Python and C++ land.
It will also provide an interface for using LAMMPS `compute` functionality, although the results of computes will be passed all the way out to Python for processing and mid-simulation logic, so that one can use rich language features to `if` and `elif`, loop and `raise`, `map` and `reduce`. Note that you'll still be able to do this in version 1, it'll just be a lot slower, and you'll have to implement your own `compute`s.

**Version 3** might head over to LAMMPS' cousin LIGGGHTS and expose some of the extra granular features there to similar Cythonic treatment.
