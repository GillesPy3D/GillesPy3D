#pragma once

#include "particle_system.hpp"
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


   enum SimulationState : unsigned int
    {
        CONTINUOUS = 0,
        DISCRETE = 1,
        DYNAMIC = 2
    };


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

        void add_reaction(const Reaction &reaction);
        const std::vector<Reaction> &get_reactions() const;
        void add_parameter(const Parameter &parameter);
        void add_species(Species &species);
        void add_initial_condition(const InitialCondition &initial_condition);
        void add_data_function(const DataFunction &data_function);
        void add_boundary_condition(const BoundaryCondition &boundary_condition);
        void add_domain(const Domain &domain);          // can't add more than one domain
        void add_timespan(const Timespan &timespan);    // can't add more than one timespan

        void run();  // Run needs to either take a path parameter to output VTK files, or return a result object

    };

}
