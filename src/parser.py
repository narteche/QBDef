#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:38:01 2019

@author: alephnoell
"""

#
# This example shows how to write a basic calculator with variables.
#

from lark import Lark, Transformer, v_args


try:
    input = raw_input   # For Python2 compatibility
except NameError:
    pass


formula_family_grammar = """

    start: formula_family

    formula_family :   name type parameters
                      


    name: "name:" NAME  -> set_name
    
    type: "type:" TYPE  -> set_type
    
    parameters : "parameters:" parameter_declaration*
    
    parameter_declaration : PARAM_NAME ":" param_type param_constraints*  -> add_param
                            
    param_type : /natural/
    
    param_constraints : "," PARAM_NAME OP NUMBER
    
    NAME : /[a-zA-Z](_?[a-zA-Z0-9])*/
    PARAM_NAME : /[a-z](_?[a-zA-Z0-9])*/
    TYPE: "natural"
    OP: "<="
    
    
    %import common.NUMBER
    %import common.WS_INLINE
    %ignore WS_INLINE
"""


@v_args(inline=True)    # Affects the signatures of the methods
class TraverseTree(Transformer):


    def __init__(self):
        self.name = ""
        self.type = ""
        self.params = []

    def set_name(self, name):
        self.name = name
        print("Current value of name: {}".format(self.name))
        
    def set_type(self, ptype):
        self.type = ptype
        print("Current value of type: {}".format(self.type))
        
    def add_param(self, name, ptype, *constraints):
        self.params.append([name, ptype, constraints])
        print("Current value of params: {}".format(self.params))
        
        
calc_parser = Lark(formula_family_grammar, parser='lalr', transformer=TraverseTree())
calc = calc_parser.parse


def main():
    while True:
        try:
            s = input('> ')
        except EOFError:
            break
        print(calc(s))


def test():
    print(calc("a = 1+2"))
    print(calc("1+a*-3"))


if __name__ == '__main__':
    # test()
    main()
