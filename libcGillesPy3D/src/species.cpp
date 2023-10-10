#include "species.hpp"
#include <string>
#include <vector>

GillesPy3D::Species::Species(const std::string &name)
{
    this->name=name;
    this->diffusion_coefficient = diffusion_coefficient;
    this->restrict_diffusion_to_type_list = std::vector<int>();
    this->non_spatial_initial_value = 0;
}

GillesPy3D::Species::Species(const std::string &name, 
            const double diffusion_coefficient, 
            const std::vector<int> restrict_to)
{
    this->name=name;
    this->diffusion_coefficient = diffusion_coefficient;
    this->restrict_diffusion_to_type_list = restrict_to;
    this->non_spatial_initial_value = 0;
}

GillesPy3D::Species::Species(const std::string &name, 
            const double initial_value)
{
    this->name=name;
    this->diffusion_coefficient = 0.0;
    this->restrict_diffusion_to_type_list = std::vector<int>();
    this->non_spatial_initial_value = initial_value;
}
