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
        std::vector<int> restrict_diffusion_to_type_list;
        double non_spatial_initial_value;
    public:
        Species(const std::string &name="");
        Species(const std::string &name, 
                const double diffusion_coefficient, 
                const std::vector<int> restrict_to);
        Species(const std::string &name, 
                const double initial_value);

        const std::string &get_name() const;
    };

}
 