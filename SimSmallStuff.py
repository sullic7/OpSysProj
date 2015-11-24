# Authors:
# Max Llewellyn
# Caroline Sullivan

class SimulatorProcess:
    """This class holds info about a process. How long it wants for CPU
    bursts, how long each burst is and how long it takes to do IO."""

    def __init__(self, info_string):
        # parse the string that has info about the process
        # string format 
        # <proc-num>|<arrival-time>|<burst-time>|<num-burst>|<io-time>|<memory>
        values = info_string.strip().split("|")
        self.proc_num = values[0]
        self.arrival_time = int(values[1])
        self.burst_time = int(values[2])
        self.num_bursts = int(values[3])
        self.io_time = int(values[4])
        self.memory_size = int(values[5])

        # set up vars to track remaining time
        self.burst_time_remaining = self.burst_time

        # set up analytic variables
        self.bursts_compleated = 0
        self.cpu_burst_time = 0
        self.turnaround_time = 0
        self.wait_time = 0
        self.time_waiting_in_queue = 0


    def __str__(self):
        return ("<proc-num> %c, <arrival-time>%d, <burst-time> %d, <num-burst> %d, <io-time> %d, <memory> %d, <bursts_compl> %d, <burst_time_compl> %d" % 
            (self.proc_num, self.arrival_time, self.burst_time, self.num_bursts, self.io_time, self.memory_size, self.bursts_compleated, self.burst_time_remaining))


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


class ProcessQueue(list):
    def __init__(self, scheduling_algorithm):
        self.scheduling_algo = scheduling_algorithm
        self.total_time_passed = 0

    def add_proc(self, proc):
        self.append(proc)
        self.sort_by_scheduling_algo()

    def sort_by_scheduling_algo(self):
        if self.scheduling_algo == "FCFS":
            # do nothing, queue is already in order
            pass
        elif self.scheduling_algo == "SRT":
            self.sort(key=lambda x: x.burst_time)

    def update_time(self, time_passed):
        """IN the PWA algorithm if a proc has been waiting in the queue for
        longer than x3 it's burst time increase it's priority by 1"""
        for proc in self:
            # first add the time passed to all the procs
            proc.time_waiting_in_queue += time_passed
            proc.wait_time += time_passed
            proc.turnaround_time += time_passed

        self.sort_by_scheduling_algo()


class FutureProcessQueue(list):
    """ Hold a list of processes and have functions to give them
    out to the rest of the simulation when the should enter the system.
    """
    def __init__(self):
        self.total_time_passed = 0

    def get_and_clear_next_proc(self):
        """ Get the next process that's going to enter the system
        and remove it from the future queue.
        """
        return self.pop(0)

    def get_time_till_next_proc_enters(self):
        if len(self) == 0:
            return None
        # Return how many ms in the future the next process will
        # arrive in.
        return self[0].arrival_time - self.total_time_passed

    def update_time(self, time_passed):
        self.total_time_passed += time_passed

class Stats:
    def __init__(self):
        self.cpu_burst_times = []
        self.turnaround_times = []
        self.wait_times = []
        self.ctx_switches = 0
        self.num_bursts_total = 0
