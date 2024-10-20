#include "solver.hpp"

GillesPy3D::Solver::Solver(
    sunrealtype t0,
    unsigned long long random_seed,
    GillesPy3D::SpeciesState &species,
    GillesPy3D::ReactionState &reactions,
    GillesPy3D::ParameterState &parameters)
    : t(t0),
      urn(random_seed),
      sol(parameters, species, reactions, urn, 0, 0),
      generator(random_seed),
      species(species),
      reactions(reactions),
      parameters(parameters)
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
}
