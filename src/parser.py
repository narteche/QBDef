#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:38:01 2019

@author: alephnoell
"""

from lark import Lark, Transformer, v_args
from representation import QBF
from itertools import chain

try:
    input = raw_input   # For Python2 compatibility
except NameError:
    pass


@v_args(inline=True)    # Affects the signatures of the methods
class TraverseTree(Transformer):
    def __init__(self):
        self.formula = QBF()
    
    def handle_value(self, name, expr):
        print("VALUE: Handling parameter {} with value {}.".format(name, expr))
        self.formula.add_value(str(name), str(expr))

    def set_name(self, name):
        print("NAME: setting name \"{}\".".format(name))
        self.formula.set_name(str(name))
        
    def set_format(self, f):
        print("FORMAT: setting format \'{}\'.".format(f))
        self.formula.set_format(str(f))
        
    def add_parameter(self, p, t, *c):
        constr = []
        for elem in c:
            constr.append(str(elem))
        print("PARAMETER: adding parameter {} of type {} with constraints {}".format(p, t, constr))
        self.formula.add_parameter(str(p), str(t), constr)
        
    def add_variable(self, varName, indices=[], *indexRanges):
        varName = str(varName)
        varIndices = []
        if indices:
            for c in indices.children:
                varIndices.append(str(c))
                
        completeRanges = []
        if indexRanges:
            for indRange in indexRanges:
                ran = indRange.children
                theIndices = []
                inds = ran[0]
                try:
                    chil = inds.children
                    for ix in chil:
                        theIndices.append(str(ix))
                except:    
                    theIndices = str(inds)
                    
                lim1 = str(ran[1])
                lim2 = str(ran[2])
               
                for ix in theIndices:
                    completeRanges.append([ix, (lim1, lim2)])
                #completeRange = [theIndices, [lim1, lim2]]
                #completeRanges.append(completeRange)

        self.formula.add_variables(varName, varIndices, completeRanges)
        print("VARIABLE: adding variable {} with indices {} and ranges {}".format(varName, varIndices, completeRanges))
        
    def add_blocks(self, *everything):
        grouping = None
        definitions = []
        conditions = []
        
        for elem in everything:
            defs = elem.find_data("single_block_def")
            for d in defs:
                definitions.append(d)
                     
            conds = elem.find_data("conditions")
            for c in conds:
                for cprime in c.children:
                    conditions.append(cprime)
            
            grps = elem.find_data("grouping")
            for g in grps:
                grouping = g
        
        defs_to_send = [self.handle_block_def(d) for d in definitions]
        conds_to_send = []
        for c in conditions:
            conds_to_send = conds_to_send + list(chain(self.handle_condition(c)))
        grouping_to_send = self.handle_grouping(grouping)
        
        self.formula.add_blocks(defs_to_send, conds_to_send, grouping_to_send)
    
    def add_attributes(self, *contents):
        att = str(contents[len(contents)-1])
        contents = contents[:len(contents)-1]
        name_indices_pairs = []
        current_block = [[], []]
        for elem in contents:
            try:
                if elem.data == "indices":
                    current_block[1] = [str(i) for i in elem.children]
                    name_indices_pairs.append(current_block)
                    current_block = [[], []]
            except:
                if current_block[0]:
                    name_indices_pairs.append(current_block)
                current_block = [str(elem), []]
        if current_block[0]:
            name_indices_pairs.append(current_block)
        
        print(name_indices_pairs)
        for block in name_indices_pairs:
            print("ATTRIBUTE: adding attribute {} to block {} with indices {}".format(att, block[0], block[1]))
         #   self.formula.add_attribute(block[0], block[1], att)
        
    def handle_condition(self, condition):
        condition = condition.children[0]
        conditions_to_send = []
        if condition.data == 'index_range':
            for ix in condition.children[0].children:
                conditions_to_send = [[str(ix), (str(condition.children[1]), str(condition.children[2]))] for ix in condition.children[0].children]
        elif condition.data == 'assignment':
            conditions_to_send = [[str(condition.children[0]), (str(condition.children[1]), str(condition.children[1]))]]
        else:
            conditions_to_send = [['other', str(condition.children[0])]]
            
        return conditions_to_send
        
        
    def handle_block_def(self, block_def):
        block_name = str(block_def.children[0])
        indices = []
        if block_def.children[1].data == "indices":
            for ix in block_def.children[1].children:
                indices.append(str(ix))
        
        block_name = (block_name, indices)

        bricks = block_def.find_data("brick")
        bricks_to_send = []
        for b in bricks:
            components = b.children
            brick_to_send = []
            if components[0] == "all blocks in":
                brick_to_send = ["all blocks in", str(components[1])]                
            else:    
                sign = ''
                if components[0] == '-':
                    sign = '-'
                    components = components[1:]
                
                name = str(components[0])
                indices = []
                if len(components) == 2:
                    for ix in components[1].children:
                        indices.append(str(ix))
                    
                brick_to_send = ((sign, name), indices)
            bricks_to_send.append(brick_to_send)
        
        print("BLOCK: adding block {} with body {}.".format(block_name, bricks_to_send))
        return [block_name, bricks_to_send]
    
    def handle_grouping(self, grp):
        return str(grp.children[0])
            
    def return_formula(self, *r):
        return self.formula
        
grammar_file = open("grammar.lark", "r")
grammar = grammar_file.read()
parser = Lark(grammar, parser='lalr', transformer=TraverseTree())
parse = parser.parse
   

def main():
    f = open("ch_test.txt", "r")
    s = f.read()
    parsed_formula = parse(s)
    #print(parsed_formula.pretty())
    formula = None
    for sub in parsed_formula.iter_subtrees():
        if sub.data == "formula_family":
            chil = sub.children
            formula = chil[len(chil) - 1]

if __name__ == '__main__':
    # test()
    main()
