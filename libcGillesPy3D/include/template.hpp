#pragma once

#include "particle_system.hpp"

namespace GillesPy3D
{
    PropensityFun *ALLOC_propensities(void);
    void FREE_propensities(PropensityFun* ptr);
    ChemRxnFun* ALLOC_ChemRxnFun(void);
    void FREE_ChemRxnFun(ChemRxnFun* ptr);
    void init_create_particle(ParticleSystem *sys, unsigned int id, double x, double y, double z, int type, double nu, double mass, double c, double rho, int solidTag, int num_chem_species);
    int init_all_particles(ParticleSystem *sys);
    void applyBoundaryConditions(Particle* me, ParticleSystem* system)
}
