#include "model_context.hpp"

GillesPy3D::ModelContext::ModelContext(GillesPy3D::Model &model)
    : reaction_context(model)
{

}

double GillesPy3D::ReactionContext::get_propensity_sum(double *state, double *parameters)
{
    double result = 0.0f;
    for (auto const &[reaction_id, propensity] : ode_propensity_map) {
        result += propensity(state, parameters);
    }
    return result;
}

GillesPy3D::CPropensityFunction::CPropensityFunction(double (*propensity_function)(double*, double*))
    : propensity_function(propensity_function)
{
    
}

GillesPy3D::ReactionContext &GillesPy3D::ModelContext::reactions()
{
    return reaction_context;
}

GillesPy3D::ReactionContext::ReactionContext(GillesPy3D::Model &model)
{
    for (std::size_t reaction_id = 0; reaction_id < model.get_reactions().size(); ++reaction_id) {
        const GillesPy3D::Reaction &reaction = model.get_reactions().at(reaction_id);
        reaction_id_map[reaction.get_name()] = reaction_id;
    }
}

std::size_t GillesPy3D::ReactionContext::get_reaction_id(const std::string &reaction_name) const
{
    return reaction_id_map.at(reaction_name);
}

std::size_t GillesPy3D::ReactionContext::get_reaction_id(const GillesPy3D::Reaction &reaction) const
{
    return get_reaction_id(reaction.get_name());
}

void GillesPy3D::ReactionContext::set_propensity_function(std::size_t reaction_id, const GillesPy3D::CPropensityFunction &propensity_function)
{
    set_ssa_propensity_function(reaction_id, propensity_function);
    set_ode_propensity_function(reaction_id, propensity_function);
}

void GillesPy3D::ReactionContext::set_ode_propensity_function(std::size_t reaction_id, const GillesPy3D::CPropensityFunction &propensity_function)
{
    set_ode_propensity_function(reaction_id, propensity_function.propensity_function);
}

void GillesPy3D::ReactionContext::set_ssa_propensity_function(std::size_t reaction_id, const GillesPy3D::CPropensityFunction &propensity_function)
{
    set_ssa_propensity_function(reaction_id, propensity_function.propensity_function);
}

void GillesPy3D::ReactionContext::set_ssa_propensity_function(std::size_t reaction_id, double (*propensity_function)(double*, double*))
{
    ssa_propensity_map[reaction_id] = propensity_function;
}

void GillesPy3D::ReactionContext::set_ode_propensity_function(std::size_t reaction_id, double (*propensity_function)(double*, double*))
{
    ode_propensity_map[reaction_id] = propensity_function;
}
