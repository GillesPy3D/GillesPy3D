#pragma once

#include "parameter_state.hpp"

#include "sundials/sundials_types.h"
#include <memory>
#include <set>
#include <vector>
#include <map>
#include <list>
#include <queue>
#include <utility>

namespace GillesPy3D
{

    class EventExecution;
    class EventStatus;

    using ReactionId = std::size_t;
    using EventId = std::size_t;
    template <typename T>
    using DelayedExecutionQueue = std::priority_queue<std::pair<EventId, EventExecution>, std::vector<std::pair<EventId, EventExecution>>, T>;

    struct EventOutput
    {
        sunrealtype *species_out;
        sunrealtype *variable_out;
        const sunrealtype *species;
        const sunrealtype *variables;
    };

    class EventState
    {
    public:
        explicit EventState(ParameterState &parameters);
        bool evaluate_triggers(double *event_state, double t);
        bool evaluate(double *output, std::size_t output_size, double t, const std::set<EventId> &events_found);
        inline bool has_active_events() const
        {
            return !m_trigger_pool.empty();
        }

    private:
        ParameterState &m_parameters;
        std::vector<EventStatus> m_events;
        std::set<EventId> m_trigger_pool;
        std::map<EventId, bool> m_trigger_state;
        DelayedExecutionQueue<std::greater<std::pair<EventId, EventExecution>>> m_delay_queue;
        std::list<std::pair<EventId, EventExecution>> m_volatile_queue;
    };

    class EventStatus
    {
    public:
        friend class EventExecution;

        bool (*trigger)(double t, const double *state, const double *parameters);
        double (*delay)(double t, const double *state, const double *parameters);
        double (*priority)(double t, const double *state, const double *parameters);
        void (*assign)(double t, EventOutput &output);
        bool get_initial_value() const;
        inline bool is_persistent() const { return m_use_persist; }

        EventExecution get_execution(double t,
                const double *state, std::size_t num_state,
                const double *parameters, std::size_t num_parameters) const;
        static void use_events(std::vector<EventStatus> &events);

    private:
        bool m_use_trigger_state;
        bool m_use_persist;

        explicit EventStatus(int event_id, bool use_trigger_state, bool use_persist);
    };

    class EventExecution
    {
    public:

        friend class EventStatus;
        ~EventExecution();
        EventExecution(const EventExecution&);
        EventExecution(EventExecution&&) noexcept;
        EventExecution &operator=(const EventExecution&);
        EventExecution &operator=(EventExecution&&) noexcept;
        bool operator<(const EventExecution &rhs) const;
        bool operator>(const EventExecution &rhs) const;

        void execute(double t, EventOutput output) const;
        void execute(double t, double *state, double *parameters) const;
        inline double priority(double t, const double *state, const double *parameters) const
        {
            return m_event.priority(t, state, parameters);
        }
        inline bool trigger(double t, const double *state, const double *parameters) const
        {
            return m_event.trigger(t, state, parameters);
        }
        inline double get_execution_time() const { return m_execution_time; }

    private:
        const EventStatus &m_event;
        double m_execution_time;

        int m_num_state = 0;
        double *m_state = nullptr;
        
        int m_num_variables = 0;
        double *m_variables = nullptr;

        std::vector<const EventStatus*> m_assignments;
        void use_assignments();

        explicit EventExecution(const EventStatus &event, double t);
        EventExecution(const EventStatus &event, double t,
                        const double *state, std::size_t num_state,
                        const double *variables, std::size_t num_variables);
    };

}
