#!/usr/bin/python

##############################################################################
# Author: Will Klieber
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
##############################################################################

import sys
import os
import re
import pdb
import pprint
import argparse
from collections import OrderedDict

stop = pdb.set_trace

def die(text): 
    sys.stderr.write("Error encountered in function '%s' at line %d:\n" % 
        (sys._getframe(1).f_code.co_name, sys._getframe(1).f_lineno))
    text = str(text)
    if (text[-1] != "\n"):
        text += "\n"
    sys.stderr.write(text + "\n")
    #stop()
    sys.exit(1)

def flatten(L):
    return (item for sublist in L for item in sublist)

def unique(coll):
    hit = set()
    for x in coll:
        if x in hit:
            continue
        hit.add(x)
        yield x

def swap_keys_with_values(d):
    return dict((v, k) for (k, v) in d.iteritems())


################################################################################

class LineReader:
    """Reads a file line-by-line."""
    def __init__(self, file):
        self.file = file
        self.cur = None
        self.line_num = 0
        self.advance()

    def advance(self):
        self.cur = self.file.readline()
        self.line_num += 1
        
    def skip(self, fn_skip):
        while 1:
            if len(self.cur)==0:  # End-Of-File
                return
            cur = self.cur.strip()
            if len(cur)==0 or fn_skip(cur): 
                self.advance()
                continue
            return
        
    def close(self):
        self.file.close()


############################################################

