#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:54:40 2019

@author: alephnoell
"""
from itertools import product
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
    
    def __init__(self, bName = "", bId = "", bBody = set(), bGroup = None, bAtt = []):
        self.blockName = bName
        self.blockId = bId
        self.blockBody = bBody
        self.blockGroup = bGroup
        self.blockAtt = bAtt
        
    def add_attribute(self, bAtt):
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

    def add_variables(self, varName, varIndices=[], varRanges=[]):        
        if varIndices and varRanges:
            for valued_indices in self.iterate(varRanges):
                self.save_variable(self.normalize_name(varName, varIndices, valued_indices)) 
        else:
            self.save_variable(self.normalize_name(varName, varIndices))
            
    def save_variable(self, normVarName):
        if normVarName in self.variables:
            print("VARIABLE ERROR: Variable {} is being declared more than once!".format(normVarName))
        else:
            self.idCounter = self.idCounter + 1
            self.variables[normVarName] = self.idCounter
            
    # ====== Blocks ======
    
    # some basic manipulation functions are needed here... 
    def get_block(self, blockId):
        return self.blockContents[blockId]
    
    # a block definition looks like:
    # [('X', ['i', 'j']), [((sign, name), indices), ...]]
    
    def add_blocks(self, definitions, conditions, grouping=None):
        
        ids_for_grouping = []
        
        for definition in definitions:
            left = definition[0]
            bricks = definition[1]
            name = left[0]
            for left_values in self.iterate(conditions):
                substitutedIndices = self.substitute(left[1], left_values)
                blockName = self.normalize_name(name, substitutedIndices)
                if self.is_defined(blockName):
                    continue
                self.save_block(blockName)
                ids_for_grouping.append(self.get_brick_id(blockName))
                contents = []
                cs = set()
                for brick in bricks:
                    if brick[0] == "all blocks in":
                        contents = contents + self.get_bricks_in_grouping(brick[1])
                    else:
                        bSign = brick[0][0]
                        bName = brick[0][1]
                        for valuedIndices in self.iterate(conditions):
                            indices = self.substitute(brick[1], left_values, valuedIndices)
                            brickId = self.get_brick_id(self.normalize_name(bName, indices,  brick[1]))
                            brickIdWithSign = int(bSign + str(brickId))
                            if brickIdWithSign not in cs:
                                contents.append(brickIdWithSign)
                                cs.add(brickIdWithSign)
                        print(contents)
                        print(cs)
                self.save_block_contents(blockName, contents, grouping)
                print("the block {} has contents {} in grp {}".format(blockName, contents, grouping))
        self.save_grouping(grouping, ids_for_grouping)
        print(self.groupings)
            
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
            return False
        else:
            self.idCounter = self.idCounter + 1
            self.blocks[normBlockName] = self.idCounter
            return True
            
    def save_block_contents(self, normName, contents, grp):
        bId = self.get_brick_id(normName)
        self.block_contents[bId] = Block(normName, bId, contents, grp)
        
    def save_grouping(self, grp, ids):
        self.groupings[grp] = ids
    
    def get_bricks_in_grouping(self, grp):
        return self.groupings[grp]
    
    def update_block_with_attribute(self, blockId, att):
        block = self.get_block(blockId)
        block.add_atribute(att)
        self.block_contents[blockId] = block
    
    # ====== Quantifiers and operators =======
    def add_attribute(self, blockName, blockIndices, att):
        print("Receiving block {} with indices {} for attribute {}".format(blockName, blockIndices, att))
        normName = self.normalize_name(blockName, blockIndices)
        blockId = self.getBrickId(normName)
        self.update_block_with_attribute(blockId, quantifier)
    
    # ====== EXTRA methods ======    
    def evaluate(self, expr, extra_values={}):
        variables = [var for var in self.values] + [var for var in extra_values]
        assigned_values = [val for val in self.values.values()] + [val for val in extra_values.values()]
        pairs = zip(variables, assigned_values)
        for p in pairs:
            assignment = "{} = {}".format(p[0], p[1])
            exec(assignment)
        return eval(expr)
    
    def normalize_name(self, varName, varIndices, valuedIndices={}):
        varName = varName + '('
        for index in varIndices:
            varName = varName + ' ' + str(valuedIndices[index]) if index in valuedIndices else varName + ' ' + str(index)
        varName = varName + ' )'
        return varName
    
    def iterate(self, conditions):
        yield from self.recursive_iteration(conditions, 0, {})
        
    def recursive_iteration(self, conditions, currentCondition, valuedIndices):
        if currentCondition == len(conditions):
            yield valuedIndices
        else:
            condition = conditions[currentCondition]
            if condition[0] == 'other':
                booleanCondition = self.evaluate(condition[1], valuedIndices)
                if booleanCondition:
                    yield from self.recursive_iteration(conditions, currentCondition + 1, valuedIndices)
            else:
                index = condition[0]
                lim1 = self.evaluate(condition[1][0], valuedIndices)
                lim2 = self.evaluate(condition[1][1], valuedIndices)
                for ix in range(lim1, lim2 + 1):
                    valuedIndices[index] = ix
                    yield from self.recursive_iteration(conditions, currentCondition + 1, valuedIndices)
    
#    def iterate_ranges(self, varRanges):
#        for i in range(len(varRanges)):
#            varRanges[i][1] = (self.evaluate(varRanges[i][1][0]), self.evaluate(varRanges[i][1][1])) 
#        keys, intervals = zip(*varRanges)
#        intervals = [range(x, y + 1) for x, y in intervals]
#        yield from (dict(zip(keys, v)) for v in product(*intervals))
#    
#    def iterate_conditions(self, conditions):
#        booleanConditions = [c[1] for c in conditions if c[0] == 'other']
#        rangeConditions   = [[c[1], c[2]] for c in conditions if c[0] != 'other']
#        
#        
#        for i in range(len(rangeConditions)):    
#            rangeConditions[i][1] = (self.evaluate(rangeConditions[i][0]), self.evaluate(rangeConditions[i][1])) 
#        keys, intervals = zip(*rangeConditions)
#        intervals = [range(x, y + 1) for x, y in intervals]
#        
#        for v in product(*intervals):
#            valuedVariables = dict(zip(keys, v))
#            if self.verifies_conditions(valuedVariables, booleanConditions):
#                yield valuedVariables 
#    
#    def verifies_conditions(self, valuedVariables, conditions):
#        for c in conditions:
#            print(c)
#        return not (False in [self.evaluate(c, valuedVariables) for c in conditions])
        
    def substitute(self, indices, values, extra_values={}):
        subs = []
        for ix in indices:
            if ix in values:
                subs.append(values[ix])
            elif ix in extra_values:
                subs.append(extra_values[ix])
            else:
                subs.append(int(ix))
        return subs
    
    def is_defined(self, name):
        return (name in self.variables) or (name in self.blocks)
    
    