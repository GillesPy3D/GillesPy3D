#pragma once

#include <sundials/sundials_types.h>

namespace GillesPy3D
{

    class Reaction
    {
    public:
        Reaction(const std::string &name);
        ssa_propensity(realtype *species_state, double *parameter_state) 
        ode_propensity(realtype *species_state, double *parameter_state) 
    };

}
