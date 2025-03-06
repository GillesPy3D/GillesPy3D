#pragma once

#include <exception>
#include <string>

namespace GillesPy3D
{

    class GillesPyError : public std::exception
    {
    public:
        GillesPyError() noexcept;
        GillesPyError(const char *const message) noexcept;
        virtual const char *what() const noexcept;
    private:
        const std::string message;
    };

}
