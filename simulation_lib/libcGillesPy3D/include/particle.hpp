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


#ifndef particle_hpp
#define particle_hpp

#include "species_state.hpp"
#include "reaction_state.hpp"
#include <vector>

#include "ANN/ANN.h" // ANN KD Tree

extern int debug_flag;

namespace GillesPy3D{

    struct Particle;
    struct ParticleSystem;
    struct NeighborNode;
    struct EventNode;

    struct Particle{
        Particle(ParticleSystem *sys, unsigned int id=0, double xl=0, double yl=0,
                    double zl=0, int type=0, double nu=0.01, double mass=1, double c=0,
                    double rho=1, int solidTag=0);
        ParticleSystem *sys;
        std::vector<NeighborNode> neighbors;
        unsigned int id;
        int type;
        double old_x[3];
        double old_v[3];
        double old_rho;
        double x[3];
        double v[3];
        double vt[3];
        double nu;
        double mass;
        double c;
        double rho;
        int solidTag;
        double bvf_phi;
        double normal[3];
        double F[3];
        double Frho;
        double Fbp[3];
        // Data Function
        //double * data_fn; //TODO
        // chem_rxn_system
        SpeciesState species_state;
        ReactionState reaction_state;
        N_Vector Y_state;  // Integrator State
        N_Vector Y_save;   // Saved Integrator State
        realtype current_time;

        //double *C; // concentration of chem species // ARE THESE USED STILL??
        //double *Q; // flux of chem species
        // below here for simulation

        double save_integrator_state();
        double restore_integrator_state();
        void integrate_forward(double tau_step_size); // "run" function
        double calculate_max_tau_step_size();


        void check_particle_nan();

        double particle_dist(Particle *p2);
        double particle_dist_sqrd(Particle *p2);
        int add_to_neighbor_list(Particle *neighbor, ParticleSystem *system, double r2);

        // KD TREE FUNCTIONS
        void get_k_cleanup(ANNidxArray nn_idx, ANNdistArray dists);
        void search_cleanup(ANNpoint queryPt, ANNidxArray nn_idx, ANNdistArray dists);
        int get_k__approx(ParticleSystem *system);
        int get_k__exact(ANNpoint queryPt, ANNdist dist, ANNkd_tree *tree);
        void find_neighbors(ParticleSystem *system, bool use_exact_k=true);

        bool operator<(const Particle& p2){
            return x[0] > p2.x[0];
        }
    };
}

#endif
