#include "event_state.hpp"

GillesPy3D::EventStatus::EventStatus(int event_id, bool use_trigger_state, bool use_persist)
    : m_use_trigger_state(use_trigger_state),
      m_use_persist(use_persist) {}

GillesPy3D::EventExecution GillesPy3D::EventStatus::get_execution(
    double t,
    const double *state,
    std::size_t num_state,
    const double *parameters,
    std::size_t num_parameters) const
{
    auto &event = *this;
    if (m_use_trigger_state) {
        return GillesPy3D::EventExecution(event, t, state, num_state, parameters, num_parameters);
    }

    return GillesPy3D::EventExecution(event, t);
}

GillesPy3D::EventExecution::EventExecution(const GillesPy3D::EventStatus &event, double t)
    : m_event(event),
      m_execution_time(t)
{
    use_assignments();
}

GillesPy3D::EventExecution::EventExecution(const GillesPy3D::EventStatus &event, double t,
    const double *state, std::size_t num_state,
    const double *variables, std::size_t num_variables)
    : m_event(event),
      m_execution_time(t),
      m_num_state(num_state),
      m_state(new double[num_state]),
      m_num_variables(num_variables),
      m_variables(new double[num_variables])
{
    std::memcpy(m_state, state, sizeof(double) * num_state);
    std::memcpy(m_variables, variables, sizeof(double) * num_variables);
    use_assignments();
}

GillesPy3D::EventExecution::EventExecution(const GillesPy3D::EventExecution &old_event)
                : m_event(old_event.m_event),
                  m_execution_time(old_event.m_execution_time),
                  m_num_state(old_event.m_num_state),
                  m_num_variables(old_event.m_num_variables),
                  m_assignments(old_event.m_assignments)
{
    if (old_event.m_state != nullptr && m_num_state > 0)
    {
        m_state = new double[m_num_state];
        std::memcpy(m_state, old_event.m_state, sizeof(double) * m_num_state);
    }

    if (old_event.m_variables != nullptr && m_num_variables > 0)
    {
        m_variables = new double[m_num_variables];
        std::memcpy(m_variables, old_event.m_variables, sizeof(double) * m_num_variables);
    }
}

GillesPy3D::EventExecution::EventExecution(GillesPy3D::EventExecution &&old_event) noexcept
    : m_event(old_event.m_event),
      m_execution_time(old_event.m_execution_time),
      m_num_state(old_event.m_num_state),
      m_state(old_event.m_state),
      m_num_variables(old_event.m_num_variables),
      m_variables(old_event.m_variables),
      m_assignments(std::move(old_event.m_assignments))
{
    old_event.m_num_state = 0;
    old_event.m_state = nullptr;
    old_event.m_num_variables = 0;
    old_event.m_variables = nullptr;
}

GillesPy3D::EventExecution &GillesPy3D::EventExecution::operator=(const GillesPy3D::EventExecution &old_event)
{
    m_execution_time = old_event.m_execution_time;
    m_assignments = old_event.m_assignments;

    if (this != &old_event)
    {
        if (old_event.m_state != nullptr)
        {
            // If the containers are not of equal size, then we cannot reuse heap data.
            if (m_num_state != old_event.m_num_state)
            {
                delete[] m_state;
                m_num_state = old_event.m_num_state;
                m_state = new double[m_num_state];
            }
            std::memcpy(m_state, old_event.m_state, sizeof(double) * m_num_state);
        }

        if (old_event.m_variables != nullptr)
        {
            if (m_num_variables != old_event.m_num_variables)
            {
                delete[] m_variables;
                m_num_variables = old_event.m_num_variables;
                m_variables = new double[m_num_variables];
            }
            std::memcpy(m_variables, old_event.m_variables, sizeof(double) * m_num_variables);
        }
    }

    return *this;
}

GillesPy3D::EventExecution &GillesPy3D::EventExecution::operator=(GillesPy3D::EventExecution &&old_event) noexcept
{
    m_execution_time = old_event.m_execution_time;
    m_assignments = std::move(old_event.m_assignments);

    if (this != &old_event)
    {
        m_num_state = old_event.m_num_state;
        m_state = old_event.m_state;
        old_event.m_num_state = 0;
        old_event.m_state = nullptr;

        m_num_variables = old_event.m_num_variables;
        m_variables = old_event.m_variables;
        old_event.m_num_variables = 0;
        old_event.m_variables = nullptr;
    }

    return *this;
}

GillesPy3D::EventExecution::~EventExecution()
{
    delete[] m_state;
    delete[] m_variables;
}

void GillesPy3D::EventExecution::execute(double t, GillesPy3D::EventOutput &output) const
{
    for (auto assignment : m_assignments)
    {
        assignment->assign(t, output);
    }
}

void GillesPy3D::EventExecution::execute(double t, double *state, double *parameters) const
{
    if (m_state == nullptr || m_variables == nullptr)
    {
        execute(t, GillesPy3D::EventOutput {
            state,
            parameters,
            state,
            parameters
        });
    }
    else
    {
        execute(t, GillesPy3D::EventOutput {
            state,
            parameters,
            m_state,
            m_variables
        });
    }
}

bool GillesPy3D::EventExecution::operator<(const GillesPy3D::EventExecution &rhs) const
{
    return m_execution_time < rhs.m_execution_time;
}

