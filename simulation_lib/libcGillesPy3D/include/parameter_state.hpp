#pragma once

#include "sundials/sundials_types.h"
#include <memory>
#include <vector>

namespace GillesPy3D
{

    class ParameterState
    {
    public:
        explicit ParameterState(const std::vector<double> &initial_parameters);
        std::size_t size();
        sunrealtype parameter(std::uint32_t parameter_id);
        sunrealtype *data() const;

    private:
        std::size_t m_parameter_count;
        std::unique_ptr<sunrealtype*> m_parameter_values;
    };

}
