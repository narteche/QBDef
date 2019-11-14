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
    
class QuantifierBlock:
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

class QBF:
    def __init__(self, name, formType):
        self.name = name
        self.formType = formType
        self.variables = []
        self.quantifierBlocks = []
        self.operatorBlocks = []
        self.quantifierPrefix = None
        self.formulaOutput = None