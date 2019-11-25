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
    
class ParamType(Enum):
    natural = 'natural'
    
class Parameter:
    
    def __init__(self, pName = "", pType=ParamType.natural, pValue = None, pRest = []):
        self.paramName = pName
        self.paramType = pType
        self.paramValue = pValue
        self.paramRestrictions = pRest
        
    def get_name(self):
        return self.paramName
    
class Variable:
    def __init__(self, pName = "", pType=ParamType.natural, pValue = None, pRest = []):
        self.paramName = pName
        self.paramType = pType
        self.paramValue = pValue
        self.paramRestrictions = pRest
    
class QBF:
    def __init__(self):
        self.varCounter = 0
        
        self.name = ""
        self.format = ""
        self.values = {}
        self.parameters = []
        self.readVariables = []
        self.variables = {}
        
    def get_name(self):
        return self.name
    
    def set_name(self, n):
        self.name = n
        
    def get_format(self):
        return self.format
    
    def set_format(self, f):
        if f == 'CNF':
            self.format = Format.CNF
        else:
            self.format = Format.circuit
            
    def get_values(self):
        return self.values
    
    def set_values(self, newValues):
        self.values = newValues
    
    def get_value(self, name):
        return self.values[name]
    
    def set_value(self, name, expression):
        self.values[name] = eval(expression)
    
    def get_parameters(self):
        return self.parameters
    
    def get_parameter(self, pName):
        params = self.parameters
        for p in params:
            if p.get_name() == pName:
                return p
            
    def add_parameter(self, paramName, paramType, cons):
        value = self.values[paramName]
        constraints = []
        for expr in cons:
            #res = eval(expr.replace(paramName, str(value)))
            res = self.evaluate(expr) # bring variables into scope
            constraints.append(res)
        self.parameters.append(Parameter(paramName, paramType, value, constraints))
        
    def add_variable(self, varName, varIndices=[], varRanges=[]):
        print(varIndices)
        if varIndices and varRanges:
            self.recursive_nesting(varRanges, 0, 0, varName, [])
        elif varIndices:
            varName = varName + "("
            for inx in varIndices:
                varName = varName + ' ' + str(inx)
            varName = varName + ')'
            self.varCounter = self.varCounter + 1
            varId = self.varCounter
            self.variables[varName] = varId
        else:
            self.varCounter = self.varCounter + 1
            varId = self.varCounter
            self.variables[varName + "( )"] = varId
            
    def get_variables(self):
        return self.variables
        
    def recursive_nesting(self, levels, currentLevel, currentIndex, varName, valuedIndices):
        if currentLevel == len(levels):
            name = varName + "("
            for inx in valuedIndices:
                name = name + ' ' + str(inx)
            name = name + ' )'
            self.varCounter = self.varCounter + 1
            varId = self.varCounter
            self.variables[name] = varId
            return
            
        level = levels[currentLevel]
        indices = level[0]
        if currentIndex == len(indices):
            self.recursive_nesting(levels, currentLevel + 1, 0, varName, valuedIndices)
            return
        
        limits = level[1]
        lim1 = self.evaluate(limits[0])
        lim2 = self.evaluate(limits[1])
        
        for index in range(lim1, lim2 + 1):
            vals = valuedIndices.copy()
            vals.append(index)
            self.recursive_nesting(levels, currentLevel, currentIndex + 1, varName, vals)
            
    def evaluate(self, expr):
        variables = [var for var in self.values]
        assigned_values = [val for val in self.values.values()]
        pairs = zip(variables, assigned_values)
        for p in pairs:
            assignment = "{} = {}".format(p[0], p[1])
            exec(assignment)
        return eval(expr)    
        
        
    