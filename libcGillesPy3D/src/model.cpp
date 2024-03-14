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

//void GillesPy3D::Model::add_parameter(const std::vector<GillesPy3D::Parameter> &parameter)
//{
//    // TODO
//}
void GillesPy3D::Model::add_parameter(const GillesPy3D::Parameter &parameter)
{
    // TODO
}

void GillesPy3D::Model::add_species(GillesPy3D::Species &species)
{
    std::cout << "single species" << std::endl;
}

/*void GillesPy3D::Model::add_species(const std::vector<GillesPy3D::Species> &species)
{
    std::cout << "multiple species" << std::endl;
}*/

void GillesPy3D::Model::add_initial_condition(const GillesPy3D::InitialCondition &initial_condition)
{
    // TODO
}

void GillesPy3D::Model::add_data_function(const GillesPy3D::DataFunction &data_function)
{
    // TODO
}

void GillesPy3D::Model::add_boundary_condition(const GillesPy3D::BoundaryCondition &boundary_condition)
{
    // TODO
}

void GillesPy3D::Model::add_domain(const GillesPy3D::Domain &domain)
{
    // TODO
}

void GillesPy3D::Model::add_timespan(int num_timesteps, double timestep_size, double output_freq)
{
    timespan = std::make_unique<GillesPy3D::Timespan>(num_timesteps,timestep_size,output_freq);

}

void GillesPy3D::Model::run()
{
    // TODO
}
