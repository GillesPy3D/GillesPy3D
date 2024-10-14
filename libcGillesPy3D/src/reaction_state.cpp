#include "reaction_state.hpp"

GillesPy3D::ReactionState::ReactionState(const GillesPy3D::ParameterState &parameters)
    : m_parameters(parameters) {}

std::size_t GillesPy3D::ReactionState::size()
{
    return m_propensity_impl.size();
}

void GillesPy3D::ReactionState::ssa_propensity(sunrealtype *y, sunrealtype *propensities)
{
    for (unsigned int rxn_i = 0; rxn_i < size(); ++rxn_i)
    {
        switch (m_reaction_state[rxn_i]) {
        case SimulationState::DISCRETE:
            // Process stochastic reaction state by updating the root offset for each reaction.
            propensities[rxn_i] = m_propensity_impl.at(rxn_i)(y, m_parameters.data());
            break;

        case SimulationState::CONTINUOUS:
        default:
            propensities[rxn_i] = 0;
            break;
        }
    }
}
