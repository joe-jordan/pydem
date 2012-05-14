PYDEM
=====
 
*python bindings for granular DEM simulations.*

Useful Links:
-------------

The [LAMMPS](http://lammps.sandia.gov/) simulator project.

[Pygame](http://www.pygame.org/), an optional dependency for simple visualisations.

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

**NOTE** this version does NOT support MPI parallel computations - they might work, but I have little desire to test them! This library will be bundled with a tool for running multiple simulations at once, as an alternative to this functionality, at a later date.

Future Versions
---------------

*CANCELLED*
**Version 1** aims to implement this by generating very simple LAMMPS scripts, calling them using `os.system()`, and retrieving the data dump files and parsing them for you.
Since the ultimate aim is to avoid the domain speific LAMMPS language, this version will not support constraints, tests or loops in LAMMPS; it will run one granular simulation for a specified number of timesteps and then scoop up the data.

*NEW TARGET*
**Version 2** will use a simple C interface combined with Cython to expose a well defined set of functionality for passing data between Python and C++ land.
It will also provide an interface for using LAMMPS `compute` functionality, although the results of computes will be passed all the way out to Python for processing and mid-simulation logic, so that one can use rich language features to `if` and `elif`, loop and `raise`, `map` and `reduce`. Note that you'll still be able to do this in version 1, it'll just be a lot slower, and you'll have to implement your own `compute`s.

**Version 3** will support aspherical particles in a similar way to LIGGGHTS - i.e. via coupled/rigid sets of spheres.


Installation Instructions:
--------------------------

*These instruction are for Mac and Linux (tested on a mac, so if you find a Linux bug do report it on github!) If you're on Windows, all I can suggest is that you try installing cygwin.*

Building LAMMPS is big and complicated and tricky, they have a whole documentation section devoted to it; but fear not! it is slightly simpler to do, if you only want support as a python library.

1) install the GRANULAR module

    cd lammps-checkout/src
    make yes-granular

2) *for now* apply my patches

    cd ..
    patch -p0 -i pydem-checkout-path/patches/bypass_evnvar_hacks_requirement.diff
    patch -p0 -i pydem-checkout-path/patches/support_for_more_extract_atom_keywords.diff

(where `pydem-checkout-path` is a valid path to a checkout of this project, obviously.)

3) run make at least once - this is required so that some header files are in the right place. it doesn't need to succeed.

    cd src
    
    # e.g. for mac:
    make mac
    
    # or linux:
    make serial
    
    # either of these will be followed by loads of output from make and gcc.

(type `make` for a full list of makefiles included.)

4) install lammps python module as usual using `setup.py` (note, I tend to do this in two steps so that the temporary build files are not owned by root, which is annoying to clean up later.)

    cd ../python
    python setup_serial.py build
    
    # (expect a load more compiler output)
    
    sudo python setup_serial.py install

5) Finally, you're ready to install *my* python bindings! Same drill as the last step:

    cd pydem-checkout-path
    python setup.py build
    sudo python setup.py install

You're now ready to test it all using my example script for a 2D simulation with visualisations (which requires `pygame`, which comes with oneclick installers for most platforms.)

    # never run scripts in a module's build directory (because shenanigans...)
    cp test_run.py ~/
    cd ~
    python test_run.py

Take a peek inside `test_run.py` to see the key classes in action, and an example energy evaluation function.
