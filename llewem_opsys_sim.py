import sys
# methods
# import opsys_sim_components import feed_cpu, sort_queue_by_schedule
# classes
from opsys_sim_components_max import SimulatorProcess, IOSubsystem, CPU, ProcessQueue
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
    print("time %dms: P%d %s %s" % (time, proc.proc_num, event, queue_string))

def execute_premption(time, process_queue, cpu, scheduling_algo):
    # take the proc out of the cpu and add a new one from the queue
    old_proc = cpu.preempt_process()
    new_proc = process_queue.pop(0)
    cpu.add_process(new_proc)
    # add the old proc back to the queue and sort it
    process_queue.add_proc(old_proc)
    # little sketchy here for quickness
    event_string = "preempted by P%d" % new_proc.proc_num
    print_event(time, old_proc, event_string, process_queue)

def check_for_premption(time, process_queue, cpu, scheduling_algo):
    """ returns true if a preemption happened false otherwise"""
    # check if we need to swap the current process using the CPU
    if scheduling_algo == "SRT" and len(process_queue) > 0:
        # lowest remaining time wins
        if cpu.get_current_process().burst_time_remaining > \
                process_queue[0].burst_time_remaining:
            execute_premption(time, process_queue, cpu, scheduling_algo)
            return True

    if scheduling_algo == "PWA" and len(process_queue) > 0:
        # lowest priority wins
        if cpu.get_current_process().priority > process_queue[0].priority:
            execute_premption(time, process_queue, cpu, scheduling_algo)
            return True

    return False


def run_simulation(process_queue, io_subsystem, cpu, scheduling_algo):
    time = 0
    print("time 0ms: Simulator started for %s %s" % 
        (scheduling_algo, get_queue_print_string(process_queue)))

    # keep going while there's processes kicking about
    while ((len(process_queue) != 0) or io_subsystem.has_processes()
        or cpu.has_process()):

        #first check if the CPU is empty, IT MUST BE FEED
        if (not cpu.has_process() and len(process_queue) != 0):
            # feed the CPU a process (no time taken yet)
            # get the next process from the queue
            proc = process_queue.pop(0)
            # and feed it to the cpu
            cpu.add_process(proc)

        # if there was a preemption go to next loop
        if check_for_premption(time, process_queue, cpu, scheduling_algo):
            continue

        # now check what's going to finish next and give it attention
        time_left_on_cpu = cpu.get_time_till_next_event()
        time_left_on_io = io_subsystem.get_time_till_next_event()
        time_left_on_process_queue = process_queue.get_time_till_next_event()
        # print("times cpu, io, queue", time_left_on_cpu, time_left_on_io, time_left_on_process_queue)

        # check if we need to age a process first
        if (time_left_on_process_queue is not None and
            (time_left_on_cpu is None or time_left_on_process_queue < time_left_on_cpu) and
            (time_left_on_io is None or time_left_on_process_queue < time_left_on_io)):

            # print("aging processes in queue")
            time_passed = time_left_on_process_queue
            time += time_passed
            cpu.update_time(time_passed)
            io_subsystem.update_time(time_passed)
            process_queue.update_time(time_passed)
            # go to the next loop
            continue

        # we don't need to age a process, check if we need to do CPU stuff
        # before we do IO stuff
        if (time_left_on_cpu is not None and time_left_on_cpu < time_left_on_io):
            time_passed = time_left_on_cpu
            time += time_passed
            io_subsystem.update_time(time_passed)
            process_queue.update_time(time_passed)

            # cpu is done first either finish a ctx switch or dump to IO
            if(cpu.in_ctx_switch()):
                proc = cpu.finish_ctx_switch()
                print_event(time, proc, "started using the CPU", process_queue)
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

        elif(time_left_on_io is not None):
            time_passed = time_left_on_io
            time += time_passed
            cpu.update_time(time_passed)
            io_subsystem.update_time(time_passed)
            process_queue.update_time(time_passed)
            # io is done now so feed the queue
            proc = io_subsystem.get_and_clear_next_process()
            # feed the proc back to the process_queue if needed
            if proc.bursts_compleated < proc.num_bursts:
                process_queue.add_proc(proc)
                # print the event
                print_event(time, proc, "completed I/O", process_queue)
            else:
                print_event(time, proc, "terminated", process_queue)

    print("time %dms: Simulator for %s ended\n\n" % (time, scheduling_algo))



# main method
if __name__ == "__main__":
    # make sure the args are good
    # if(len(sys.argv) != 2):
    #     print("Usage %s filename" % sys.argv[0])

    
    scheduling_algorithms = ["FCFS", "RR"]

    for algo in scheduling_algorithms:
        # process_queue = load_processes(sys.argv[1])
        # create a new ProcessQueue and add all the loaded processes to it
        process_queue = ProcessQueue(algo)
        process_queue.extend(load_processes("input_file.txt"))
        process_queue.sort_by_scheduling_algo()

        # print("Process order for %s\n" % algo)
        # for proc in process_queue:
        #     proc.print_self()
        io_subsystem = IOSubsystem()
        cpu = CPU(algo)
        run_simulation(process_queue, io_subsystem, cpu, algo)
