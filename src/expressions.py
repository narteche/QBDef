

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

    start: expr

    formula_family : 
    
   
    expr : expr OP expr | PARAM_NAME | INDEX -> add_expression



    PARAM_NAME : /[a-z]([a-zA-Z0-9])*/
    INDEX : /[a-z]([a-z])*/ | NUMBER
    
    
    OP : "==" | "!=" | "<=" | "<" | ">=" | ">" | "+" | "-" | "*" | "/" | "mod"
    

    
    
    %import common.NUMBER
    %import common.WS_INLINE
    %ignore WS_INLINE
"""


@v_args(inline=True)    # Affects the signatures of the methods
class TraverseTree(Transformer):

    def __init__(self):
        self.formula = QBF()

    def set_name(self, name):
        self.formula.set_name(name)
        
    def set_format(self, f):
        self.formula.set_format(f)
        
    def add_parameter(self, p, t, c):
        self.formula.add_parameter(p, t, c)
        
    def add_variable(self, name, indices, cons): #something for ranges
        self.add_variable(self, name, indices, cons)
        
    def add_expression(self, expr, OP, ")
        
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
