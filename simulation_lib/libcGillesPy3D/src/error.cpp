#include "error.hpp"

GillesPy3D::GillesPyError::GillesPyError() noexcept
    : message("")
{
    // empty constructor body
}

GillesPy3D::GillesPyError::GillesPyError(const char *const message) noexcept
    : message(message)
{
    // empty constructor body
}

const char *GillesPy3D::GillesPyError::what() const noexcept
{
    return message.c_str();
}
