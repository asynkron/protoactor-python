from protoactor.messages import ResumeMailbox, Restart, Stop

class SupervisorDirective:
    Resume = 0
    Restart = 1
    Stop = 2
    Escalate = 3

class Supervisor(object):
    def escalate_failure(who, reason):
        raise NotImplementedError("Implement this on a subclass")


class SupervisorStrategy(object):
    def handle_failure(supervisor, pid_child, crs, exc_cause):
        raise NotImplementedError("Implement this on a subclass")


class OneOfOneStrategy(SupervisorStrategy):
    def __init__(self, decider, max_retries_number, within_timedelta):
        self.__decider = decider
        self.__max_retries_number = max_retries_number
        self.__within_timedelta = within_timedelta

    def __get_pid_aref(self, pid):
        return pid.aref if pid.aref is not None else ProcessRegistry().get(self)

    def handle_failure(self, supervisor, pid_child, crs, exc_cause):
        directive = self.__decider(pid_child, exc_cause)

        if directive == SupervisorDirective.Resume:
            pid_aref = self.__get_pid_aref(pid_child)
            pid_aref.send_system_message(pid_child, ResumeMailbox())
            return

        if directive == SupervisorDirective.Restart:
            pid_aref = self.__get_pid_aref(pid_child)
            if crs.request_restart_permission(self.__max_retries_number, self.__within_timedelta):
                # TODO: Log console "Restarting {child.ToShortString()} Reason {exc_cause}"
                pid_aref.send_system_message(pid_child, Restart())
            else:
                # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
                pid_aref.send_system_message(pid_child, Stop())
            return

        if directive == SupervisorDirective.Stop:
            # TODO: Log console Stopping {child.ToShortString()} Reason { exc_cause}"
            pid_aref = self.__get_pid_aref(pid_child)
            pid_aref.send_system_message(pid_child, Stop())
            return

        if directive == SupervisorDirective.Escalate:
            supervisor.escalate_failure(pid_child, exc_cause)
            return

        