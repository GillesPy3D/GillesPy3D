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
        int initial_value;
    public:
        //Species(const std::string &name);
        //Species(const std::string &name, double diffusion_coefficient);
        Species(const std::string &name="", 
            const double diffusion_coefficient=0.0, 
            const std::vector<int> restrict_to=std::vector<int>(), 
            const int initial_value=0);
    };

}
