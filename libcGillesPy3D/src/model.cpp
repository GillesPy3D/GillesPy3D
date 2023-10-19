#include "model.hpp"
#include <string>
#include <stdio.h>

GillesPy3D::Model::Model(const std::string & name)
{
    std::cout << "Model(" << name << ")" << std::endl;
}


void GillesPy3D::Model::add_reaction(const std::vector<GillesPy3D::Reaction> &reaction)
{
    // TODO
}

void GillesPy3D::Model::add_parameter(const std::vector<GillesPy3D::Parameter> &parameter)
{
    // TODO
}

void GillesPy3D::Model::add_species(GillesPy3D::Species &species)
{
    std::cout << "single species" << std::endl;
}

void GillesPy3D::Model::add_species(const std::vector<GillesPy3D::Species> &species)
{
    std::cout << "multiple species" << std::endl;
}

void GillesPy3D::Model::add_initial_condition(const std::vector<GillesPy3D::InitialCondition> &initial_condition)
{
    // TODO
}

void GillesPy3D::Model::add_data_function(const std::vector<GillesPy3D::DataFunction> &data_function)
{
    // TODO
}

void GillesPy3D::Model::add_boundary_condition(const std::vector<GillesPy3D::BoundaryCondition> &boundary_condition)
{
    // TODO
}

void GillesPy3D::Model::add_domain(const GillesPy3D::Domain &domain)
{
    // TODO
}

void GillesPy3D::Model::add_timespan(const GillesPy3D::Timespan &timespan)
{
    // TODO
}

void GillesPy3D::Model::run()
{
    // TODO
}

GillesPy3D::Simulation *GillesPy3D::Model::get_simulation_object()
{
    // TODO
    return nullptr;
}
