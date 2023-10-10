#include "species.hpp"
#include <string>
#include <vector>

GillesPy3D::Species::Species(const std::string &name, 
            const double diffusion_coefficient, 
            const std::vector<int> restrict_to, 
            const int initial_value)
{
    this->name=name;
    this->diffusion_coefficient;
    this->restrict_to_type_list = restrict_to;
    this->initial_value = initial_value;
}
