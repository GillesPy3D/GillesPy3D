#pragma once

#include "model.hpp"
#include "reaction.hpp"
#include <vector>
#include <map>
#include <unordered_map>
#include <string>
#include <iostream>

namespace GillesPy3D
{
    class ReactionContext;

    class CPropensityFunction
    {
    public:
        friend class ReactionContext;
        explicit CPropensityFunction(double (*propensity_function)(double*, double*));

    private:
        double (*propensity_function)(double*, double*);
    };

    class ReactionContext
    {
    public:
        explicit ReactionContext(Model &model);
        std::size_t get_reaction_id(const std::string &reaction_name) const;
        std::size_t get_reaction_id(const Reaction &reaction) const;
        void set_propensity_function(std::size_t reaction_id, const CPropensityFunction &propensity_function);
        void set_ode_propensity_function(std::size_t reaction_id, const CPropensityFunction &propensity_function);
        void set_ssa_propensity_function(std::size_t reaction_id, const CPropensityFunction &propensity_function);

        double get_propensity_sum(double *state, double *parameters);

    private:
        void set_ssa_propensity_function(std::size_t reaction_id, double (*propensity_function)(double*, double*));
        void set_ode_propensity_function(std::size_t reaction_id, double (*propensity_function)(double*, double*));
        std::unordered_map<std::string, std::size_t> reaction_id_map;
        std::unordered_map<std::size_t, double(*)(double*, double*)> ssa_propensity_map;
        std::unordered_map<std::size_t, double(*)(double*, double*)> ode_propensity_map;
    };

    class ModelContext
    {
    public:
        explicit ModelContext(Model &model);
        ReactionContext &reactions();

    private:
        ReactionContext reaction_context;
    };

}
