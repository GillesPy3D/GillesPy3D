#pragma once

#include "species_state.hpp"
#include "reaction_state.hpp"
#include "integrator.hpp"

#include "sundials/sundials_types.h"
#include <vector>
#include <random>

namespace GillesPy3D
{

    struct SolverConfiguration
    {
        unsigned long long random_seed;
        IntegratorConfiguration integrator;
        SpeciesState &species;
        ReactionState &reactions;
        ParameterState &parameters;
    };

    struct Solver
    {
        Solver(sunrealtype t0, SolverConfiguration config);

    private:
        sunrealtype t;
        Integrator sol;
        std::mt19937_64 generator;
        GillesPy3D::URNGenerator urn;
        std::vector<sunrealtype> current_state;
        int num_rate_rules = 0;
        int num_species;
        int num_reactions;
        SpeciesState &species;
        ReactionState &reactions;
        ParameterState &parameters;
        std::vector<std::size_t> non_negative_species;
    };

}
