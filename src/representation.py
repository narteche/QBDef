#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:54:40 2019

@author: alephnoell
"""
from itertools import product
from enum import Enum
from time import time
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
        
    def get_name(self):
        return self.paramName
class Block:
    
    def __init__(self, bName = "", bId = "", bBody = set(), bGroup = None, bAtt = []):
        self.blockName = bName
        self.blockId = bId
        self.blockBody = bBody
        self.blockGroup = bGroup
        self.blockAtt = bAtt
        
    def add_attribute(self, bAtt):
        self.blockAtt = bAtt
    
    def get_body(self):
        return self.blockBody
    
    def get_name(self):
        return self.blockName
    
    def get_attribute_str(self):
        return str(self.blockAtt)

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
        
        self.final = None
    
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
            
    def format_in_string(self):
        if self.format == Format.CNF:
            return "CNF"
        else:
            return "circuit"
            
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
        return self.block_contents[blockId]
    
    # a block definition looks like:
    # [('X', ['i', 'j']), [((sign, name), indices), ...]]
    
    def add_blocks(self, definitions, conditions, grouping=None):
       
        ids_for_grouping = []
        for left_values in self.iterate(conditions):
            for definition in definitions:
                left = definition[0]
                bricks = definition[1]
                name = left[0]
                substitutedIndices = self.substitute(left[1], left_values)
                blockName = self.normalize_name(name, substitutedIndices)
                if self.is_defined(blockName):
                    continue
                else:
                    self.save_block(blockName)
                ids_for_grouping.append(self.get_brick_id(blockName))
                contents = []
                cs = set()
                for i in range(len(bricks)):
                    if bricks[i][0] == "all blocks in":
                        contents.append([self.get_bricks_in_grouping(bricks[i][1])])
                    else:
                        contents.append([])

                for valuedIndices in self.iterate(conditions):
                    for i in range(len(bricks)):
                        brick = bricks[i]
                        if brick[0] != "all blocks in":
                            bSign = brick[0][0]
                            bName = brick[0][1]
                            indices = self.substitute(brick[1], left_values, valuedIndices)
                            brickId = self.get_brick_id(self.normalize_name(bName, indices,  brick[1]))
                            brickIdWithSign = int(bSign + str(brickId))
                            if brickIdWithSign not in cs:
                                contents[i].append(brickIdWithSign)
                                cs.add(brickIdWithSign)
                contents = [elem for b in contents for elem in b]
                self.save_block_contents(blockName, contents, grouping)
        self.save_grouping(grouping, ids_for_grouping)    

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
        if grp:
            self.groupings[grp] = ids
    
    def get_bricks_in_grouping(self, grp):
        return self.groupings[grp]
    
    def update_block_with_attribute(self, blockId, att):
        block = self.get_block(blockId)
        block.add_attribute(att)
        self.block_contents[blockId] = block
    
    # ====== Quantifiers and operators =======
    def add_attribute(self, blockName, blockIndices, att):
        #print("Receiving block {} with indices {} for attribute {}".format(blockName, blockIndices, att))
        normName = self.normalize_name(blockName, blockIndices)
        blockId = self.get_brick_id(normName)
        self.update_block_with_attribute(blockId, att)
        
    def add_attributes_grp(self, grp, att):
        if grp not in self.groupings:
            print("GROUPING ERROR: grouping name {} is not defined".format(grp))
        else:
            for block_id in self.groupings[grp]:
                self.update_block_with_attribute(block_id, att)
                
    # ====== Final block ========
    def save_final_block(self, name, indices):
        normName = self.normalize_name(name, indices)
        blockId = self.get_brick_id(normName)
        self.final = blockId
    
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
    
    # def iterate(self, conditions):
    #     yield from self.recursive_iteration(conditions, 0, {})

    def iterate(self, conditions):
        stack = [[{}, 0]]
        while stack:
            valuedIndices, currentCondition = stack.pop(0)
            if currentCondition < len(conditions):
                condition = conditions[currentCondition]
                if condition[0] == 'other':
                    booleanCondition = self.evaluate(condition[1], valuedIndices)
                    if booleanCondition:
                        currentCondition = currentCondition + 1 
                    else:
                        continue
                else:
                    index = condition[0]
                    lim1 = self.evaluate(condition[1][0], valuedIndices)
                    lim2 = self.evaluate(condition[1][1], valuedIndices)
                    for ix in range(lim1, lim2 + 1):
                        valuedIndices[index] = ix
                        stack.append([valuedIndices.copy(), currentCondition + 1])
            else:
                yield valuedIndices

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
        
    def substitute(self, indices, values, extra_values={}):
        subs = []
        for ix in indices:
            if ix in self.values:
                subs.append(self.values[ix])
            elif ix in values:
                subs.append(values[ix])
            elif ix in extra_values:
                subs.append(extra_values[ix])
            else:
                subs.append(int(ix))
        return subs
    
    def is_defined(self, name):
        return (name in self.variables) or (name in self.blocks)
    
    def print_formula(self):
        my_formula = "========== Printed QBF ==========\n"
        my_formula = my_formula + "Printing the formula of the family {}, defined in {} format, for the VALUES:\n".format(self.get_name(), self.format_in_string()) 
        my_formula = my_formula + "\n"
        for val in ["    {} = {};\n".format(param.get_name(), self.values[param.get_name()]) for param in self.get_parameters()]:
            my_formula = my_formula + val
        my_formula = my_formula + "\n"
        
        my_formula = my_formula +  "The formula has the following {} variables, with assigned corresponding numeric identifiers:\n\n".format(len(self.get_variables()))
        for var in self.get_variables():
            my_formula = my_formula + "    {} --> {}\n".format(var, self.variables[var])
        my_formula = my_formula + "\n"
        
        my_formula = my_formula +  "The formula has the following {} blocks, with assigned corresponding numeric identifiers and contents:\n\n".format(len(self.blocks))
        for b in self.blocks:
            my_formula = my_formula + "    {} --> {}, with contents {}\n".format(b, self.blocks[b], self.block_contents[self.blocks[b]].get_body())
        my_formula = my_formula + "\n"
        
        my_formula = my_formula +  "The formula has the following {} groupings, which contains the following blocks:\n\n".format(len(self.groupings))
        for g in self.groupings:
            my_formula = my_formula + "    {}, with contents {}\n".format(g, self.groupings[g])
        my_formula = my_formula + "\n"
        
        my_formula = my_formula + "The formula has the following quantifiers and operators associated to the blocks: \n"
        for block in self.block_contents:
            my_formula = my_formula + "    Block {}, with attribute {}\n".format(block, self.block_contents[block].get_attribute_str())
        my_formula = my_formula + "\n"
        my_formula = my_formula + "The output of the formula is determined by the block {}, i.e. {}\n".format(self.final, self.block_contents[self.final].get_name())
        my_formula = my_formula + "======================================================\n"
        
        print(my_formula)