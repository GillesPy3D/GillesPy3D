#pragma once

#include <sundials/sundials_types.h>
#include <string>

namespace GillesPy3D
{

    class Reaction
    {
    public:
        explicit Reaction(const std::string &name);
        const std::string &get_name() const;

    private:
        const std::string name;
    };

}