def read_qcir_file(filename):
    try:
        if (filename == '-'):
            filename = "<stdin>"
            file_ptr = sys.stdin
        elif (filename.endswith(".gz")):
            import gzip
            file_ptr = gzip.open(filename, 'r')
        else:
            file_ptr = open(filename, 'r')
    except IOError, e:
        die(str(e))
    in_file = LineReader(file_ptr)

    def LineDie(msg):
        sys.stderr.write("Error on line %i of %s. " % (in_file.line_num, filename))
        sys.stderr.write(msg + "\n")
        sys.exit(1)

    orig_names = {}
    quant_prefix = []
    quant_vars = []
    output_lit = None

    # Read VarName lines
    if Glo.args.keep_var_names:
        while True:
            in_file.skip(lambda line: False)
            cur_line = in_file.cur.strip()
            if not(cur_line.startswith("#VarName ")):
                if cur_line.startswith("#"):
                    in_file.advance()
                    continue
                else:
                    break
            m = re.match('#VarName +([0-9]+)\s*:\s*([*-z]+)\s*$', cur_line)
            if (not m):
                LineDie("Error reading VarName line.")
            orig_names[int(m.group(1))] = m.group(2)
            in_file.advance()

    # Read quantifier blocks and output literal.
    while True:
        in_file.skip(lambda line: line.startswith('#'))
        CurLine = in_file.cur.strip()
        m = re.match('^([A-Za-z]+)[(](.*)[)]$', CurLine)
        if not m:
            LineDie("Expected a line of the form 'quant(var_list)' or 'output(var)'.")
        [qtype, var_list] = m.groups()
        qtype = qtype.lower()
        if qtype == 'output':
            output_lit = var_list
            if re.match('^(-?[A-Za-z0-9_]+)$', output_lit) == None:
                LineDie("Bad output literal: '%s'" % (output_lit,))
            in_file.advance()
            break
        elif qtype not in ['exists', 'forall', 'free']:
            LineDie("Unrecognized token: '%s'.  Expecting 'exists', 'forall', 'free', or 'output'." % (qtype,))
        if qtype == 'free' and quant_prefix != []:
            LineDie("A 'free' block must be outermost.")
        var_list = var_list.replace(',', ' ').split()
        for var in var_list:
            if re.match('^([A-Za-z0-9_]+)$', var) == None:
                LineDie("Bad variable name: '%s'" % (var,))
        quant_prefix.append([qtype, var_list])
        quant_vars += var_list
        in_file.advance()
    
    quant_var_set = set(quant_vars)

    # Assign a positive integer to each quantified variable.
    unassigned_nums = OrderedDict((x,x) for x in range(1, len(quant_vars) + 1))
    qvar_to_num = {}
    # If a variable name is already a number, keep it.
    for qvar in quant_vars:
        try:
            n = int(qvar)
        except:
            continue
        if n > len(quant_vars):
            continue
        qvar_to_num[qvar] = n
        del unassigned_nums[n]
    # Assign numbers to other variables.
    for qvar in quant_vars:
        if qvar in qvar_to_num:
            continue
        n = unassigned_nums.popitem(last=False)[0]
        qvar_to_num[qvar] = n
    # Create the reverse mapping
    Glo.var_num_to_name = swap_keys_with_values(qvar_to_num)
    for (var_num, var_name) in orig_names.items():
        if str(var_num) not in quant_var_set:
            continue
        assert(Glo.var_num_to_name[var_num] == str(var_num))
        Glo.var_num_to_name[var_num] = var_name

    # Replace variable names with numbers in the prefix
    for ii in range(0, len(quant_prefix)):
        (qtype, qvars) = quant_prefix[ii]
        qvars = [qvar_to_num[x] for x in qvars]
        quant_prefix[ii] = (qtype, qvars)
    
    gate_to_def = {}
    Glo.gate_to_orig_names = {}

    def lit_str_to_fmla(arg, die_fn=LineDie):
        # Given a string representing a literal, return the corresponding formula.
        if arg[0] == '-':
            if arg[1] == '-':
                die_fn("Double negation")
            return negate(lit_str_to_fmla(arg[1:]))
        if re.match('^([A-Za-z0-9_]+)$', arg) == None:
            die_fn("Bad variable name: '%s'" % (arg,))
        if arg in quant_var_set:
            return qvar_to_num[arg]
        else:
            try:
                return gate_to_def[arg]
            except KeyError:
                die_fn("Variable '%s' was not quantified and was not defined as a gate variable." % (arg,))

    # Read the gate definitions.
    while True:
        if len(in_file.cur)==0: break
        CurLine = in_file.cur.strip().lower()
        if CurLine.startswith('#') or len(CurLine)==0: 
            in_file.advance()
            continue
        if 1:
        #try:
            m = re.match('([A-Za-z0-9_]+) += +([A-Za-z]+)\((.*)\)', in_file.cur)
            if not m:
                LineDie("Syntax error: expected a line of the form 'gate_var = gate_type(args)'")
            [gate_var, op, args] = m.groups()
            if ';' in args:
                try:
                    (qvars, subexpr) = args.split(';')
                except ValueError:
                    LineDie("Expecting exactly one semicolon.")
                LineDie("Quantified subgates are not implemented yet.")
            args = args.replace(",", " ").split()
            if (op in ["and", "or"]):
                pass
            elif (op == "xor"):
                if len(args) != 2:
                    LineDie("An XOR gate must have exactly 2 inputs.")
            elif (op == "ite"):
                if len(args) != 3:
                    LineDie("An ITE gate must have exactly 3 inputs.")
            else:
                die("Unrecognized operator: '%s'" % op)
            if gate_var in gate_to_def:
                LineDie("Gate '%s' was already defined.")
            gate_fmla = Fmla(op, *[lit_str_to_fmla(x) for x in args])
            gate_to_def[gate_var] = gate_fmla
            Glo.gate_to_orig_names.setdefault(gate_fmla, []).append(gate_var)
        #except Exception, e:
        #    die("Error trying to parse line %i." % (in_file.line_num))
        in_file.advance()

    in_file.close()
    out_fmla = lit_str_to_fmla(output_lit, lambda msg: die("Error looking up output literal: " + msg))
    return [quant_prefix, out_fmla]


##############################################################################

class memoized(object):
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value


class Glo(object):  # for global variables
    pass

def is_lit(x):
    # Returns true if this a literal (as opposed to a formula with logical operators).
    return type(x) == int

