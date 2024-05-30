#include "model.hpp"
#include <memory>
#include <string>
#include <stdio.h>

GillesPy3D::Model::Model(const std::string & name)
{
    std::cout << "Model(" << name << ")" << std::endl;
}


void GillesPy3D::Model::add_reaction(const GillesPy3D::Reaction &reaction)
{
    listOfReactions.emplace_back(reaction);
}

const std::vector<GillesPy3D::Reaction> &GillesPy3D::Model::get_reactions() const
{
    return listOfReactions;
}

void GillesPy3D::Model::add_parameter(const GillesPy3D::Parameter &parameter)
{
    listOfParameters.emplace_back(parameter);
}

void GillesPy3D::Model::add_species(GillesPy3D::Species &species)
{
    listOfSpecies.emplace_back(species);
}


void GillesPy3D::Model::add_initial_condition(const GillesPy3D::InitialCondition &initial_condition)
{
    listOfInitialConditions.emplace_back(initial_condition);
}

void GillesPy3D::Model::add_data_function(const GillesPy3D::DataFunction &data_function)
{
    listOfDataFunctions.emplace_back(data_function);
}

void GillesPy3D::Model::add_boundary_condition(const GillesPy3D::BoundaryCondition &boundary_condition)
{
    listOfBoundaryConditions.emplace_back(boundary_condition);
}

void GillesPy3D::Model::add_domain(const GillesPy3D::Domain &dom)
{
    domain = dom;
}

void GillesPy3D::Model::add_timespan(int num_timesteps, double timestep_size, double output_freq)
{
    timespan = std::make_unique<GillesPy3D::Timespan>(num_timesteps,timestep_size,output_freq);

}

void GillesPy3D::Model::run()
{
    sim = Simulation(this);
    while(t < this.t_end){
       sim.run_until(next_t);
       // save to result
    }
}
