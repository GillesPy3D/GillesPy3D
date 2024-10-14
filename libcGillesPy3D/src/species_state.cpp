#include "species_state.hpp"

GillesPy3D::SpeciesState::SpeciesState(const GillesPy3D::ParameterState &parameters)
    : m_parameters(parameters)
{
    // TODO: populate species state initial values
}

std::size_t GillesPy3D::SpeciesState::size()
{
    return m_state.size();
}

void GillesPy3D::SpeciesState::integrate(sunrealtype t, sunrealtype *y, sunrealtype *dydt)
{
    for (std::size_t spec_i = 0; spec_i < size(); ++spec_i)
    {
        dydt[spec_i] = m_diff_equations.at(spec_i).evaluate(t, y);
    }
}
