#include "species.hpp"
#include <string>
#include <vector>

GillesPy3D::Species::Species(std::string name, double diffusion_coefficient, std::vector<int> restrict_to_type_list):
    name(name),
    diffusion_coefficient(diffusion_coefficient)
{
    restrict_to_type_list = restrict_to_type_list;
}

GillesPy3D::Species::Species(std::string name, double diffusion_coefficient):
    name(name),
    diffusion_coefficient(diffusion_coefficient)
{}

GillesPy3D::Species::Species(std::string name):
    name(name),
    diffusion_coefficient(0.0)
{}
