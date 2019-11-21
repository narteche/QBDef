#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:54:40 2019

@author: alephnoell
"""
from enum import Enum

class Quantifier(Enum):
    EXISTS = 'E'
    FORALL = 'A'
    
class Operator(Enum):
    OR = 'or'
    AND = 'and'
    XOR = 'xor'
    
class Format(Enum):
    circuit = 'circuit'
    CNF = 'CNF'

class Literal:
    def __init__(self, var):
        self.var = var
        self.neg = False
        
    def get_var(self):
        return self.var
    
    def negate(self):
        self.neg = True
        
    def is_negated(self):
        return self.neg

class Block:
    def __init__(self, name):
        self.name = name
        self.body = []
    
    def get_body(self):
        return self.body
    
    def set_body(self, newBody):
        self.body = newBody
        
    def add_to_body(self, lit):
        self.body.append(lit)
    
class QuantifierBlock(Block):
    def __init__(self, name):
        super().__init__(name)
        self.quantifier = Quantifier.EXISTS
    
    def quantify(self, Q):
        self.quantifier = Q
        
    def is_existential(self):
        return self.quantifier == Quantifier.EXISTS
    
    def is_universal(self):
        return not self.is_existential(self)
    
class OperatorBlock(Block):
    def __init__(self, name):
        super().__init__(name)
        self.operator = Operator.OR
        
    def set_operator(self, op):
        self.operator = op
        
    def get_operator(self):
        return self.operator
    
class BlockGroup:
    def __init__(self, blockGroup):
        self.group = blockGroup
    
    def get_group(self):
        return self.group
    
    def set_group(self, newBlockGroup):
        self.group = newBlockGroup
        
    def add_to_group(self, block):
        self.group.append(block)

class Parameter:
    def __init__(self, p, pType, cons):
        self.param = p
        self.value = None
        self.type = pType
        self.cons = cons
        
        
    def set_param(self, p):
        self.param = p
    
    def get_param(self):
        return self.param
    
    def set_value(self, v):
        self.value = v
    
    def get_value(self):
        return self.value
    
    def set_type(self, t):
        self.type = t
        
    def get_type(self):
        return self.type
    
    def get_constraints(self):
        return self.cons
    
    def add_contraint(self, c):
        self.cons.append(c)

class QBF:
    def __init__(self):
        self.name = ""
        self.format = ""
        self.parameters = []
        self.variables = []
        self.quantifierBlocks = []
        self.operatorBlocks = []
        self.quantifierPrefix = None
        self.formulaOutput = None
        
    def set_name(self, n):
        self.name = n
        
    def get_name(self):
        return self.name
    
    def set_format(self, f):
        if f == 'CNF':
            self.format = Format.CNF
        else:
            self.format = Format.circuit
        
    def get_format(self):
        return self.format
    
    def get_parameters(self):
        return self.parameters
    
    def add_parameter(self, p, t, c):
        self.parameters.append(Parameter(p, t, c))
        
