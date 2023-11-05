
%include <std_string.i>
%include "std_vector.i"
%include <std_except.i>

%module libcgillespy3d
%{
#include "model.hpp"
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
%include "simulation.hpp"
%include "species.hpp"
%include "timespan.hpp"
%include "model.hpp"
%include "error.hpp"
