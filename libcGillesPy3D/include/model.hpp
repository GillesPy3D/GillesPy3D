#pragma once

#include "particle_system.hpp"
#include "simulation.hpp"

namespace GillesPy3D
{

    class Model
    {
    public:
        Model();

        void add_reaction();
        void add_parameter();
        void add_species();
        void add_timespan();
        void add_initial_condition();
        void add_data_function();
        void add_boundary_condition();
        void add_domain();

        ParticleSystem *get_initial_state();

        void run();
        Simulation *get_simulation_object();
    };

}