bool GillesPy3D::EventExecution::operator>(const GillesPy3D::EventExecution &rhs) const
{
    return m_execution_time > rhs.m_execution_time;
}

GillesPy3D::EventState::EventState(GillesPy3D::ParameterState &parameters)
    : m_parameters(parameters)
{
    // TODO replace the below code with integration code via EventContext
    // As it currently stands, `m_events` is always empty
    // Event::use_events(m_events);

    for (GillesPy3D::EventId event_id = 0; event_id < m_events.size(); ++event_id)
    {
        auto &event = m_events[event_id];
        // With the below implementation, it is impossible for an event to fire at t=t[0].
        m_trigger_state.insert({
            event_id,
            event.get_initial_value(),
        });
    }
}

bool GillesPy3D::EventState::evaluate_triggers(double *event_state, double t)
{
    for (std::size_t event_id = 0; event_id < m_events.size(); ++event_id)
    {
        auto &event = m_events[event_id];
        if (event.trigger(t, event_state, m_parameters.data()) != m_trigger_state.at(event_id))
        {
            m_trigger_pool.insert(event_id);
        }
    }

    return has_active_events();
}

bool GillesPy3D::EventState::evaluate(double *event_state, std::size_t output_size, double t, const std::set<GillesPy3D::EventId> &events_found)
{
    if (m_events.empty())
    {
        return has_active_events();
    }

    sunrealtype *parameters = m_parameters.data();
    auto compare = [t, event_state, parameters](std::pair<GillesPy3D::EventId, GillesPy3D::EventExecution> &lhs,
                                                std::pair<GillesPy3D::EventId, GillesPy3D::EventExecution> &rhs) -> bool
    {
        return lhs.second.priority(t, event_state, parameters) < rhs.second.priority(t, event_state, parameters);
    };
    std::priority_queue<std::pair<GillesPy3D::EventId, GillesPy3D::EventExecution>, std::vector<std::pair<GillesPy3D::EventId, GillesPy3D::EventExecution>>, decltype(compare)>
            trigger_queue(compare);

    // Step 1: Identify any fired event triggers.
    for (GillesPy3D::EventId event_id = 0; event_id < m_events.size(); ++event_id)
    {
        auto &event = m_events[event_id];
        if (m_trigger_state.at(event_id) != event.trigger(t, event_state, parameters))
        {
            double delay = event.delay(t, event_state, parameters);
            GillesPy3D::EventExecution execution = event.get_execution(t + delay, event_state, output_size, parameters, m_parameters.size());

            if (delay <= 0)
            {
                // Immediately put EventExecution on "triggered" pile
                trigger_queue.push({ event_id, execution});
            }
            else if (event.is_persistent())
            {
                // Put EventExecution on "delayed" pile
                m_delay_queue.push({ event_id, execution });
            }
            else
            {
                // Search the volatile queue to see if it is already present.
                // If it is, the event has "double-fired" and must be erased.
                auto vol_iter = m_volatile_queue.begin();
                while (vol_iter != m_volatile_queue.end()
                       && vol_iter->first != event_id)
                {
                    ++vol_iter;
                }

                if (vol_iter == m_volatile_queue.end())
                {
                    // No match found; this is a new delay trigger, and is therefore valid.
                    // Delayed, but must be re-checked on every iteration.
                    m_volatile_queue.emplace_back(event_id, execution);
                }
                else
                {
                    // Match found; this is an existing trigger, discard.
                    m_volatile_queue.erase(vol_iter);
                    m_trigger_pool.erase(event_id);
                    m_trigger_state.at(event_id) = !m_trigger_state.at(event_id);
                }
            }
        }
    }

    // Step 2: Process delayed, non-persistent executions that are now ready to fire.
    // Both the volatile and non-volatile queue are processed in a similar manner.
    for (auto vol_event = m_volatile_queue.begin(); vol_event != m_volatile_queue.end(); ++vol_event)
    {
        auto &[event_id, execution] = *vol_event;
        // Execution objects in the volatile queue must remain True until execution.
        // Remove any execution objects which transitioned to False before execution.
        if (execution.get_execution_time() < t)
        {
            trigger_queue.push({ event_id, execution });
            vol_event = m_volatile_queue.erase(vol_event);
        }
    }

    // Step 3: Process delayed executions, which includes both persistent triggers
    // and non-persistent triggers whose execution time has arrived.
    while (!m_delay_queue.empty())
    {
        auto &[event_id, event] = m_delay_queue.top();
        if (event.get_execution_time() >= t)
        {
            // Delay queue is sorted in chronological order.
            // As soon as we hit a time that is beyond the current time,
            //  there is no use in continuing through the queue.
            break;
        }
        trigger_queue.push({ event_id, event });
        m_delay_queue.pop();
    }

    // Step 4: Process any pending triggers, unconditionally.
    while (!trigger_queue.empty())
    {
        auto &[event_id, event] = trigger_queue.top();

        event.execute(t, event_state, parameters);
        trigger_queue.pop();
        m_trigger_pool.erase(event_id);
    }

    // Step 5: Update trigger states based on the new simulation state.
    // This is to account for events that re-assign values that the event triggers depend on.
    for (GillesPy3D::EventId event_id = 0; event_id < m_events.size(); ++event_id)
    {
        auto &event = m_events[event_id];
        m_trigger_state.at(event_id) = event.trigger(t, event_state, parameters);
    }

    return has_active_events();
}
