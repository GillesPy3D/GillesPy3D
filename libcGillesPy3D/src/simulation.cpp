#include "simulation.hpp"
#include <iostream>


GillesPy3D::Simulation::Simulation(GillesPy3D::Model &model){
    context = GillesPy3D::ModelContext(model);


    // TODO
    // to turn a Model into a Simulation, we need to compile the 
    // propensity functions
    // 1. compile a c lib, dll.load it
    // 2. JIT (for python)
    // 3. if model is all mass-action
    // TODO - update:  Move this constructor to python, use numba JIT
    // as the default for the first implementation

}


GillesPy3D::Simulation::Simulation(GillesPy3D::ModelContext &context)
    : context(context)
{
    double test_state[2] = {1.23, 4.56};
    double test_parameters[1] = {2.5};
    std::cout << "testing propensity sum: " << context.reactions().get_propensity_sum(test_state, test_parameters) << std::endl;
}


void GillesPy3D::Simulation::reset(){
    // set t=0, re-set initial conditions
}

void GillesPy3D::Simulation::run_until(double t)
{
    // TODO
    // while current_time < t
        // foreach particle
            // find neighbors (1st step, all steps if non-static)
            // find max tau
        // foreach particle
            // integrate forward by tau

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
