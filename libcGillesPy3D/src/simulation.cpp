#include "simulation.hpp"

GillesPy3D::Simulation::Simulation()
{
    // TODO
}

void GillesPy3D::Simulation::run_until(double t)
{
    // TODO
}

double *GillesPy3D::Simulation::get_species(const std::string &species_name)
{
    // TODO
    return new double[32];
}

double *GillesPy3D::Simulation::get_property(const std::string &property_name)
{
    // TODO
    return new double[32];
}

double *GillesPy3D::Simulation::get_position()
{
    // TODO
    return new double[32];
}

void GillesPy3D::Simulation::output_vtk(const std::string &output_directory)
{
    // TODO
}
