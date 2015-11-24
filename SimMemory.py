class Memory(object):
    def __init__(self, fitting_algorithm, size, memory_move_time):
        self.fitting_algorithm = fitting_algorithm
        self.size = size
        self.t_memmove = memory_move_time
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