#pragma once

#include <vector>
#include <memory>
#include <string>
#include <tuple>
#include "particle_system.hpp"

namespace GillesPy3D
{

    class Simulation
    {
    public:
        Simulation();

        void run_until(double t);
        double *get_species(const std::string &species_name);
        double *get_property(const std::string &property_name);
        double *get_position();

        void output_vtk(const std::string &output_directory);
    };

}