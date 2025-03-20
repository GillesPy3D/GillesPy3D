
%include <std_string.i>
%include <std_vector.i>
%include <std_except.i>

namespace std {
    %template(DataVector) vector<double>;
}

%typemap(in) double(*)(double*, double*) {
    *((void**)&$1) = PyLong_AsVoidPtr($input);
}

%module libcgillespy3d
%{
#include "model.hpp"
#include "model_context.hpp"
#include "simulation.hpp"
#include "error.hpp"
%}
%template(SpeciesVector) std::vector<GillesPy3D::Species>;
%catches(GillesPy3D::GillesPyError);
%include "boundary_condition.hpp"
%include "data_function.hpp"
%include "domain.hpp"
%include "initial_condition.hpp"
%include "parameter.hpp"
%include "reaction.hpp"
%include "species.hpp"
%include "timespan.hpp"
%include "error.hpp"
%include "model.hpp"
%include "model_context.hpp"
%include "simulation.hpp"