class Fmla(tuple):
    id_cache = {}
    idx = {}
    next_idx = 1
    rev_hash = {}
    hash = {}

    def __eq__(self, other): return (self is other)
    def __ne__(self, other): return not(self is other)

    __hash__ = object.__hash__

    def __new__(cls, *args):
        ret = Fmla.id_cache.get(args, None)
        if (ret is None):
            ret = tuple.__new__(Fmla, args)
            if args[0] == 'xor': assert(len(args[1:]) == 2)
            if args[0] == 'ite': assert(len(args[1:]) == 3)
            Fmla.id_cache[args] = ret
            assert(ret not in Fmla.idx)
            Fmla.idx[ret] = Fmla.next_idx
            Fmla.next_idx += 1
        return ret

Fmla_True = Fmla(True)
Fmla_False = Fmla(False)

def negate(fmla):
    if is_lit(fmla):
        return -fmla
    if isinstance(fmla, tuple) and fmla[0] == 'not':
        return fmla[1]
    else:
        assert(isinstance(fmla, tuple))
        return Fmla('not', fmla)
        
##############################################################################

def write_qcir(self, prefix, outf):
    if type(outf) == str:
        with open(outf, 'wt') as f:
            write_qcir(self, prefix, f)
            return
    if (self in (Fmla_True, Fmla_False)):
        q = "exists" if self == Fmla_True else "forall"
        outf.write(
            "#QCIR-G14\n" +
            q + "(g)\n" +
            "output(g)\n")
        outf.close()
        return
    
    nesting_info = get_subformula_print_ordering(self)
    subformulas = [fmla for (order, fmla) in sorted((order, fmla) for (fmla, order) in nesting_info.items())]
    fmla_num = calc_subfmla_nums(subformulas)
    subformulas = [x for x in subformulas if not is_lit(x)]

    outf.write("#QCIR-G14 %i\n" % (max(fmla_num.values()),))

    if Glo.args.keep_var_names:
        for (new_num, old_name) in Glo.var_num_to_name.items():
            if str(new_num) == old_name:
                continue
            outf.write("#VarName %3i : %s\n" % (new_num, old_name))

    for (quantifier, vars) in prefix:
        assert(quantifier in ['exists','forall','free'])
        outf.write("%s(%s)\n" % (quantifier, ", ".join(str(x) for x in vars)))
    outf.write("output(%i)\n" % (fmla_num[self],))

    hit = set()
    prev_nest_lev = None
    for subfmla in subformulas:
        (op, args) = (subfmla[0], subfmla[1:])
        for arg in args:
            assert(is_lit(arg) or (arg in hit))
        hit.add(subfmla)
        hit.add(Fmla('not', subfmla))
        arg_nums = [fmla_num[x] for x in args]
        args = ", ".join([str(x) for x in arg_nums])
        cur_nest_lev = nesting_info[subfmla][0]
        if cur_nest_lev != prev_nest_lev:
            outf.write("# Nesting Level L%i\n" % (cur_nest_lev,))
            prev_nest_lev = cur_nest_lev
        def print_orig_gate_name():
            if not(Glo.args.keep_gate_names):
                return
            orig_gate_names = Glo.gate_to_orig_names.get(subfmla, [])
            if len(orig_gate_names) == 0:
                return
            if len(orig_gate_names) == 1 and orig_gate_names[0] == str(fmla_num[subfmla]):
                return
            outf.write("#%i" % (fmla_num[subfmla],))
            for name in orig_gate_names:
                outf.write(" OrigName_%s" % (name,))
            outf.write("\n")
        print_orig_gate_name()
        outf.write("%i = %s(%s)\n" % (fmla_num[subfmla], op, args))
    outf.close()

