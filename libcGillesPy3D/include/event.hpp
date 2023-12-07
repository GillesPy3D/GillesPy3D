#pragma once

#include <string>
#include <map>
#include <set>
#include <queue>
#include <list>

namespace GillesPy3D
{

    class EventExecution;

    class Event;
    typedef int ReactionId;
    template <typename T>
    using DelayedExecutionQueue = std::priority_queue<EventExecution, std::vector<EventExecution>, T>;

    struct EventOutput
    {
        double *species_out;
        double *variable_out;
        const double *species;
        const double *variables;
        const double *constants;
    };

    class EventList
    {
    public:
        EventList();
        bool evaluate_triggers(double *event_state, double t);
        bool evaluate(double *output, int output_size, double t, const std::set<int> &events_found);
        inline bool has_active_events() const
        {
            return !m_trigger_pool.empty();
        }

    private:
        std::vector<Event> m_events;
        std::set<int> m_trigger_pool;
        std::map<int, bool> m_trigger_state;
        DelayedExecutionQueue<std::greater<EventExecution>> m_delay_queue;
        std::list<EventExecution> m_volatile_queue;
    };

    class Event
    {
    public:
        friend class EventExecution;

        inline bool trigger(double t, const double *state) const
        {
            return Event::trigger(m_event_id, t, state, Reaction::s_variables.get(), Reaction::s_constants.get());
        }

        inline double delay(double t, const double *state) const
        {
            return Event::delay(m_event_id, t, state, Reaction::s_variables.get(), Reaction::s_constants.get());
        }

        inline bool get_initial_value() const
        {
            return Event::initial_value(m_event_id);
        }

        inline bool is_persistent() const { return m_use_persist; }
        inline int get_event_id() const { return m_event_id; }

        EventExecution get_execution(double t,
                const double *state, int num_state) const;
        static void use_events(std::vector<Event> &events);

    private:
        int m_event_id;
        bool m_use_trigger_state;
        bool m_use_persist;

        explicit Event(int event_id, bool use_trigger_state, bool use_persist);

        static bool trigger(
                int event_id, double t,
                const double *state,
                const double *variables,
                const double *constants);
        static double delay(
                int event_id, double t,
                const double *state,
                const double *variables,
                const double *constants);
        static double priority(
                int event_id, double t,
                const double *state,
                const double *variables,
                const double *constants);
        static void assign(int event_id, double t, EventOutput output);
        static bool initial_value(int event_id);
    };

    class EventExecution
    {
    public:

        friend class Event;
        ~EventExecution();
        EventExecution(const EventExecution&);
        EventExecution(EventExecution&&) noexcept;
        EventExecution &operator=(const EventExecution&);
        EventExecution &operator=(EventExecution&&) noexcept;

        void execute(double t, EventOutput output) const;
        void execute(double t, double *state);
        inline double priority(double t, const double *state) const
        {
            return Event::priority(m_event_id, t, state, Reaction::s_variables.get(), Reaction::s_constants.get());
        }
        inline bool trigger(double t, const double *state) const
        {
            return Event::trigger(m_event_id, t, state, Reaction::s_variables.get(), Reaction::s_constants.get());
        }

        inline double get_execution_time() const { return m_execution_time; }
        inline int get_event_id() const { return m_event_id; }

        bool operator<(const EventExecution &rhs) const;
        bool operator>(const EventExecution &rhs) const;

    private:
        double m_execution_time;
        int m_event_id;

        int m_num_state = 0;
        double *m_state = nullptr;
        
        int m_num_variables = 0;
        double *m_variables = nullptr;

        std::vector<int> m_assignments;
        void use_assignments();

        EventExecution(int event_id, double t);
        EventExecution(int event_id, double t,
                       const double *state, int num_state,
                       const double *variables, int num_variables);
    };

}
