#include "reaction.hpp"

GillesPy3D::Reaction::Reaction(const std::string &name)
    : name(name)
{
    // TODO
}

const std::string &GillesPy3D::Reaction::get_name() const
{
    return name;
}
