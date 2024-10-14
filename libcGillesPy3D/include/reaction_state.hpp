#pragma once

#include "parameter_state.hpp"
#include "model_context.hpp"
#include <sundials/sundials_types.h>
#include <vector>
#include <tuple>

namespace GillesPy3D
{

    class ReactionState
    {
    public:
        explicit ReactionState(const ParameterState &parameters);
        std::size_t size();
        void ssa_propensity(sunrealtype *y, sunrealtype *propensities);
        SimulationState mode(std::size_t reaction_id);

    private:
        const ParameterState &m_parameters;
        const std::vector<SimulationState> m_reaction_state;
        const std::vector<UniquePropensityFunction<sunrealtype>> m_propensity_impl;
    };

}
