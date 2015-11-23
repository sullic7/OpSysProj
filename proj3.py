import sys
from opsys_sim_components import Processes, CPUs, Memory

def readfile(procfile):
    F = open(procfile)
    readqueue = [] #queue of processes in order of appearance
    for f in F:
        if (not (f[0]=="#") | (f[0]=="\n")): #ignore blank and commented lines
            proc = f.split("|")
            procnum = proc[0]
            temp = Processes(procnum,int(proc[1]),int(proc[2]),int(proc[3]),int(proc[4]),int(proc[5]))
            readqueue.append(temp)
    F.close()
    return readqueue

def output(t, current, outstr, queue):
    if (len(queue)==0):
        print "time %dms: Process '%s' %s [Q]" % (t, current, outstr)
    else:
        print "time %dms: Process '%s' %s [Q %s]" % (t, current, outstr, str(queue).strip('[]').replace(',',''))

def output_to_file(algo, avg_burstt, waitt, turnaroundt, tot_cs):
    outfile = open("simout.txt", 'a')
    outfile.write("Algorithm %s\n" % algo)
    outfile.write("-- average CPU burst time: %.2f ms\n" % avg_burstt)
    outfile.write("-- average wait time: %.2f ms\n" % waitt)
    outfile.write("-- average turnaround time: %.2f ms\n" % turnaroundt)
    outfile.write("-- total number of context switches: %d\n\n" % tot_cs)
    outfile.close()

def resetproc(procqueue):
    for p in procqueue:
        p.reset()

def RR(t_cs, t_slice, queue, avg_burstt):
    tot_proc = len(queue)   #total number of processes
    t = 0                   #elapsed time (ms)
    tot_cs = 0              #total number of context switches
    turnaround = 0
    num_turnaround = 0
    wait = 0
    CPU = CPUs(queue[0])
    CPU.start_process(queue[0],t)
    CPU.iscontextswitch = True

    mem = Memory()

    terminated = 0
    IO = {}
    print "time %dms: Simulator started for RR [Q %s]" % (t, str(queue).strip('[]').replace(',',''))

    while (True): #as long as there are still processes in queue
        if (CPU.start_t == t-1): #if CPU free
            #if CPU not idle
            if (len(queue)>0):
                #process is taken from queue to be used by CPU
                CPU.start_process(queue[0],t-1)
                CPU.iscontextswitch = True
                #calculate wait
                wait += t - CPU.proc.waitt
                #calculate turnaround
                num_turnaround += 1
            else:
                CPU.start_t = t
                CPU.isidle = True

        elif ((t-CPU.start_t) == t_cs): #CPU running
            queue.pop(0) #take off process from beginning of queue
            output(t, CPU.proc.procnum, "started using the CPU", queue)
            CPU.proc.time_elapse()
            CPU.iscontextswitch = False
            tot_cs += 1

        elif ((CPU.proc.remaining_burstt>0)and(not CPU.iscontextswitch)and(not CPU.isidle)): #while CPU runs
            CPU.proc.time_elapse()


        elif (CPU.proc.remaining_burstt == 0): #process finishes in CPU
            CPU.start_t = t #CPU now free
            turnaround += t - CPU.proc.turnaroundt
            CPU.proc.turnaroundt = t + CPU.proc.iot
            CPU.proc.burst_reset()
            if(CPU.proc.numburst==0): #skip I/O and end simulator after final CPU burst
                terminated += 1
                output(t, CPU.proc.procnum, "terminated", queue)
                if (terminated == tot_proc):
                    print "time %dms: Simulator for RR ended [Q]\n" %t
                    break;

            else: #performs I/O
                IO[CPU.proc] = CPU.proc.iot
                output(t, CPU.proc.procnum, "completed its CPU burst", queue)
                output(t, CPU.proc.procnum, "performing I/O", queue)

        temp = []
        for i in IO:
            if(IO[i]==0):
                temp.append(i)
            else:
                IO[i] -= 1

        while (len(temp)>0):
            first = min(temp, key=lambda x: x.procnum)
            if (first.numburst == 0): #terminate or replace on queue if process has more bursts
                output(t, first.procnum, "terminated", queue)
            else:
                queue.append(first)
                first.waitt = t
                output(t, first.procnum, "completed I/O", queue)
            IO.pop(first) #pop finished process
            temp.remove(first)

        if((CPU.proc.numburst!=0) and len(queue)>0 and (t-CPU.start_t==t_slice)): #check for preemption
            CPU.start_t = t
            CPU.proc.waitt = t+1
            #process is preempted
            temp = queue.pop(0)
            queue.insert(0,CPU.proc)
            print "time %dms: Process '%s' preempted by Process '%s' [Q %s]" % (t, CPU.proc, temp, str(queue).strip('[]').replace(',',''))
            queue.insert(0,temp)

        t+=1

    for i in range(10):
        mem.mem[5+i] = "B"
    mem.show()
    mem.defrag()
    mem.show()

    avg_wait = wait/float(tot_cs)
    avg_turnaround = turnaround/float(num_turnaround)
    output_to_file("RR", avg_burstt, avg_wait, avg_turnaround, tot_cs)

