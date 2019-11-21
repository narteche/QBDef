#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:38:01 2019

@author: alephnoell
"""


from lark import Lark, Transformer, v_args
from representation import QBF

try:
    input = raw_input   # For Python2 compatibility
except NameError:
    pass


formula_family_grammar = """

    start: formula_family

    formula_family : value* name format parameters? finish
    
    value : "value:" NAME "=" NUMBER ";" -> assign_var
    
    name: "name:" FAMILY_NAME -> set_name
    
    format: "format:" FORMAT -> set_format
    
    parameters: "parameters:" parameter_declaration+
    
    parameter_declaration: NAME ":" PARAM_TYPE param_constraints* -> add_parameter
    
    param_constraints: "," bool_expr

    bool_expr :   arith_expr "==" arith_expr -> eq
                | arith_expr "!=" arith_expr -> neq
                | arith_expr "<=" arith_expr -> le
                | arith_expr ">=" arith_expr -> ge
                | arith_expr "<" arith_expr  -> lt
                | arith_expr ">" arith_expr  -> gt
    
    arith_expr :   sum
                 | NAME "=" sum -> assign_var  
                 
    sum :  product
         | sum "+" product -> add
         | sum "-" product -> sub
         
    product :   atom
              | product "*" atom -> mul
              | product "/" atom -> div
              | product "mod" atom -> mod
              
    atom :     NUMBER           -> number
             | "-" atom         -> neg
             | NAME             -> var
             | "(" sum ")"

    finish : -> return_formula
    
    FAMILY_NAME : /[a-zA-Z]([a-zA-Z0-9])*/
    NAME : /[a-z]([a-zA-Z0-9])*/
    FORMAT : "CNF" | "circuit"
    INDEX : NAME | NUMBER
    PARAM_TYPE : "natural"
    
    
    
    %import common.NUMBER
    %import common.WS_INLINE
    %import common.NEWLINE
    %ignore WS_INLINE
    %ignore NEWLINE
"""


@v_args(inline=True)    # Affects the signatures of the methods
class TraverseTree(Transformer):
    from operator import lt, le, eq, ne, ge, gt, mod, add, sub, mul, truediv as div, neg
    number = int

    def __init__(self):
        self.vars = {}
        self.formula = QBF()
        
    def assign_var(self, name, value):
    
        self.vars[name] = value
        return value

    def var(self, name):
        return self.vars[name]

    def set_name(self, name):
        self.formula.set_name(name)
        
    def set_format(self, f):
        self.formula.set_format(f)
        
    def add_parameter(self, p, t, c):
        self.formula.add_parameter(p, t, c)
        
    def return_formula(self):
        return self.formula
        
parser = Lark(formula_family_grammar, parser='lalr', transformer=TraverseTree())
parse = parser.parse

#def main():
#    while True:
#        try:
#            s = input('> ')
#        except EOFError:
#            break
#        c = parse(s)
#        
#        for sub in c.iter_subtrees():
#            if sub.data == "formula_family":
#                chil = sub.children
#                o = chil[len(chil) - 1]
#                print(o)
#                name = o.get_name()
#                print(name)
#                f = o.get_format()
#                print(str(f))
#     

def main():
    f = open("test_def.txt", "r")
    s = f.read()
    parsed_formula = parse(s)
    formula = None
    for sub in parsed_formula.iter_subtrees():
        if sub.data == "formula_family":
            chil = sub.children
            formula = chil[len(chil) - 1]
    print(formula)

#def test():
#    print(calc("a = 1+2"))
#    print(calc("1+a*-3"))


if __name__ == '__main__':
    # test()
    main()
