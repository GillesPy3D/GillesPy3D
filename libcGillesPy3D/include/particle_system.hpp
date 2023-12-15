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

/* *****************************************************************************
SSA-SDPD simulation engine
Copyright 2018 Brian Drawert (UNCA)

This program is distributed under the terms of the GNU General Public License.
See the file LICENSE.txt for details.
***************************************************************************** */
#ifndef particlesystem_hpp
#define particlesystem_hpp

#include <vector>

#include "ANN/ANN.h" // ANN KD Tree
#include "propensities.hpp"

extern int debug_flag ;

namespace GillesPy3D {


    struct URNGenerator
    {
    private:
        std::uniform_real_distribution<double> uniform;
        std::mt19937_64 rng;
        unsigned long long seed;
    public:
        double next();
        URNGenerator() = delete;
        explicit URNGenerator(unsigned long long seed);
    };


    struct Particle;
    struct ParticleSystem;
    struct NeighborNode;
    struct EventNode;

    struct NeighborNode{
        Particle *data;
        double dist;
        double dWdr;
        double D_i_j;
        NeighborNode(Particle *data, double dist, double dWdr, double D_i_j);

        bool operator<(const NeighborNode& n2){
            return dist > n2.dist;
        }
    };

    struct ParticleSystem{
        ParticleSystem(size_t num_types, size_t num_chem_species, size_t num_chem_rxns,
                         size_t num_stoch_species, size_t num_stoch_rxns,size_t num_data_fn);
        ~ParticleSystem();
        int dimension;
        double dt;
        unsigned int nt;
        unsigned int current_step;
        double xlo, xhi, ylo, yhi, zlo, zhi;
        double h;
        double c0;
        double rho0;
        double P0;
        std::vector<Particle> particles;
        double* parameter_state;  // current state of the rxn system parameters
        URNGenerator urn;


        bool static_domain;
        size_t num_types;

        double* gravity;

        void add_particle(Particle *me);

        ANNkd_tree *kdTree;
        ANNpointArray kdTree_pts;
        bool kdTree_initialized;
    };


}

#endif //particle_h
