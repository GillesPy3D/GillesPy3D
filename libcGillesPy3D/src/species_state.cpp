#include "species_state.hpp"

GillesPy3D::SpeciesState::SpeciesState(
    const std::vector<sunrealtype> &initial_populations,
    const GillesPy3D::ParameterState &parameters)
    : m_initial_populations(initial_populations),
      m_parameters(parameters),
      m_state(initial_populations) {}

std::size_t GillesPy3D::SpeciesState::size() const
{
    return m_state.size();
}

void GillesPy3D::SpeciesState::integrate(sunrealtype t, sunrealtype *y, sunrealtype *dydt) const
{
    for (std::size_t spec_i = 0; spec_i < size(); ++spec_i)
    {
        dydt[spec_i] = m_diff_equations.at(spec_i).evaluate(t, y);
    }
}

void GillesPy3D::SpeciesState::initialize(sunrealtype *out) const
{
    std::copy(m_initial_populations.begin(), m_initial_populations.end(), out);
}
