import sys
# methods
# import opsys_sim_components import feed_cpu, sort_queue_by_schedule
# classes
from opsys_sim_components_max import SimulatorProcess, IOSubsystem, CPU, \
ProcessQueue, FutureProcessQueue, Memory
# this is a program to simulate a CPU and IO black box for CSCI 4210

context_switch_time = 13

def load_processes(file_name):
    """take a file and return a list of processes in a list"""
    process_queue = []
    # open the file and read lines from it
    for line in open(file_name, 'r'):
        # parse the input
        # ignore lines that start with #
        if line[0] == '#':
            continue
        # add the process to the list
        process_queue.append(SimulatorProcess(line))

    return process_queue

def get_queue_print_string(queue):
    queue_string = "[Q"
    for process in queue:
        queue_string += " " + str(process.proc_num)
    queue_string += "]"
    return queue_string

def print_event(time, proc, event, queue):
    queue_string = get_queue_print_string(queue)
    print("time %dms: Process %s %s %s" % (time, proc.proc_num, event, queue_string))

def execute_premption(time, process_queue, cpu):
    # take the proc out of the cpu and add a new one from the queue
    old_proc = cpu.preempt_process()
    new_proc = process_queue.pop(0)
    cpu.add_process(new_proc)
    # add the old proc back to the queue and sort it
    process_queue.add_proc(old_proc)

    # little sketchy here for quickness
    event_string = "preempted by Process %s" % new_proc.proc_num
    print_event(time, old_proc, event_string, process_queue)

def check_for_premption(time, process_queue, cpu, scheduling_algo):
    """ returns true if a preemption happened false otherwise"""
    # check if we need to swap the current process using the CPU
    if scheduling_algo == "SRT" and len(process_queue) > 0:
        # lowest remaining time wins
        if cpu.get_current_process().burst_time_remaining > \
                process_queue[0].burst_time_remaining:
            return True

    return False


