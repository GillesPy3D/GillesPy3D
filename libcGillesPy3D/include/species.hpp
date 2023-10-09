#pragma once

#include <string>
#include <vector>

namespace GillesPy3D
{

    class Species
    {
    private:
        std::string name;
        double diffusion_coefficient;
        std::vector<int> restrict_to_type_list;
    public:
        Species(std::string name);
        Species(std::string name, double diffusion_coefficient);
        Species(std::string name, double diffusion_coefficient, std::vector<int> restrict_to_type_list);
    };

}
