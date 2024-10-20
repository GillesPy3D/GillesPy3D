#include "species_state.hpp"

double GillesPy3D::DifferentialEquation::evaluate(double t, double *ode_state, double *parameters) const
{
    double sum = 0.0;

    for (auto &rate_rule : rate_rules)
    {
        sum += rate_rule(t, ode_state, parameters);
    }

    for (auto &formula : formulas)
    {
        sum += formula(ode_state);
    }

    return sum;
}

GillesPy3D::SpeciesState::SpeciesState(
    const std::vector<sunrealtype> &initial_populations,
    const GillesPy3D::ParameterState &parameters)
    : m_initial_populations(initial_populations),
      m_parameters(parameters),
      m_state(initial_populations) {}

const GillesPy3D::DifferentialEquation &GillesPy3D::SpeciesState::diff_equation(std::size_t species_id) const
{
    return m_diff_equations[species_id];
}

std::size_t GillesPy3D::SpeciesState::size() const
{
    return m_state.size();
}

void GillesPy3D::SpeciesState::integrate(sunrealtype t, sunrealtype *y, sunrealtype *dydt) const
{
    for (std::size_t spec_i = 0; spec_i < size(); ++spec_i)
    {
        dydt[spec_i] = m_diff_equations.at(spec_i).evaluate(t, y, m_parameters.data());
    }
}

void GillesPy3D::SpeciesState::initialize(sunrealtype *out) const
{
    std::copy(m_initial_populations.begin(), m_initial_populations.end(), out);
}