def run_simulation(future_queue, process_queue, io_subsystem, cpu, scheduling_algo, memory):
    time = 0
    print("time 0ms: Simulator started for %s %s" % 
        (scheduling_algo, get_queue_print_string(process_queue)))

    # keep going while there's processes kicking about
    while ((len(process_queue) != 0) or io_subsystem.has_processes()
        or cpu.has_process()):

        #first check if the CPU is empty, IT MUST BE FED
        if (not cpu.has_process() and len(process_queue) != 0):
            # get the next process from the queue
            proc = process_queue.pop(0)
            # and feed it to the cpu
            cpu.add_process(proc)

        # if there was a preemption execute it and go to next loop
        # this function also executes the preemption if needed
        if check_for_premption(time, process_queue, cpu, scheduling_algo):
            execute_premption(time, process_queue, cpu)
            continue


        # now check what's going to finish next and give it attention
        time_left_on_cpu = cpu.get_time_till_next_event()
        time_left_on_io = io_subsystem.get_time_till_next_event()
        time_till_next_new_proc = future_queue.get_time_till_next_proc_enters()
        # print("times cpu, io, future queue", time_left_on_cpu, time_left_on_io, time_till_next_new_proc)

        # check if we need to add a new process
        if (time_till_next_new_proc is not None and
            (time_left_on_cpu is None or time_till_next_new_proc < time_left_on_cpu) and
            (time_left_on_io is None or time_till_next_new_proc < time_left_on_io)):
            # TODO: add entering a process into memory and the process queue here
            # if a new proc is entering and requires defrag update
            proc = future_queue.get_and_clear_next_proc()
            # process_queue.add_proc(proc) # for now ignore memory for testing

            if memory.can_fit_process_without_defrag(proc):
                process_queue.add_proc(proc)
                memory.add_process(proc)
            else:
                time_passed = memory.do_defrag_and_report_time()
                time += time_passed
                io_subsystem.update_time(time_passed)
                future_queue.updbate_time(time_passed)
                if memory.can_fit_process_without_defrag(proc):
                    process_queue.add_proc(proc)
                    memory.add_process(proc)
                else:
                    print("""I tried to defrag my memory and I still couldn't
                            fit the process. I'm going to throw it away as per
                            The G Man's instructions in class.""")
            continue

        # we don't need to age a process, check if we need to do CPU stuff
        # before we do IO stuff
        if (time_left_on_cpu is not None and time_left_on_cpu < time_left_on_io):
            time_passed = time_left_on_cpu
            time += time_passed
            io_subsystem.update_time(time_passed)
            future_queue.update_time(time_passed)

            # cpu is done first either finish a ctx switch or dump to IO
            if(cpu.in_ctx_switch()):
                proc = cpu.finish_ctx_switch()
                print_event(time, proc, "started using the CPU", process_queue)

            elif(cpu.finishing_round_robin()):
                # CPU is finishing round robbin
                # preempt the proc in the cpu with the next one on the queue
                # then put the process back into the queue
                old_proc = cpu.finish_round_robin()
                new_proc = process_queue.pop(0)
                cpu.add_process(new_proc)
                process_queue.add_proc(old_proc)

                event_string = "preempted by Process %s" % new_proc.proc_num
                print_event(time, old_proc, event_string, process_queue)

            else:
                # cpu is ready now to feed io a process
                proc = cpu.get_and_clear_process()
                # and feed it to IO if needed
                if proc.io_time != 0 and proc.bursts_compleated < proc.num_bursts:
                    # print the event
                    print_event(time, proc, "completed its CPU burst", process_queue)
                    print_event(time, proc, "performing I/O", process_queue)
                    io_subsystem.add_process(proc)
                else:
                    # this process terminates now without IO
                    print_event(time, proc, "terminated", process_queue)
                    memory.remove_process(proc)

        elif(time_left_on_io is not None):
            time_passed = time_left_on_io
            time += time_passed
            cpu.update_time(time_passed)
            io_subsystem.update_time(time_passed)
            future_queue.update_time(time_passed)
            # io is done now so feed the queue
            proc = io_subsystem.get_and_clear_next_process()
            # feed the proc back to the process_queue if needed
            if proc.bursts_compleated < proc.num_bursts:
                process_queue.add_proc(proc)
                # print the event
                print_event(time, proc, "completed I/O", process_queue)
            else:
                print_event(time, proc, "terminated", process_queue)
                memory.remove_process(proc)

    print("time %dms: Simulator for %s ended\n\n" % (time, scheduling_algo))



# main method
if __name__ == "__main__":
    # make sure the args are good
    # if(len(sys.argv) != 2):
    #     print("Usage %s filename" % sys.argv[0])

    
    scheduling_algorithms = ["SRT", "RR"]
    fitting_algorithms = ['first-fit', 'next-fit', 'best-fit']

    for schedule_algo in scheduling_algorithms:
        for fit_algo in fitting_algorithms:
            future_queue = FutureProcessQueue()
            # create a new FutureProcessQueue and add all the loaded processes to it
            future_queue.extend(load_processes("processes.txt"))
            # future_queue.extend(load_processes(sys.argv[1]))

            # sort the future queue by arrivial time
            future_queue.sort(key=lambda x: x.arrival_time)
            # get all the time=0 events from the future queue into the process queue
            process_queue = ProcessQueue(schedule_algo)
            memory = Memory(fit_algo)
            while(future_queue.get_time_till_next_proc_enters() == 0):
                next_proc = future_queue.get_and_clear_next_proc()

                if(next_proc.memory_size>256):
                    # suspend process if memory is too large
                    print("Process "+next_proc.proc_num+" is too large to fit in memory")
                    # TODO: suspend process

                memory.add_process(next_proc)
                # TODO: check for errors loading the proc into memory
                process_queue.add_proc(next_proc)
            

            # print("Process order for %s\n" % algo)
            # for proc in process_queue:
            #     proc.print_self()

            io_subsystem = IOSubsystem()
            cpu = CPU(schedule_algo)

            run_simulation(future_queue, process_queue, io_subsystem, cpu, schedule_algo, memory)
            #reset memory
            memory.clear()
