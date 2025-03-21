/*
 * GillesPy2 is a modeling toolkit for biochemical simulation.
 * Copyright (C) 2019-2023 GillesPy2 developers.
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include "model.hpp"
#include "reaction_state.hpp"
#include "species_state.hpp"
#include "event_state.hpp"
#include "simulation.hpp"
#include "cvode/cvode.h"
#include "sunlinsol/sunlinsol_spgmr.h"
#include "sundials/sundials_types.h"
#include "sundials/sundials_context.h"
#include "sundials/sundials_nvector.h"
#include "nvector/nvector_serial.h"
#include <vector>
#include <random>
#include <functional>
#include <set>

namespace GillesPy3D
{
    /* IntegratorStatus: represents the runtime state of the integrator.
     * OK indicates that no errors have occurred.
     */
    enum IntegrationStatus
    {
        // No errors have occurred.
        OK = 0,
        // Attempted to perform a SUNDIALS operation on a null CVODE object.
        NULL_POINTER,
        // A non-null object resulted in a memory error and must be initialized.
        BAD_MEMORY,
        // Could not perform integration, step size too small.
        BAD_STEP_SIZE
    };

    /// @name SolverConfiguration
    /// @brief Container struct for integrator-specific configuration.
    /// TODO: should this be moved to the Simulation object? maybe create a Solver class(es)? or at least somewhere more visible?
    struct IntegratorConfiguration
    {
        double rel_tol;
        double abs_tol;
        double max_step;
    };

    class IntegratorData
    {
    public:
        std::vector<EventStatus> *events = nullptr;
        std::vector<std::function<double(double, const double*, const double*)>> active_triggers;
        // Container representing the rootfinder-enabled reactions.
        // Each integer at index i represents the reaction id corresponding to rootfinder element i.
        // In `rootfn`, this means that gout[i] is the "output" of reaction active_reaction_ids[i].
        // This is used to map the internal reaction number to the actual reaction id.
        std::vector<unsigned int> active_reaction_ids;
        std::vector<double> propensities;

        IntegratorData(const ParameterState &parameter_state, const SpeciesState &species_state, const ReactionState &reaction_state);

        const ParameterState &parameters() { return m_parameter_state; }
        const SpeciesState &species() { return m_species_state; }
        const ReactionState &reactions() { return m_reaction_state; }

    private:
        const ParameterState &m_parameter_state;
        const SpeciesState &m_species_state;
        const ReactionState &m_reaction_state;
    };

    /* :IntegrationResults:
     * Organized data structure for accessing the integrator's output vector.
     * Contents are MUTABLE! Updating the values in any containing pointers
     *   will be permanently reflected in the integrator's vector.
     * 
     * All pointers in the structure point to different regions of the same vector.
     * N_Vector: [ --- concentrations --- | ---- rxn_offsets ---- ]
     */
    struct IntegrationResults
    {
        // concentrations: bounded by [0, num_species)
        realtype *concentrations;
        // reactions:      bounded by [num_species, num_species + num_reactions)
        realtype *reactions;
        int retcode;
    };

    class IntegratorContext
    {
    public:
        explicit IntegratorContext(void *mpi_mem = nullptr);
        ~IntegratorContext();
        IntegratorContext(IntegratorContext&) = delete;
        IntegratorContext(IntegratorContext&&) = default;
        IntegratorContext &operator=(const IntegratorContext &context) = delete;
        IntegratorContext &operator=(IntegratorContext &&context) = default;
        SUNContext &operator*();

    private:
        SUNContext m_sundials_context;
    };

    class Integrator
    {
    private:
        void *cvode_mem;
        IntegratorContext context;
        SUNLinearSolver solver;
        int num_species;
        int num_reactions;
        int *m_roots = nullptr;
        URNGenerator urn;
    public:
        // status: check for errors before using the results.
        IntegrationStatus status;
        N_Vector y;
        N_Vector y0;
        N_Vector y_save;
        realtype t;
        realtype t_save;

        /* save_state()
         * Creates a duplicate copy of the integrator's current solution vector.
         * Contents of the most recent duplicate will be restored when restore_state() is called.
         * 
         * Returns the time value of the integrator's saved state.
         */
        double save_state();

        /* restore_state()
         * Loads the most recent duplicated copy of the solution vector.
         * 
         * Returns the time value that the integrator was restored to.
         */
        double restore_state();

        /* refresh_state()
         * Loads any new changes to the solution vector without changing previous output.
         * Any new values assigned to the public N_Vector y will be recognized by the integrator.
         * The current time value remains the same. To change this, modify `t`.
         */
        void refresh_state();

        /* rereinitialize()
         * restore state to the values passed to the constructor.
         */
        void reinitialize();

        /// @brief Make events available to root-finder during integration.
        /// The root-finder itself is not activated until enable_root_finder() is called.
        ///
        /// @param events List of event objects to make available to the root-finder.
        /// The trigger functions of all given events are added as root-finder targets.
        void use_events(const std::vector<EventStatus> &events);

        /// @brief Make reactions available to root-finder during integration.
        /// The root-finder itself is not activated until enable_root_finder() is called.
        void use_reactions();

        /// @brief Installs a CVODE root-finder onto the integrator.
        /// Any events or reactions provided by previous calls to use_events() or use_reactions()
        /// will cause the integrator to return early, which the integrate() method will indicate.
        bool enable_root_finder();

        /// @brief Removes the CVODE root-finder from the integrator.
        /// Early returns on root-finder events no longer happen,
        /// and the underlying SBML event data and reaction data are removed.
        bool disable_root_finder();

        /// @brief Configures CVODE to use the user-supplied configuration data.
        /// If all configurations were applied successfully, returns true. Otherwise, returns false.
        bool configure(IntegratorConfiguration config);

        void set_error_handler(CVErrHandlerFn error_handler);


		inline realtype *get_y_save_ptr()
		{
			return &N_VGetArrayPointer(y_save)[0];
		}
		inline realtype *get_y0_ptr()
		{
			return &N_VGetArrayPointer(y0)[0];
		}

		inline realtype *get_species_state()
		{
			return &N_VGetArrayPointer(y)[0];
		}
		inline realtype *get_reaction_state()
		{
			return &N_VGetArrayPointer(y)[num_species];
		}

        IntegrationResults integrate(double *t);
        IntegrationResults integrate_constant(double *t);
        IntegrationResults integrate(double *t, std::set<int> &event_roots, std::set<unsigned int> &reaction_roots, int num_det_rxns, int num_rate_rules);
        IntegratorData data;

        Integrator(const GillesPy3D::ParameterState &parameter_state, const SpeciesState &species_state, const ReactionState &reaction_state, URNGenerator urn, double reltol, double abstol);
        ~Integrator();
        N_Vector init_model_vector(const SUNContext &context);
        void reset_model_vector();
    };

    int rhs(realtype t, N_Vector y, N_Vector ydot, void *user_data);
    int rootfn(realtype t, N_Vector y, realtype *gout, void *user_data);
}
