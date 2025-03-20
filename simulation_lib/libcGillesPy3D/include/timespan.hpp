#pragma once

namespace GillesPy3D
{

    class Timespan
    {
    public:
        int num_timesteps;
        double timestep_size;
        double output_freq;
        Timespan(int num_timesteps, double timestep_size, double output_freq);
    };

}
