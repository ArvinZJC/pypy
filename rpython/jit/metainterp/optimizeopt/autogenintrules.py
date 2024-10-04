# Generated by ruleopt/generate.py, don't edit!

from rpython.jit.metainterp.history import ConstInt
from rpython.jit.metainterp.optimizeopt.util import (
    get_box_replacement)
from rpython.jit.metainterp.resoperation import rop

from rpython.rlib.rarithmetic import LONG_BIT, r_uint, intmask, ovfcheck, uint_mul_high

class OptIntAutoGenerated(object):
    def optimize_INT_ADD(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        # add_reassoc_consts: int_add(int_add(x, C1), C2) => int_add(x, C)
        arg_0_int_add = self.optimizer.as_operation(arg_0, rop.INT_ADD)
        if arg_0_int_add is not None:
            arg_0_int_add_0 = get_box_replacement(arg_0.getarg(0))
            b_arg_0_int_add_0 = self.getintbound(arg_0_int_add_0)
            arg_0_int_add_1 = get_box_replacement(arg_0.getarg(1))
            b_arg_0_int_add_1 = self.getintbound(arg_0_int_add_1)
            if b_arg_0_int_add_1.is_constant():
                C_arg_0_int_add_1 = b_arg_0_int_add_1.get_constant_int()
                if b_arg_1.is_constant():
                    C_arg_1 = b_arg_1.get_constant_int()
                    C = intmask(r_uint(C_arg_0_int_add_1) + r_uint(C_arg_1))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_0_int_add_0, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    return
        # add_reassoc_consts: int_add(C2, int_add(x, C1)) => int_add(x, C)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            arg_1_int_add = self.optimizer.as_operation(arg_1, rop.INT_ADD)
            if arg_1_int_add is not None:
                arg_1_int_add_0 = get_box_replacement(arg_1.getarg(0))
                b_arg_1_int_add_0 = self.getintbound(arg_1_int_add_0)
                arg_1_int_add_1 = get_box_replacement(arg_1.getarg(1))
                b_arg_1_int_add_1 = self.getintbound(arg_1_int_add_1)
                if b_arg_1_int_add_1.is_constant():
                    C_arg_1_int_add_1 = b_arg_1_int_add_1.get_constant_int()
                    C = intmask(r_uint(C_arg_1_int_add_1) + r_uint(C_arg_0))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_1_int_add_0, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    return
        # add_reassoc_consts: int_add(int_add(C1, x), C2) => int_add(x, C)
        arg_0_int_add = self.optimizer.as_operation(arg_0, rop.INT_ADD)
        if arg_0_int_add is not None:
            arg_0_int_add_0 = get_box_replacement(arg_0.getarg(0))
            b_arg_0_int_add_0 = self.getintbound(arg_0_int_add_0)
            arg_0_int_add_1 = get_box_replacement(arg_0.getarg(1))
            b_arg_0_int_add_1 = self.getintbound(arg_0_int_add_1)
            if b_arg_0_int_add_0.is_constant():
                C_arg_0_int_add_0 = b_arg_0_int_add_0.get_constant_int()
                if b_arg_1.is_constant():
                    C_arg_1 = b_arg_1.get_constant_int()
                    C = intmask(r_uint(C_arg_0_int_add_0) + r_uint(C_arg_1))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_0_int_add_1, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    return
        # add_reassoc_consts: int_add(C2, int_add(C1, x)) => int_add(x, C)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            arg_1_int_add = self.optimizer.as_operation(arg_1, rop.INT_ADD)
            if arg_1_int_add is not None:
                arg_1_int_add_0 = get_box_replacement(arg_1.getarg(0))
                b_arg_1_int_add_0 = self.getintbound(arg_1_int_add_0)
                arg_1_int_add_1 = get_box_replacement(arg_1.getarg(1))
                b_arg_1_int_add_1 = self.getintbound(arg_1_int_add_1)
                if b_arg_1_int_add_0.is_constant():
                    C_arg_1_int_add_0 = b_arg_1_int_add_0.get_constant_int()
                    C = intmask(r_uint(C_arg_1_int_add_0) + r_uint(C_arg_0))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_1_int_add_1, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    return
        return self.emit(op)
