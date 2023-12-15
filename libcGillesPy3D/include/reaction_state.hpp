#pragma once

#include <sundials/sundials_types.h>



namespace GillesPy3D
{

    class ReactionState
    {

    public:
        SimulationState mode;
        Reaction *base_reaction;

        ReactionState();
    };

}
