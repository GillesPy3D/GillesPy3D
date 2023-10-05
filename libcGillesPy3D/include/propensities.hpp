/**
# GillesPy3D is a Python 3 package for simulation of
# spatial/non-spatial deterministic/stochastic reaction-diffusion-advection problems
# Copyright (C) 2023 GillesPy3D developers.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU GENERAL PUBLIC LICENSE Version 3 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU GENERAL PUBLIC LICENSE Version 3 for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/

#ifndef PROPENSITIES__H
#define PROPENSITIES__H

#include <random>

extern std::mt19937_64 rng;

namespace GillesPy3D{

    /* Global variable that can be used to pass parameters to the propensity functions. */
    extern double *parameters;
    struct Particle ;
    struct ParticleSystem ;

    unsigned int get_next_output(ParticleSystem* system);
    /* Definition of the propensity function. */
    // double rfun(const int *x, double t, const double vol, const double *data, int sd, int voxel, int *xx, const size_t *irK, const size_t *jcK, const double *prK)
    //typedef double (*PropensityFun)(const int *, double, double, const double *, int, int, int *, const size_t *, const size_t *, const double *);
    // double rfun(const int *x, double t, const double vol, const double *data, int sd)
    typedef double (*PropensityFun)(const unsigned int *, double, double, double*, int);
    typedef double (*ChemRxnFun)(double*, double, double, double*, int);

    /* Declaration of allocation and deallocation of propensity list. */
    PropensityFun *ALLOC_propensities(void);
    ChemRxnFun *ALLOC_ChemRxnFun(void);
    void FREE_propensities(PropensityFun* ptr);
    void applyBoundaryConditions(Particle* me, ParticleSystem* system);
}

#endif
/* PROPENSITIES__H */
