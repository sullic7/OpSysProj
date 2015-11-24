context_switch_time = 13

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
        self.ctx_switch_time_remaining = context_switch_time
        self.time_elapased_in_RR = 0

    def get_time_till_next_event(self):
        if self.current_proc is None:
            return None

        RR_time_remaining = self.time_till_round_robin_done()

        if(self.ctx_switch_time_remaining > 0):
            return self.ctx_switch_time_remaining
        else:
            # return the time till the burst is finished, or RR time expires
            # whichever will happen first
            return min(self.current_proc.burst_time_remaining, 
                        RR_time_remaining)

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


class Memory(object):
    def __init__(self, fitting_algorithm):
        self.fitting_algorithm = fitting_algorithm
        self.size = 256
        self.t_memmove = 10
        self.mem = []
        for i in range(self.size):
            self.mem.append(".")

    def can_fit_process_without_defrag(self, new_proc):
        """ This will return True if new_proc can fit into memory without
        a defrag."""
        i = 0
        j = 0
        max_open_mem = 0
        while(j<self.size and self.mem[j]!="."):
            j+=1
        i=j
        while(j < self.size):
            while(j<self.size and self.mem[j]!="."):
                j+=1
                i=j
            if(j-i > max_open_mem):
                max_open_mem = j-i
            j+=1
        if(j==self.size and j-i > max_open_mem):
            max_open_mem = j-i

        if(new_proc.memory_size>max_open_mem):
            return None
        return True

    def add_process(self, new_proc):
        """ Add a new process to memory.
        This assumes the process can fit (because 
        can_fit_process_without_defrag should have been called before)
        and should error out if there's a problem.
        """
        i = 0
        j = 0
        proc_size = new_proc.memory_size
        if(self.fitting_algorithm=='first-fit'):
            while(j<self.size and self.mem[j]!="."):
                j+=1
            i=j
            while(j < self.size):
                while(i<self.size and self.mem[j]!="."):
                    j+=1
                    i=j
                if(j-i > proc_size):
                    break
                j+=1

        elif(self.fitting_algorithm=='next-fit'):
            # TODO: need a last-used index
            count = 0
            start_index = 10 #self.prev_proc
            
            i = start_index
            j = start_index
            while(j<self.size and self.mem[j]!="."):
                j += 1
            i = j
            while(count<=256):
                while(i<self.size and self.mem[j]!="."):
                    j+=1
                    i=j
                if( j-i > proc_size):
                    break
                count+=1
                if( j+1 == self.size and count<256):
                    i = 0
                    j = 0
                else:
                    j += 1
            # must parse all around mem

        elif(self.fitting_algorithm=='best-fit'):
            start_index = 0
            open_size = 256
            while(j<self.size and self.mem[j]!="."):
                j += 1
            i = j
            while(j < self.size):
                while(i<self.size and self.mem[j]!="."):
                    j += 1
                    i = j
                if(j-i > proc_size and j-i < open_size):
                    start_index = i
                    open_size = j-i
                j += 1
            i = start_index

        for k in range(proc_size):
            self.mem[i+k] = new_proc.proc_num
        # print self.fitting_algorithm
        self.show()

    def do_defrag_and_report_time(self):
        """ Defragment memory and report how long it took."""
        i = 0
        j = 0
        while(i<self.size and self.mem[i]=="."):
            i += 1
        units_moved = 0
        while(i < self.size-1):
            i+=1
            if(self.mem[i] != "."):
                self.mem[j] = self.mem[i]
                self.mem[i] = "."
                units_moved += 1
                j += 1
        return self.t_memmove * units_moved

    def remove_process(self, process):
        """ Remove the given process from memory. """
        i = 0
        while(i<self.size and self.mem[i]!=process.proc_num):
            i += 1
        while(i<self.size and i < i+process.memory_size):
            self.mem[i] = "."
            i += 1

    def show(self):
        line = '=' * 32
        print line
        for i in range(self.size/32):
            print ''.join(self.mem[32*i:32*(i+1)])
        print line

    def clear(self):
        for i in range(self.size):
            self.mem[i] = "."
