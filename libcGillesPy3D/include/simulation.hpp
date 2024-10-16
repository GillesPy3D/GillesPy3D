#pragma once

#include <vector>
#include <memory>
#include <string>
#include <tuple>
#include "model_context.hpp"
#include "particle_system.hpp"

namespace GillesPy3D
{

    class Simulation
    {
    public:
        // explicit Simulation(Model &model);
        explicit Simulation(ModelContext &context);

        void run_until(double t);
        double *get_species(const std::string &species_name);
        double *get_property(const std::string &property_name);
        double *get_position();

        void output_vtk(const std::string &output_directory);
        void reset();

    private:
        ModelContext &context;
    };

}
