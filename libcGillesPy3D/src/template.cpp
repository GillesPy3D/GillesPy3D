#include "particle_system.hpp"
#include "template.hpp"

namespace GillesPy3D
{
    /* Parameter definitions */
    __DEFINE_PARAMETERS__
    /* Reaction definitions */
    __DEFINE_REACTIONS__
    /* Deterministic RHS definitions */
    __DEFINE_CHEM_FUNS__
    /* Definition for get next output step */
    __DEFINE_GET_NEXT_OUTPUT__

    PropensityFun *ALLOC_propensities(void)
    {
        PropensityFun *ptr = (PropensityFun *)malloc(sizeof(PropensityFun)*__NUMBER_OF_REACTIONS__);
    __DEFINE_PROPFUNS__
        return ptr;
    }

    void FREE_propensities(PropensityFun* ptr)
    {
        free(ptr);
    }

    ChemRxnFun* ALLOC_ChemRxnFun(void){
        ChemRxnFun*ptr = (ChemRxnFun*)malloc(sizeof(ChemRxnFun)*__NUMBER_OF_REACTIONS__);
    __DEFINE_CHEM_FUN_INITS__
        return ptr;
    }
    void FREE_ChemRxnFun(ChemRxnFun* ptr){
        free(ptr);
    }


    __INPUT_CONSTANTS__

    //dsfmt_t dsfmt;

    void init_create_particle(ParticleSystem *sys, unsigned int id, double x, double y, double z, int type, double nu, double mass, double c, double rho, int solidTag, int num_chem_species){
        sys->particles.emplace_back(Particle(sys, id, x, y, z, type, nu, mass, c, rho,
            solidTag));
        Particle *this_particle = &sys->particles.back() ;
        if(num_chem_species > 0){
            for(int i=0;i<num_chem_species;i++){
                this_particle->C[i] = (double) input_u0[id*num_chem_species+i];
            }
        }
        __DATA_FUNCTION_ASSIGN__
    }


    int init_all_particles(ParticleSystem *sys){
        unsigned int id=0;
        __INIT_PARTICLES__
        return id;
    }

    void applyBoundaryConditions(Particle* me, ParticleSystem* system){
    __BOUNDARY_CONDITIONS__
    }
}
