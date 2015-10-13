#if defined(__ARM_ARCH_4__) || defined (__ARM_ARCH_4T__)
# define call_reg(x) "mov lr, pc ; bx " #x "\n"
#else
/* ARM >= 5 */
# define call_reg(x) "blx " #x "\n"
#endif

static void *slp_switch(void *(*save_state)(void*, void*),
                        void *(*restore_state)(void*, void*),
                        void *extra)
{
  void *result;
  /*
      seven registers to preserve: r2, r3, r7, r8, r9, r10, r11
      registers marked as clobbered: r0, r1, r4, r5, r6, r12, lr
      others: r13 is sp; r14 is lr; r15 is pc
  */

  __asm__ volatile (

    /* align the stack and save 7 more registers explicitly */
    "mov r0, sp\n"
    "and r1, r0, #-16\n"
    "mov sp, r1\n"
    "push {r0, r2, r3, r7, r8, r9, r10, r11}\n"   /* total 8, still aligned */

    /* save values in callee saved registers for later */
    "mov r4, %[restore_state]\n"  /* can't be r0 or r1: marked clobbered */
    "mov r5, %[extra]\n"          /* can't be r0 or r1 or r4: marked clob. */
    "mov r3, %[save_state]\n"     /* can't be r0, r1, r4, r5: marked clob. */
    "mov r0, sp\n"        	/* arg 1: current (old) stack pointer */
    "mov r1, r5\n"        	/* arg 2: extra                       */
    call_reg(r3)		/* call save_state()                  */

    /* skip the rest if the return value is null */
    "cmp r0, #0\n"
    "beq zero\n"

    "mov sp, r0\n"			/* change the stack pointer */

	/* From now on, the stack pointer is modified, but the content of the
	stack is not restored yet.  It contains only garbage here. */
    "mov r1, r5\n"       	/* arg 2: extra                       */
                /* arg 1: current (new) stack pointer is already in r0*/
    call_reg(r4)		/* call restore_state()               */

    /* The stack's content is now restored. */
    "zero:\n"

    "pop {r1, r2, r3, r7, r8, r9, r10, r11}\n"
    "mov sp, r1\n"
    "mov %[result], r0\n"

    : [result]"=r"(result)	/* output variables */
	/* input variables  */
    : [restore_state]"r"(restore_state),
      [save_state]"r"(save_state),
      [extra]"r"(extra)
    : "r0", "r1", "r4", "r5", "r6", "r12", "lr",
      "memory", "cc", "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7"
  );
  return result;
}
