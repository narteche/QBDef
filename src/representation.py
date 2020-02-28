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
    
  
class Parameter:
    
    def __init__(self, pName = "", pType="", pValue = None, pCons = [], pEval = []):
        self.paramName = pName
        self.paramType = pType
        self.paramValue = pValue
        self.paramConstraints = pCons
        self.paramEvaluatedConstraints = pEval
        

class Block:
    
    def __init__(self, bName = "", bId = "", bBody = [], bGroup = None, bAtt = []):
        self.blockName = bName
        self.blockId = bId
        self.blockBody = bBody
        self.blockGroup = bGroup
        self.blockAtt = bAtt

class QBF:
    def __init__(self):

        self.values = {}
        
        self.name = ""
        self.format = None
        

        self.parameters = []
        
        self.idCounter = 0
        self.variables = {}
        self.blocks = {}
        self.block_contents = {}
        self.groupings = {}
    
    # ====== Name ======
    def get_name(self):
        return self.name
    
    def set_name(self, n):
        self.name = n
        
    # ===== Format ======
    def get_format(self):
        return self.format
    
    def set_format(self, f):
        if f == 'CNF':
            self.format = Format.CNF
        else:
            self.format = Format.circuit
            
    # ====== Values ======
    def get_values(self):
        return self.values
    
    def set_values(self, newValues):
        self.values = newValues
    
    def get_value(self, name):
        return self.values[name]
    
    def add_value(self, name, expression):
        self.values[name] = self.evaluate(expression)
    
    # ====== Parameters ======
    def get_parameters(self):
        return self.parameters
    
    def set_parameters(self, params):
        self.parameters = params
    
    def add_parameter(self, paramName, paramType, cons):
        try:
            value = self.values[paramName]
        except:
            print("PARAMETER ERROR: Cannot find appropriate value for parameter {}".format(paramName))
            exit()
        
        constraints = []
        for expr in cons:
            res = self.evaluate(expr) # bring variables into scope
            constraints.append(res)
        for i in range(len(constraints)):
            if not constraints[i]:
                print("PARAMETER ERROR: Constraint \'{}\' for parameter {} was violated.".format(cons[i], paramName))
        self.parameters.append(Parameter(paramName, paramType, value, cons, constraints))
        
        
    # ====== Variables ======
    def get_variables(self):
        return self.variables
    
    def set_variables(self, newVars):
        self.variables = newVars
        
    def get_variable_id(self, normVarName):
        try:
            return self.variables[normVarName]
        except:
            print("VARIABLE ERROR: Variable {} has not been declared.".format(normVarName))

    def add_variable(self, varName, varIndices=[], varRanges=[]):
        if varIndices and varRanges:
            self.recursive_nesting(varRanges, 0, 0, varName, [])
        else:
            self.save_variable(self.normalize_name(varName, varIndices))

    def save_variable(self, normVarName):
        if normVarName in self.variables:
            print("VARIABLE ERROR: Variable {} is being declared more than once!".format(normVarName))
        else:
            self.idCounter = self.idCounter + 1
            self.variables[normVarName] = self.idCounter

            
    def normalize_name(self, varName, varIndices):
        varName = varName + '('
        for inx in varIndices:
            varName = varName + ' ' + str(inx)
        varName = varName + ' )'
        return varName
        
    def recursive_nesting(self, levels, currentLevel, currentIndex, varName, valuedIndices):
        if currentLevel == len(levels):
            self.save_variable(self.normalize_name(varName, valuedIndices))
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
            
    # ====== Blocks ======
    def add_blocks(self, grouping, defs, conditions):
        self.process_conditions(conditions, 0, {}, defs, 0, grouping)        
        
    def process_conditions(self, conditions, currentCondition, valuedIndices, block_defs, currentIndex, grouping):
        if currentCondition == len(conditions):
            for definition in block_defs:
                self.add_block(definition[0], definition[1], grouping, valuedIndices)
            return
            
        cond = conditions[currentCondition]
        if cond[0] == 'range':
            indices = cond[1]
            if currentIndex == len(indices):
                self.process_conditions(conditions, currentCondition + 1, valuedIndices, block_defs, 0, grouping)
            else:
                lim1 = self.evaluate(cond[2])
                lim2 = self.evaluate(cond[3])
                for indexVal in range(lim1, lim2 + 1):
                    valuedIndices[indices[currentIndex]] = indexVal
                    self.process_conditions(conditions, currentCondition, valuedIndices, block_defs, currentIndex + 1, grouping)
        elif cond[0] == 'assignment':
            valuedIndices[cond[1]] = self.evaluate(cond[2])
            self.process_conditions(conditions, currentCondition + 1, valuedIndices, block_defs, currentIndex, grouping)
        else:
            if not self.evaluate(cond[1]):
                return
            else:
                self.process_conditions(conditions, currentCondition + 1, valuedIndices, block_defs, currentIndex, grouping)
       
    def substitute(self, indices, values):
        subs = []
        for ix in indices:
            if ix in values:
                subs.append(values[ix])
            else:
                subs.append(ix)
        return subs
    
    def add_block(self, name, bricks, grp = None, valuedIndices = {}):
        indices = self.substitute(name[1], valuedIndices)
        name = self.normalize_name(name[0], indices)
        self.save_block(name)

        contents = []
        for brick in bricks:
            if brick[0] == "all blocks in":
                print("Not ready")
                #contents = contents + self.groupings[brick[1]]
            else:
                bSign = brick[0][0]
                bName = brick[0][1]
                indices = self.substitute(brick[1], valuedIndices)
                brickId = self.get_brick_id(self.normalize_name(bName, indices))
                contents.append(int(bSign + str(brickId)))
        
        self.save_block_contents(name, contents, grp)
                
    def get_brick_id(self, normName):
        if normName in self.variables:
            return self.variables[normName]
        elif normName in self.blocks:
            return self.blocks[normName]
        else:
            print("BRICK ERROR: Block or variable {} has not been declared.".format(normName))

    def save_block(self, normBlockName):
        if normBlockName in self.blocks:
            print("BLOCK ERROR: Block {} is being declared more than once!".format(normBlockName))
        else:
            self.idCounter = self.idCounter + 1
            self.blocks[normBlockName] = self.idCounter
            
    def save_block_contents(self, normName, contents, grp):
        bId = self.get_brick_id(normName)
        self.block_contents[bId] = Block(normName, contents, grp)
            
    # ====== EXTRA: expression evaluation ======
    def evaluate(self, expr):
        variables = [var for var in self.values]
        assigned_values = [val for val in self.values.values()]
        pairs = zip(variables, assigned_values)
        for p in pairs:
            assignment = "{} = {}".format(p[0], p[1])
            exec(assignment)
        return eval(expr)
        