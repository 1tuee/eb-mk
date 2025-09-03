# eb-mk
microkernel in rust with QEMU in 46 hours livestream...


specs.
 general architecture 1.

core components: process manager, memory manager, ipc handler, interrupt handler, system call interface.

**more in depth:**

**process manager** - handles the lifecycle of all running programs. creates new processes, terminates finished ones, and uses round-robin scheduling to give each process fair cpu time. maintains a simple process table with basic state information.

**memory manager** - manages physical ram allocation using a basic page-based system. provides simple protection by separating kernel space from user space. handles page allocation and deallocation requests from processes.

 **ipc handler** - implements message passing between processes through send and receive system calls. messages are copied between process address spaces. this is the primary communication mechanism for all system services.

**interrupt handler** - manages hardware interrupts from devices like keyboard, mouse, and timer. routes interrupts to appropriate handlers and manages the timer interrupt used for process scheduling.

 **system call interface** - provides the boundary between user programs and kernel services. implements essential system calls for process creation, memory allocation, and inter-process communication.