def SRT(t_cs, readqueue, avg_burstt):
    queue = sorted(readqueue, key = lambda x: x.burstt)
    tot_proc = len(queue)
    tot_bursts = 0
    for q in queue:
        tot_bursts += q.numburst
    tot_cs = 0 #total number of context switches
    turnaround = 0
    wait = 0
    t = 0 #elapsed time (ms)
    CPU = CPUs(queue[0])
    CPUt = 0
    CPUP = queue[0]
    terminated = 0
    times = {}
    print "time %dms: Simulator started for SRT [Q %s]" % (t, str(queue).strip('[]').replace(',',''))

    while (True): #as long as there are still processes in queue
        if (CPUt == t-1): #if CPU free
            #if CPU not idle
            if (len(queue)>0):
                #process is taken from queue to be used by CPU
                CPUP = queue[0]
                #calculate wait
                wait += t-CPUP.waitt
            else:
                CPUt = t

        elif ((t-CPUt) == t_cs): #CPU starts running
            queue.pop(0)
            output(t, CPUP.procnum, "started using the CPU", queue)
            CPUP.time_elapse()
            tot_cs += 1

        elif ((CPUP.remaining_burstt>0)and((t-CPUt)>t_cs)): #while CPU runs
            CPUP.time_elapse()

        elif (CPUP.remaining_burstt == 0): #process finishes in CPU
            CPUt = t #CPU now free
            turnaround += t - CPUP.turnaroundt
            CPUP.turnaroundt = t + CPUP.iot
            CPUP.burst_reset()
            if(CPUP.numburst==0): #skip I/O and end simulator after final CPU burst
                terminated += 1
                output(t, CPUP.procnum, "terminated", queue)
                if (terminated == tot_proc):
                    print "time %dms: Simulator for SRT ended [Q]\n" %t
                    break;

            else: #performs I/O
                times[CPUP] = CPUP.iot
                if(CPUP.iot!=0):
                    output(t, CPUP.procnum, "completed its CPU burst", queue)
                    output(t, CPUP.procnum, "performing I/O", queue)

        temp = []
        for i in times:
            if(times[i]==0):
                temp.append(i)
            else:
                times[i] -= 1

        while (len(temp)>0):
            first = min(temp, key=lambda x: x.procnum)
            if (first.numburst == 0): #terminate or replace on queue if process has more bursts
                output(t, first.procnum, "terminated", queue)
            else:
                queue.append(first)
                first.waitt = t+1
                #sort queue by SRT
                queue = sorted(queue, key = lambda x: x.remaining_burstt)
                output(t, first.procnum, "completed I/O", queue)

            times.pop(first) #pop finished process
            temp.remove(first)

        if((CPUP.numburst!=0) and len(queue)>0 and (CPUP.remaining_burstt > queue[0].remaining_burstt)): #check for preemption
            CPUt = t
            CPUP.waitt = t+1
            #process is preempted
            temp = queue.pop(0)
            queue.insert(0,CPUP)
            print "time %dms: Process '%s' preempted by Process '%s' [Q %s]" % (t, CPUP, temp, str(queue).strip('[]').replace(',',''))
            queue.insert(0,temp)
        t+=1
    avg_wait = wait/float(tot_bursts)
    avg_turnaround = turnaround/float(tot_bursts)
    output_to_file("SRT", avg_burstt, avg_wait, avg_turnaround, tot_cs)

if __name__ == "__main__":
    #read file
    #if file entered into command line
    if(len(sys.argv) > 1):
        myfile = sys.argv[1]
    else:
        myfile = "processes.txt"

    outfile = open("simout.txt", 'w')

    #proctdict contains each process as <proc-num>: Process object
    readqueue = readfile(myfile)
    
    t_cs = 13 #time (ms) it takes to perform a context switch
    tot_burstt = 0
    num = 0
    for q in readqueue:
        tot_burstt += q.burstt*q.const_numburst
        num+=q.const_numburst
    avg_burstt = tot_burstt/float(num)

    #Round-Robin
    t_slice = 80
    queue = list(readqueue)
    RR(t_cs, t_slice, queue, avg_burstt)

    #SRT
    resetproc(readqueue)
    queue = list(readqueue)
    #SRT(t_cs, queue, avg_burstt)