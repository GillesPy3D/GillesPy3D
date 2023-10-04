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
        std::unique_ptr<double[]> get_species(std::string species_name);
        std::unique_ptr<double[]> get_property(std::string property_name);
        std::unique_ptr<double[]> get_position();

        void output_vtk(std::string output_directory);
    };

}
