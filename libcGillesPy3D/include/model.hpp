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
        std::vector<Parameter> listOfParameters;
        std::vector<Reaction> listOfReactions;
        std::vector<InitialCondition> listOfInitialConditions;
        std::vector<DataFunction> listOfDataFunctions;
        std::vector<BoundaryCondition> listOfBoundaryConditions;
        Domain domain;
        Timespan timespan;
    public:
        Model(const std::string & name="");

        void add_reaction(const std::vector<Reaction> &reaction);
        void add_parameter(const std::vector<Parameter> &parameter);
        void add_species(const std::vector<Species> &species);
        void add_initial_condition(const std::vector<InitialCondition> &initial_condition);
        void add_data_function(const std::vector<DataFunction> &data_function);
        void add_boundary_condition(const std::vector<BoundaryCondition> &boundary_condition);

        void add_domain(const Domain &domain);          // can't add more than one domain
        void add_timespan(const Timespan &timespan);    // can't add more than one timespan

        Simulation *get_simulation_object(); // should this be replaced by passing the model object to the Simulation constructor?

        void run();  // Run needs to either take a path parameter to output VTK files, or return a result object

    };

}
