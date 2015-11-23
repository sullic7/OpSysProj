context_switch_time = 13

class SimulatorProcess:
    """This class holds info about a process. How long it wants for CPU
    bursts, how long each burst is and how long it takes to do IO."""

    def __init__(self, info_string):
        # parse the string that has info about the process
        # string format 
        # <proc-num>|<arrival-time>|<burst-time>|<num-burst>|<io-time>|<memory>
        values = info_string.strip().split("|")
        self.proc_num = int(values[0])
        self.arrival_time = int(values[1])
        self.burst_time = int(values[2])
        self.num_bursts = int(values[3])
        self.io_time = int(values[4])
        self.memory_size = int(values[5])

        # set up vars to track remaining time
        self.burst_time_remaining = self.burst_time
        self.time_waiting_in_queue = 0

        # set up analytic variables
        self.bursts_compleated = 0
        self.cpu_burst_time = 0
        self.turnaround_time = 0
        self.wait_time = 0


    def print_self(self):
        print("<proc-num> %d, <burst-time> %d, <num-burst> %d, <io-time> %d, <bursts_compl> %d" % 
            (self.proc_num, self.burst_time, self.num_bursts, self.io_time, self.bursts_compleated))

class IOSubsystem:
    """This class represents the IO subsystem. It takes processes and 
    calculates when they will finish and feeds them back to the process queue 
    if need be."""

    def __init__(self):
        # things in here of the format (proc, time_left)
        # this should be sorted according to time left
        self.processes_doing_IO = []

    def add_process(self, proc):
        # do an insert at the right place so the list stays ordered
        for i in range(0, len(self.processes_doing_IO)):
            if self.processes_doing_IO[i][1] > proc.io_time:
                # we found a bigger io time than the one we have
                # put the new proc before it
                # make a list with the remaining IO time
                self.processes_doing_IO.insert(i, [proc, proc.io_time])
                # proc_list = []
                # print("processes in order of time to complete")
                # for proc_pair in self.processes_doing_IO:
                #     proc_list.append((proc_pair[0].proc_num, proc_pair[1]))
                # print(proc_list)
                return
        # the process never got inserted in the list so it must be the
        # new largest. Put it at the end of the list
        # make a list with the remaining IO time
        self.processes_doing_IO.append([proc, proc.io_time])

    def has_processes(self):
        """Tells us if there's anything in the IO Subsystem"""
        return len(self.processes_doing_IO) != 0

    def get_time_till_next_event(self):
        """This function returns the simulation time before the next process
        is done with it's IO."""
        if len(self.processes_doing_IO) != 0:
            return self.processes_doing_IO[0][1]
        else:
            return 999999999

    def get_and_clear_next_process(self):
        if len(self.processes_doing_IO) != 0:
            return self.processes_doing_IO.pop(0)[0]
        else:
            return None

    def update_time(self, time_passed):
        for i in range(len(self.processes_doing_IO)):
            self.processes_doing_IO[i][1] -= time_passed

class CPU:
    """This class represents the CPU. It holds a process and will feed it
    to the IOSubsystem when it's done."""

    def __init__(self, scheduling_algorithm, round_robin_time_slice=80):
        self.current_proc = None
        self.ctx_switch_time_remaining = 0
        self.scheduling_algorithm = scheduling_algorithm
        self.round_robin_time_slice = round_robin_time_slice
        self.time_elapased_in_RR= 0

    def has_process(self):
        """Tells us if the CPU has a process"""
        return self.current_proc != None

    def get_current_process(self):
        return self.current_proc

    def in_ctx_switch(self):
        return self.ctx_switch_time_remaining != 0

    def finishing_round_robbin(self):
        return self.round_robin_time_slice - self.time_elapased_in_RR

    def finish_ctx_switch(self):
        self.ctx_switch_time_remaining = 0
        return self.current_proc

    def add_process(self, new_proc):
        if self.current_proc != None:
            print("ERROR! CPU is being fed a process and isn't done with it's old one!")
            exit(1)
        self.current_proc = new_proc
        self.ctx_switch_time_remaining = context_switch_time
        self.time_elapased_in_RR = 0

    def get_time_till_next_event(self):
        if self.current_proc is None:
            return None


        # TODO: check for RR time expiring

        if(self.ctx_switch_time_remaining > 0):
            return self.ctx_switch_time_remaining
        elif(self.current_proc.burst_time_remaining > 0):
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


class ProcessQueue(list):
    def __init__(self, scheduling_algorithm):
        self.scheduling_algo = scheduling_algorithm
        self.total_time_passed = 0

    def add_proc(self, proc):
        # TODO change the sorting in the sim method to be in here
        proc.time_waiting_in_queue = 0
        self.append(proc)
        self.sort_by_scheduling_algo()

    def sort_by_scheduling_algo(self):
        if self.scheduling_algo == "FCFS":
            # do nothing, queue is already in order
            pass
        elif self.scheduling_algo == "SRT":
            self.sort(key=lambda x: x.burst_time)
        elif self.scheduling_algo == "PWA":
            self.sort(key=lambda x: x.priority)

    def update_time(self, time_passed):
        """IN the PWA algorithm if a proc has been waiting in the queue for
        longer than x3 it's burst time increase it's priority by 1"""
        self.total_time_passed += time_passed
        for proc in self:
            # first add the time passed to all the procs
            proc.time_waiting_in_queue += time_passed

            if proc.time_waiting_in_queue >= proc.burst_time * 3:
                # don't go past max priority
                if proc.priority > 0:
                    proc.priority -= 1
                    proc.time_waiting_in_queue = 0
                    # print("proc P%d aged to priority %d" % 
                    #     (proc.proc_num, proc.priority))

        # things may have changed, resort
        self.sort_by_scheduling_algo()

    def get_time_till_next_event(self):
        """ Get the time till the next process enters the queue"""

        if len(self) == 0:
            return None

        # make a copy of the process list and sort it by arrival time
        sorted_by_arrival_time_list = sorted(list, key=lambda x: x.)

        # find the process with the arrival time
        for process in sorted(self

        self.total_time_passed