def write_dimacs(self, prefix, outf):
    if type(outf) == str:
        with open(outf, 'wt') as f:
            write_dimacs(self, prefix, f)
            return
    if (self in (Fmla_True, Fmla_False)):
        q = "e" if self == Fmla_True else "a"
        outf.write(
            "p cnf 1 1\n" +
            q + " 1 0\n" +
            "1 0\n")
        outf.close()
        return

    nesting_info = get_subformula_print_ordering(self)
    subformulas = [fmla for (order, fmla) in sorted((order, fmla) for (fmla, order) in nesting_info.items())]
    gate_num = calc_subfmla_nums(subformulas)
    subformulas = [x for x in subformulas if not is_lit(x)]
    
    def iter_clauses(fmla):
        (op, args) = (fmla[0], fmla[1:])
        if op == 'xor':
            assert(len(args) == 2)
            op = 'ite'
            args = (args[0], negate(args[1]), args[1])
        #
        if op == 'and':
            # (f <==> (x1 & x2 & x3)) expands to
            # (~x1 | ~x2 | ~x3 | f)  &  (~f | x1)  &  (~f | x2)  &  (~f | x3)
            yield [fmla] + [negate(x) for x in args]
            for x in args:
                yield [negate(fmla), x]
        elif op == 'or':
            # (f <==> (x1 | x2 | x3)) expands to
            # (~f | x1 | x2 | x3)   &   (~x1 | f)  &  (~x2 | f)  &  (~x3 | f)
            yield [negate(fmla)] + [x for x in args]
            for x in args:
                yield [fmla, negate(x)]
        elif op == 'not':
            return
        elif op == 'ite':
            # v <==> (c ? t : f) expands to
            # ((c & t) => v) & ((c & ~t) => ~v) & ((~c & f) => v) & ((~c & ~f) => ~v)
            # which expands to
            # (~c | ~t | v)  &  (~c | t | ~v)  &  (c | ~f | v)  &  (c | f | ~v) 
            (cond, tbra, fbra) = args
            yield [negate(cond), negate(tbra), fmla]
            yield [negate(cond), tbra, negate(fmla)]
            yield [cond, negate(fbra), fmla]
            yield [cond, fbra, negate(fmla)]
        else:
            die("Unknown operator '%s'\n" % (self,))

    p_num_clauses = [0]

    def write_clause(clause):
        clause_str = " ".join(str(gate_num[x]) for x in clause)
        hit = set()
        for lit in clause:
            lit = gate_num[lit]
            if lit in hit:
                die("Repeated literal %i in clause [%s]" % (lit, clause_str))
            if -lit in hit:
                die("Contradictory literals %i and %i in clause [%s]" % (lit, -lit, clause_str))
            hit.add(lit)
        outf.write(clause_str + "  0\n")
        p_num_clauses[0] += 1

    comment = ""
    if Glo.args.keep_var_names:
        VarNameLines = []
        for (new_num, old_name) in Glo.var_num_to_name.items():
            if str(new_num) == old_name:
                continue
            VarNameLines.append("c VarName %3i : %s\n" % (new_num, old_name))
        comment += "".join(VarNameLines)

    #comment = "c leafs=%i, vars=%i, seed=%i" % \
    #    (Glo.args.leafs, Glo.args.vars, Glo.seed)
    #comment += "\n"
    outf.write(comment)
    outf.write((" " * 78) + "\n")  # Reserve space for header
    if len(prefix) != 0:
        gate_vars = []
        for x in subformulas:
            if is_lit(x): continue
            gate_vars.append(gate_num[x])
        if prefix[-1][0] == 'exists':
            prefix[-1][1].extend(gate_vars)
        elif prefix[-1][0] == 'forall':
            prefix.append(['exists', gate_vars])
        else:
            die("Bad quantifier '%s'\n" % (prefix[-1][0],))
    for (quantifier, vars) in prefix:
        quantifier = {'exists':'e', 'forall':'a'}[quantifier]
        outf.write("%s %s  0\n" % (quantifier, " ".join(str(x) for x in vars)))
        
    write_clause([self])
    for fmla in subformulas:
        if is_lit(fmla) or len(fmla) == 1:
            continue
        for clause in iter_clauses(fmla):
            write_clause(clause)
    num_vars = max(gate_num.values())
    try:
        outf.seek(len(comment));
    except IOError:
        die("IO ERROR: Couldn't seek to beginning of output file!")
    outf.write("p cnf %d %d " % (num_vars, p_num_clauses[0]))
    outf.close()


