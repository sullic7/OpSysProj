# Authors:
# Max Llewellyn
# Caroline Sullivan

class CPU:
    """This class represents the CPU. It holds a process and will feed it
    to the IOSubsystem when it's done."""

    def __init__(self, scheduling_algorithm, context_switch_time, round_robin_time_slice):
        self.current_proc = None
        self.ctx_switch_time_remaining = 0
        self.scheduling_algorithm = scheduling_algorithm
        self.context_switch_time = context_switch_time
        self.round_robin_time_slice = round_robin_time_slice
        self.time_elapased_in_RR= 0

    def has_process(self):
        """Tells us if the CPU has a process"""
        return self.current_proc != None

    def get_current_process(self):
        return self.current_proc

    def in_ctx_switch(self):
        return self.ctx_switch_time_remaining != 0

    def finishing_round_robin(self):
        if self.scheduling_algorithm != "RR":
            return False

        RR_time_left = self.round_robin_time_slice - self.time_elapased_in_RR
        # if we are going to finish a CPU burst before the RR time slice
        # expires we want to return false, otherwise if the next CPU related
        # thing to happen will be finishing a RR time slice return true.
        return self.current_proc.burst_time_remaining > RR_time_left

    def time_till_round_robin_done(self):
        return self.round_robin_time_slice - self.time_elapased_in_RR

    def finish_round_robin(self):
        RR_time_left = self.round_robin_time_slice - self.time_elapased_in_RR
        self.current_proc.burst_time_remaining -= RR_time_left
        # is redundant but just be to be safe
        self.time_elapased_in_RR = 0
        proc = self.current_proc
        self.current_proc = None
        return proc


    def finish_ctx_switch(self):
        self.ctx_switch_time_remaining = 0
        return self.current_proc

    def add_process(self, new_proc):
        if self.current_proc != None:
            print("ERROR! CPU is being fed a process and isn't done with it's old one!")
            exit(1)
        self.current_proc = new_proc
        self.ctx_switch_time_remaining = self.context_switch_time
        self.time_elapased_in_RR = 0

    def get_time_till_next_event(self):
        if self.current_proc is None:
            return None

        RR_time_remaining = self.time_till_round_robin_done()

        if(self.ctx_switch_time_remaining > 0):
            return self.ctx_switch_time_remaining
        else:
            if self.scheduling_algorithm == "RR":
                # return the time till the burst is finished, or RR time expires
                # whichever will happen first
                return min(self.current_proc.burst_time_remaining, 
                            RR_time_remaining)
            else:
                return self.current_proc.burst_time_remaining

    def update_time(self, time_passed):
        # no process means we don't care about time
        if self.current_proc is None:
            return

        # always bump the RR time, even if we're inside a ctx switch
        self.time_elapased_in_RR += time_passed

        if(self.ctx_switch_time_remaining > 0):
            if(self.ctx_switch_time_remaining < time_passed):
                time_passed -= self.ctx_switch_time_remaining
                self.current_proc.burst_time_remaining -= time_passed
                self.ctx_switch_time_remaining = 0
                
            else:
                self.ctx_switch_time_remaining -= time_passed

        if(self.ctx_switch_time_remaining == 0):
            self.current_proc.burst_time_remaining -= time_passed

        # maybe don't let these go below 0, maybe ignore it and use
        # <= when checking it. Not sure what's the best

    def preempt_process(self):
        if(self.current_proc is None):
            print("ERROR asked to preempt a process that doesn't exist from the cpu!")
        proc = self.current_proc
        self.current_proc = None
        return proc

    def get_and_clear_process(self):
        if(self.current_proc is None):
            print("ERROR asked to get a process that doesn't exist from the cpu!")
        proc = self.current_proc
        self.current_proc = None
        # advance the bursts completed counter
        proc.bursts_compleated += 1
        proc.burst_time_remaining = proc.burst_time
        return proc

    def give_new_RR_timeslice(self):
        self.time_elapased_in_RR = 0
        self.current_proc.burst_time_remaining -= self.round_robin_time_slice