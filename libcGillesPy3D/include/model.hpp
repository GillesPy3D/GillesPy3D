#pragma once

#include "particle_system.hpp"
#include "simulation.hpp"
#include "species.hpp"
#include "parameter.hpp"
#include "reaction.hpp"
#include "timespan.hpp"
#include "initial_condition.hpp"
#include "data_function.hpp"
#include "boundary_condition.hpp"
#include "domain.hpp"
#include <string>
#include <vector>

namespace GillesPy3D
{

    class Model
    {
    private:
        std::string name;
        std::vector<Species> listOfSpecies;
    public:
        Model(const std::string & name="");

        void add_reaction(const Reaction &reaction);
        void add_parameter(const Parameter &parameter);
        void add_species(const std::vector<Species> &species);
        void add_timespan(const Timespan &timespan);
        void add_initial_condition(const InitialCondition &initial_condition);
        void add_data_function(const DataFunction &data_function);
        void add_boundary_condition(const BoundaryCondition &boundary_condition);
        void add_domain(const Domain &domain);
        void run();
        Simulation *get_simulation_object();
    };

}
