# GillesPy3D is a Python 3 package for simulation of
# spatial/non-spatial deterministic/stochastic reaction-diffusion-advection problems
# Copyright (C) 2023-2024 GillesPy3D developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU GENERAL PUBLIC LICENSE Version 3 as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU GENERAL PUBLIC LICENSE Version 3 for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module defines a model that simulates a discrete, stoachastic, mixed biochemical reaction network in python.

def initialize(model, epsilon):
    """
    This method initailizes the state for tau-leaping selections to be made.
    Based on Cao, Y.; Gillespie, D. T.; Petzold, L. R. (2006). "Efficient step size selection for the tau-leaping
    simulation method" (PDF).
    The Journal of Chemical Physics. 124 (4): 044109. Bibcode:2006JChPh.124d4109C. doi:10.1063/1.2159468. PMID 16460151
    """

    HOR = {}  # Highest Order Reaction of species
    reactants = set()  # a list of all species in the model which act as reactants
    mu_i = {}  # mu_i for each species
    sigma_i = {}  # sigma_i squared for each species
    g_i = {}  # Relative species error allowance denominator
    epsilon_i = {}  # Relative error allowance of species
    critical_threshold = 10  # Reactant Population to be considered critical

    # initialize Highest Order Reactions
    for s in model.listOfSpecies:
        HOR[s] = 0

    # Create list of all reactants
    for r in model.listOfReactions:
        # Calculate this reaction's order
        reaction_order = sum(model.listOfReactions[r].reactants.values())
        for reactant, count in model.listOfReactions[r].reactants.items():
            # Build reactant list
            reactants.add(reactant)
            # Initialize mu and sigma for each reactant
            mu_i[reactant.name] = 0
            sigma_i[reactant.name] = 0
            # if this reaction's order is higher than previous, set HOR
            if reaction_order > HOR[reactant.name]:
                HOR[reactant.name] = reaction_order
                if count == 2 and reaction_order == 2:
                    g_i[reactant.name] = lambda x: 2 + (1 / (x - 1))
                elif count == 2 and reaction_order == 3:
                    g_i[reactant.name] = lambda x: (
                        3 / 2) * (2 + (1 / (x - 1)))
                elif count == 3:
                    g_i[reactant.name] = lambda x: (
                        3 + (1 / (x - 1)) + (2 / (x - 2)))
                else:
                    g_i[reactant.name] = HOR[reactant.name]
                    epsilon_i[reactant.name] = epsilon / g_i[reactant.name]

    # Return components for tau selection
    return HOR, reactants, mu_i, sigma_i, g_i, epsilon_i, critical_threshold


def select(*tau_args):
    """
    Tau Selection method based on Cao, Y.; Gillespie, D. T.; Petzold, L. R. (2006).
    "Efficient step size selection for the tau-leaping simulation method" (PDF).
    The Journal of Chemical Physics. 124 (4): 044109. Bibcode:2006JChPh.124d4109C. doi:10.1063/1.2159468. PMID 16460151
    """

    HOR, reactants, mu_i, sigma_i, g_i, epsilon_i, epsilon, critical_threshold, model, propensities, curr_state, \
        curr_time, save_time = tau_args
    tau_step = 0
    crit_taus = {}  # Estimated time to single-firing of critical reactions
    critical_reactions = []  # List of critical reactions at this step
    critical = False  # system-wide flag, true when any reaction is critical
    critical_tau = 0  # holds the smallest tau time for critical reactions
    non_critical_tau = 0  # holds the smallest tau time for non-critical reactions
    tau = 0

    # Determine if there are any critical reactions
    for rxn in model.listOfReactions:
        for r, v in model.listOfReactions[rxn].reactants.items():
            if curr_state[r.name] / v < critical_threshold and propensities[rxn] > 0:
                critical_reactions.append(rxn)
                critical = True

    # If a critical reaction is present, estimate tau for a single firing of each
    # critical reaction with propensity > 0, and take the smallest tau
    if critical:
        for rxn in model.listOfReactions:
            if propensities[rxn] > 0:
                crit_taus[rxn] = 1 / propensities[rxn]
        critical_tau = min(crit_taus.values())

    # If a reactant's HOR requires >1 of that reactant, evaluate lambda at curr_state
    for r in g_i:
        if callable(g_i[r]):
            g_i[r] = g_i[r](curr_state[r])
            epsilon_i[r] = epsilon / g_i[r]

    tau_i = {}  # estimated tau for non-critical reactions
    mu_i = {species.name: 0 for species in model.listOfSpecies.values()}
    sigma_i = {species.name: 0 for species in model.listOfSpecies.values()}

    for r in model.listOfReactions:
        # Calculate abs mean and standard deviation for each reactant
        for reactant in model.listOfReactions[r].reactants:
            net_change = model.listOfReactions[r].reactants[reactant]
            if reactant in model.listOfReactions[r].products:
                net_change -= model.listOfReactions[r].products[reactant]
            net_change = abs(net_change)
            mu_i[reactant.name] += net_change * \
                propensities[r]  # Cao, Gillespie, Petzold 32a
            sigma_i[reactant.name] += net_change ** 2 * \
                propensities[r]  # Cao, Gillespie, Petzold 32b

    for r in reactants:
        calculated_max = epsilon_i[r.name] * curr_state[r.name]
        max_pop_change_mean = max(calculated_max, 1)
        max_pop_change_sd = max(calculated_max, 1) ** 2
        if mu_i[r.name] > 0:
            # Cao, Gillespie, Petzold 33
            tau_i[r.name] = min(
                abs(max_pop_change_mean / mu_i[r.name]),
                max_pop_change_sd / sigma_i[r.name])

    if len(tau_i) > 0:
        non_critical_tau = min(tau_i.values())

    for r in model.listOfReactions:
        # Calculate abs mean and standard deviation for each reactant
        for product in model.listOfReactions[r].products:
            mu_i[product.name] -= model.listOfReactions[r].products[product] * propensities[
                r]  # Cao, Gillespie, Petzold 32a
            sigma_i[product.name] += model.listOfReactions[r].products[product] ** 2 * propensities[
                r]  # Cao, Gillespie, Petzold 32b

    # If all reactions are non-critical, use non-critical tau.
    if not critical:
        tau = non_critical_tau
    # If all rxns are critical, use critical tau.
    elif len(tau_i) == 0:
        tau = critical_tau
    # If there are both critical and non-critical reactions,
    # take the shortest tau between critical and non-critical.
    else:
        tau = min(non_critical_tau, critical_tau)
    # If selected tau exceeds save time, integrate to save time
    if tau > 0:
        tau = max(tau, 1e-10)  # set minimum to prevent integration errors
        if save_time - curr_time > 0:
            tau = min(tau, save_time - curr_time)
    else:
        tau = save_time - curr_time
    return tau