def calc_subfmla_nums(subformulas):
    # Assigns a variable number to each gate, for use in (Q)DIMACS and QCIR.
    unassigned_nums = OrderedDict((x,x) for x in range(1, len(subformulas) + 1))
    fmla_num = {}
    for x in subformulas:
        if is_lit(x):
            fmla_num[x] = x
            fmla_num[-x] = -x
            if abs(x) in unassigned_nums:
                del unassigned_nums[abs(x)]
    for fmla in subformulas:
        try:
            name = Glo.gate_to_orig_names[fmla][0]
            if name == str(int(name)) and (int(name) in unassigned_nums):
                fmla_num[fmla] = int(name)
                fmla_num[Fmla('not', fmla)] = -int(name)
                del unassigned_nums[int(name)]
        except:
            pass
    for fmla in subformulas:
        if is_lit(fmla):
            continue
        if fmla in fmla_num:
            continue
        next_fmla_num = unassigned_nums.popitem(last=False)[0]
        fmla_num[fmla] = next_fmla_num
        fmla_num[Fmla('not', fmla)] = -next_fmla_num
        #print("%5i = fmla_num[%s]" % (next_fmla_num, dol_fmla(fmla)))
    return fmla_num


def get_subformula_print_ordering(fmla, nest_lev=None, p_next_idx=None):
    # Determines the order in which the gate definitions are printed.
    # For QCIR, gates must be defined before they are used.
    # Subformulas are ordered by (nesting_level, index), where nesting_level is
    # the tree depth of the subformula and index is the order in which the
    # subformula was encountered in a depth-first search.
    if nest_lev is None:
        nest_lev = {}
        p_next_idx = [1]
    if is_lit(fmla):
        cur_idx = p_next_idx[0]
        p_next_idx[0] += 1
        nest_lev[fmla] = (1, cur_idx)
        return nest_lev
    if len(fmla) == 1:
        die("Unexpected constant: %r\n" % (fmla,))
    if fmla in nest_lev:
        return nest_lev
    if fmla[0] == 'not':
        return get_subformula_print_ordering(fmla[1], nest_lev, p_next_idx)
    max_sub_level = 0
    for arg in fmla[1:]:
        get_subformula_print_ordering(arg, nest_lev, p_next_idx)
        if isinstance(arg, tuple) and arg[0] == 'not':
            arg_lev = nest_lev[arg[1]][0]
        else:
            arg_lev = nest_lev[arg][0]
        max_sub_level = max(max_sub_level, arg_lev)
    cur_idx = p_next_idx[0]
    p_next_idx[0] += 1
    nest_lev[fmla] = (max_sub_level + 1, cur_idx)
    return nest_lev

##############################################################################


class DeadExc(Exception):
    pass

@memoized
def simplify(fmla):
    if is_lit(fmla):
        return fmla
    (op, args) = (fmla[0], fmla[1:])
    if fmla in [Fmla_True, Fmla_False]:
        return fmla
    args = [simplify(arg) for arg in args]

    if op in ('and', 'or'):
        if op == 'and':  (base, negbase) = (Fmla_True, Fmla_False)
        elif op == 'or': (base, negbase) = (Fmla_False, Fmla_True)
        def expand_arg(arg):
            if arg == base:
                return ()
            if arg == negbase:
                raise DeadExc
            else:
                return (arg,)
        ret = None
        try:
            args = tuple(flatten([expand_arg(a) for a in args]))
        except DeadExc:
            ret = negbase
        if ret == None:
            if   len(args) == 0:  ret = base
            elif len(args) == 1:  ret = args[0]
            else:
                ret = Fmla(op, *unique(args))
                if len(args) > 6:
                    arg_coll = set(args)
                else:
                    arg_coll = args
                for arg in args:
                    if negate(arg) in arg_coll:
                        ret = negbase
    elif op == 'not':
        if   args[0] == Fmla_True:  ret = Fmla_False
        elif args[0] == Fmla_False: ret = Fmla_True
        else: ret = Fmla(op, *args)
    elif op == 'xor':
        assert(len(args) == 2)
        if args[1] in (Fmla_True, Fmla_False):
            args = [args[1], args[0]]
        #
        if args[0] == Fmla_False:
            ret = args[1]
        elif args[0] == Fmla_True:
            ret = negate(args[1])
        else:
            ret = Fmla(op, *args)
    elif op == 'ite':
        (test, tbra, fbra) = args
        if   test == Fmla_True:    ret = tbra
        elif test == Fmla_False:   ret = fbra
        elif tbra == Fmla_True:    ret = simplify(Fmla('or',  test,         fbra))
        elif fbra == Fmla_True:    ret = simplify(Fmla('or',  negate(test), tbra))
        elif tbra == Fmla_False:   ret = simplify(Fmla('and', negate(test), fbra))
        elif fbra == Fmla_False:   ret = simplify(Fmla('and', test,         tbra))
        else: ret = Fmla(op, *args)
    else:
        die("Unknown operator: '%s'\n" % op)
    orig_gate_names = Glo.gate_to_orig_names.get(fmla, None)
    if orig_gate_names:
        Glo.gate_to_orig_names[ret] = orig_gate_names
    return ret

