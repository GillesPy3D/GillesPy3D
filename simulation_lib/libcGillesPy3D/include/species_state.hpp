#pragma once

#include "parameter_state.hpp"
#include "sundials/sundials_types.h"
#include <vector>
#include <functional>

namespace GillesPy3D
{
    /* Gillespy::TauHybrid::DiffEquation
     * A vector containing evaluable functions, which accept integrator state and return propensities.
     *
     * The vector is understood to be an arbitrarily sized collection of propensity evaluations,
     *   each weighted by some individual, constant factor.
     * The sum of evaluations of all collected functions is interpreted to be the dy/dt of that state.
     */
    struct DifferentialEquation
    {
    public:
        std::vector<std::function<double(double*)>> formulas;
        std::vector<std::function<double(double, double*, double*)>> rate_rules;

        double evaluate(double t, double *ode_state, double *parameters) const;
    };

    class SpeciesState
    {
    public:
        SpeciesState(const std::vector<sunrealtype> &initial_populations, const ParameterState &parameters);

        const DifferentialEquation &diff_equation(std::size_t species_id) const;
        std::size_t size() const;
        void integrate(sunrealtype t, sunrealtype *y, sunrealtype *dydt) const;
        void initialize(sunrealtype *out) const;

    private:
        const std::vector<sunrealtype> &m_initial_populations;
        const ParameterState &m_parameters;
        const std::vector<sunrealtype> m_state;
        const std::vector<DifferentialEquation> m_diff_equations;
    };

}
