class Processes(object):
    def __init__(self, procnum, arrival, burstt, numburst, iot, memory):
        self.arrival = arrival
        self.procnum = procnum
        self.burstt = burstt
        self.const_numburst = numburst
        self.iot = iot
        self.mem = memory

        #not const
        self.numburst = numburst
        self.remaining_burstt = burstt
        self.procnum                   #current process
        self.turnaroundt = 0
        self.waitt = 0

    def __repr__(self):
        return str(self.procnum)

    def time_elapse(self):
        if(self.remaining_burstt!=0):
            self.remaining_burstt -= 1

    def burst_reset(self):
        if(self.remaining_burstt==0):
            self.remaining_burstt = self.burstt
        if(self.numburst!=0):
            self.numburst -= 1

    def reset(self):
        self.numburst = self.const_numburst
        self.remaining_burstt = self.burstt
        self.turnaroundt = 0
        self.waitt = 0


class CPUs(object):
    def __init__(self, proc):
        self.iscontextswitch = False
        self.isidle = True
        self.start_t = 0
        self.proc = proc

    def start_process(self, proc, t):
        self.isidle = False
        self.proc = proc
        self.start_t = t

class Memory(object):
    def __init__(self):
        self.size = 256
        self.mem = []
        for i in range(self.size):
            self.mem.append(".")

    def show(self):
        line = '=' * 32
        print line
        for i in range(self.size/32):
            print ''.join(self.mem[32*i:32*(i+1)])
        print line

    def clear(self):
        for i in range(self.size):
            self.mem[i] = "."

    def defrag(self):
        i = 0
        j = 0
        while(i < self.size):
            if(self.mem[i]=="."):
                j = i
                i+=1
                for self.mem[i] != ".":
                if(self.mem[i]!="."):
                    self.mem[j] = self.mem[i]
                    self.mem[i] = "."
            i+=1
            j+=1