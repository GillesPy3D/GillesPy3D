#include "solver.hpp"
#include "error.hpp"

#include <sstream>

GillesPy3D::Solver::Solver(
    sunrealtype t0,
    GillesPy3D::SolverConfiguration config)
    : t(t0),
      urn(config.random_seed),
      sol(config.parameters, config.species, config.reactions, urn, config.integrator.rel_tol, config.integrator.abs_tol),
      generator(config.random_seed),
      species(config.species),
      reactions(config.reactions),
      parameters(config.parameters)
{
    for (std::size_t spec = 0; spec < species.size(); spec++) {
        num_rate_rules += species.diff_equation(spec).rate_rules.size();

        for (std::size_t r = 0; r < reactions.size(); r++) {
            auto &[reactants_change, products_change] = reactions.change(r);
            if (reactants_change[spec] > 0 || products_change[spec] > 0) {
                non_negative_species.push_back(spec);
                break;// once we flagged it, skip to the next species
            }
        }
    }

    if (!sol.configure(config.integrator))
    {
        std::stringstream ss;
        throw GillesPy3D::GillesPyError((std::stringstream()
            << "Invalid integrator configuration (abstol = "
            << config.integrator.abs_tol
            << ", reltol = " << config.integrator.rel_tol
            << ")").str().c_str());
    }
}