@memoized
def to_andor(fmla):
    if is_lit(fmla):
        return fmla
    (op, args) = (fmla[0], fmla[1:])
    if len(args) == 0:
        return fmla
    args = [to_andor(arg) for arg in args]
    if op in ('and', 'or', 'not'):
        ret = Fmla(op, *args)
    elif op == 'xor':
        ret = to_andor(Fmla('ite', args[0], negate(args[1]), args[1]))
    elif op == 'ite':
        (sel, y, z) = args
        ret = Fmla('and', Fmla('or', negate(sel), y), Fmla('or', sel, z))
    else:
        die("Unknown operator: '%s'\n" % op)
    orig_gate_names = Glo.gate_to_orig_names.get(fmla, None)
    if orig_gate_names:
        Glo.gate_to_orig_names[ret] = orig_gate_names
    return ret


def vars_in_fmla(fmla, var_set=None, hit=None):
    if (var_set is None):
        var_set = set()
        hit = set()
    if fmla in hit: 
        return var_set
    if is_lit(fmla):
        var_set.add(abs(fmla))
        return var_set
    args = fmla[1:]
    for arg in args:
        vars_in_fmla(arg, var_set, hit)
    return var_set

    

def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=str)
    parser.add_argument("-o", type=str, dest="outfile", required=True, help="output file")
    parser.add_argument("--keep-var-names", choices=[0,1], type=int, default=1, dest="keep_var_names",
        help="Use VarName comment lines")
    parser.add_argument("--keep-gate-names", choices=[0,1], type=int, default=0, dest="keep_gate_names")
    parser.add_argument("--native-ite", choices=[0,1], type=int, default=0, dest="native_ite",
        help="Use special 4-clause encoding for XOR and ITE gates")
    parser.add_argument("--reclim", type=int, default=2000, help="recursion limit " + 
        "(increase this if Python dies with 'RuntimeError: maximum recursion depth exceeded')")
    parser.add_argument("--fmt", type=str, help="output file format ('qcir', 'qdimacs')")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    Glo.args = args

    if args.fmt is None:
        args.fmt = args.outfile.split('.')[-1]

    sys.setrecursionlimit(args.reclim)

    [quant_prefix, fmla] = read_qcir_file(args.input_file)
    
    orig_fmla = fmla

    if not(args.native_ite):
        fmla = to_andor(fmla)

    fmla = simplify(fmla)

    if args.fmt == 'qcir':
        write_qcir(fmla, quant_prefix, args.outfile)
    elif args.fmt == 'qdimacs':
        write_dimacs(fmla, quant_prefix, args.outfile)
    else:
        die("Unknown format '%s'.\nValid choices for '--fmt' option are 'qcir' and 'qdimacs'.\n" % (args.fmt,))
    return

if __name__ == "__main__":
    main()

