
%include <std_string.i>
%include "std_vector.i"

%module libcgillespy3d
%{
#include "model.hpp"
%}
%template(SpeciesVector) std::vector<GillesPy3D::Species>;
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

