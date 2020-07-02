#==============================================================================
#==================================== QBDeF ===================================
#==================== Noel Arteche (noel.arteche@gmail.com) ===================
#=============================== __ May 2020 __ ===============================
#==============================================================================

from sys import argv
from lark import Lark, Transformer, v_args
#from representation import QBF
from itertools import chain
from time import time

## Representation imports:
from enum import Enum
from time import time
from sys import exit 
from os import system, remove
from os.path import exists

try:
    input = raw_input   # for Python2 compatibility
except NameError:
    pass


grammar = '''
                start: value* formula_family? -> return_formula

                value : "value:" NAME "=" expression ";" -> handle_value

                formula_family : name format parameters? variables blocks output_block

                name: "name:" FAMILY_NAME ";" -> set_name

                format: "format:" FORMAT ";" -> set_format

                parameters: "parameters:" "{" parameter_declaration+ "}"

                parameter_declaration: NAME ":" PARAM_TYPE ("," expression)* ";" -> add_parameter 

                variables : "variables:" "{" variable_declaration+ "}"

                variable_declaration: NAME ("(" indices ")" ("where" index_range ("," index_range)*)?)? ";" -> add_variable

                indices : INDEX ("," INDEX)*

                index_range : indices "in" (expression | INDEX | NAME) ".." (expression | INDEX | NAME)

                blocks: "blocks:" "{" block_definition (block_definition | operator_declaration | quantifier_declaration)+ "}"

                block_definition:   "define block" single_block_def -> add_blocks
                                  | "define blocks" grouping? "{" single_block_def+ "}" conditions? ";" -> add_blocks

                single_block_def: BLOCK_NAME ("(" indices ")")? ":=" block_body ";"

                block_body: brick ("," brick)*

                brick:  /all blocks in/ BLOCK_NAME
                       | NEGATION? BLOCK_NAME ("(" indices ")")?
                       | NEGATION? NAME ("(" indices ")")?

                grouping: "grouped in" BLOCK_NAME

                conditions: "where" condition ("," condition)*

                condition: index_range | assignment | other_condition

                assignment: INDEX "=" expression

                other_condition: expression
                             
                quantifier_declaration:   "block" BLOCK_NAME ("(" indices ")")? "quantified with" QUANTIFIER ";" -> add_attributes
                                        | "blocks" BLOCK_NAME ("(" indices ")")? ("," BLOCK_NAME ("(" indices ")")?)+ "quantified with" QUANTIFIER ";" -> add_attributes
                                        | "all blocks in" BLOCK_NAME "quantified with" QUANTIFIER ";" -> add_attribute_to_grouping


                operator_declaration:   "block" BLOCK_NAME ("(" indices ")")? "operated with" OPERATOR ";" -> add_attributes
                                      | "blocks" BLOCK_NAME ("(" indices ")")? ("," BLOCK_NAME ("(" indices ")")?)+ "operated with" OPERATOR ";" -> add_attributes
                                      | "all blocks in" BLOCK_NAME "operated with" OPERATOR ";" -> add_attribute_to_grouping

                output_block: "output block:" BLOCK_NAME ("(" indices ")")? ";" -> add_final_block

                NAME : /(?!all blocks in)[a-z]([_?a-zA-Z0-9])*/
                FAMILY_NAME : /[^;]+/ // old version: /[a-zA-Z]([ ?_?a-zA-Z0-9])*(?=;)/
                FORMAT : "CNF" | "circuit-prenex" | "circuit-nonprenex"
                PARAM_TYPE : "int" | "str" | "float" | "list" | "bool" | "other" // the names used by Python
                ?expression : /[0-9]+/ | "`" /[^`]+/ "`" //| /[^`,;\]]+/
                INDEX : /[a-z][_?a-zA-Z0-9]*/ | /[0-9]+/
                BLOCK_NAME : /[A-Z]([_?a-zA-Z0-9])*/
                NEGATION : "-"
                QUANTIFIER : "E" | "A"
                OPERATOR: "AND" | "OR" | "XOR" | "=>" | "<=>"
                COMMENT: /\/\*((\*[^\/])|[^*])*\*\//



                %import common.NUMBER
                %import common.WS_INLINE
                %import common.NEWLINE
                %ignore WS_INLINE
                %ignore NEWLINE
                %ignore COMMENT
'''

#==============================================================================
#=============================== Representation ===============================
#==============================================================================


#==============================================================================
#============ Operator, quantifier and format representations =================
#==============================================================================

class Quantifier(Enum):
    EXISTS = 'exists'
    FORALL = 'forall'

class Operator(Enum):
    OR = 'or'
    AND = 'and'
    XOR = 'xor'
    IMP = 'imp'
    DIMP = 'dimp'
    
class Format(Enum):
    circuit_PRENEX = 'circuit-prenex'
    circuit_NON_PRENEX = 'circuit-nonprenex'
    CNF = 'CNF'
  
#==============================================================================
#=========================== Parameter representation =========================
#==============================================================================

class Parameter:
    
    def __init__(self, pName = "", pType="", pValue = None, pCons = [], pEval = []):
        self.paramName = pName
        self.paramType = pType
        self.paramValue = pValue
        self.paramConstraints = pCons
        self.paramEvaluatedConstraints = pEval
        
    def get_name(self):
        return self.paramName
    
#==============================================================================
#============================= Block representation ===========================
#==============================================================================

class Block:
    
    def __init__(self, bName = "", bId = "", bBody = [], bGroup = None, bAtt = None):
        self.blockName = bName
        self.blockId = bId
        self.blockBody = bBody
        self.blockGroup = bGroup
        self.blockAtt = bAtt
        
    def add_attribute(self, bAtt):
        if self.blockAtt:
            print("ATTRIBUTE ERROR: block {} already has an attribute ({}) and thus it cannot be assigned another one ({}).".format(self.blockName, self.blockAtt.value, bAtt))
            exit()

        if bAtt == "E":
            self.blockAtt = Quantifier.EXISTS
        elif bAtt == "A":
            self.blockAtt = Quantifier.FORALL
        elif bAtt == "XOR":
            self.blockAtt = Operator.XOR
        elif bAtt == "OR":
            self.blockAtt = Operator.OR
        elif bAtt == "AND":
            self.blockAtt = Operator.AND
        elif bAtt == "=>":
            self.blockAtt = Operator.IMP
        elif bAtt == "<=>":
            self.blockAtt = Operator.DIMP
        else:
            print("ATTRIBUTE ERROR: attribute {} is not a valid input.".format(bAtt))
            exit()

    def get_body(self):
        return self.blockBody
    
    def get_name(self):
        return self.blockName

    def get_id(self):
        return self.blockId
    
    def get_attribute_str(self):
        if not self.blockAtt:
            return("None")
        return str(self.blockAtt.value)

    def get_attribute(self):
        return self.blockAtt

    def has_attribute(self):
        if self.blockAtt:
            return True
        else:
            return False

#==============================================================================
#============================= QBF representation =============================
#==============================================================================

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

        self.QCIR_str = None
        self.QDIMACS_str = None
        self.non_prenex_QCIR_str = None
    
    # ======================== Name ========================
    def get_name(self):
        return self.name
    
    def set_name(self, name):
        self.name = name
        
    # ======================= Format =======================
    def get_format(self):
        return self.format

    def get_format_str(self):
        if not self.format:
            return "None"
        else:
            return str(self.format.value)
    
    def set_format(self, f):
        if f == 'CNF':
            self.format = Format.CNF
        elif f == 'circuit-prenex':
            self.format = Format.circuit_PRENEX
        elif f == 'circuit-nonprenex':
            self.format = Format.circuit_NON_PRENEX
        else:
            print("FORMAT ERROR: {} is not one of the valid formats! It should be: CNF, circuit-prenex or circuit-nonprenex.".format(f))
            exit()

            
    # ======================= Values =======================
    def get_values(self):
        return self.values
    
    def set_values(self, newValues):
        self.values = newValues
    
    def get_value(self, name):
        try: 
            return self.values[name]
        except:
            print("VALUE ERROR: Value for {} does not exist.".format(paramName))
            exit()
    
    def add_value(self, name, expression):
        self.values[name] = self.evaluate(expression)
    
    # ===================== Parameters =====================
    def get_parameters(self):
        return self.parameters
    
    def set_parameters(self, params):
        self.parameters = params
    
    def add_parameter(self, paramName, paramType, cons):
        value = self.get_value(paramName)
        constraints = []
        for expr in cons:
            res = self.evaluate(expr)
            constraints.append(res)
        for i in range(len(constraints)):
            if not constraints[i]:
                print("PARAMETER ERROR: Constraint \'{}\' for parameter {} was violated.".format(cons[i], paramName))
                exit()
        self.parameters.append(Parameter(paramName, paramType, value, cons, constraints))
        
    # ===================== Variables =====================
    def get_variables(self):
        return self.variables
    
    def set_variables(self, newVars):
        self.variables = newVars
        
    def get_variable_id(self, normVarName):
        try:
            return self.variables[normVarName]
        except:
            print("VARIABLE ERROR: Variable {} has not been declared.".format(normVarName))
            exit()

    def add_variables(self, varName, varIndices=[], varRanges=[]):        
        if varIndices and varRanges:
            for valued_indices in self.iterate(varRanges):
                self.save_variable(self.normalize_name(varName, varIndices, valued_indices)) 
        else:
            self.save_variable(self.normalize_name(varName, varIndices))
            
    def save_variable(self, normVarName):
        if normVarName in self.variables:
            print("VARIABLE ERROR: Variable {} is being declared more than once!".format(normVarName))
            exit()
        else:
            self.idCounter = self.idCounter + 1
            self.variables[normVarName] = self.idCounter
            
    # ===================== Blocks =======================
    def get_block(self, blockId):
        try:
            return self.block_contents[blockId]
        except:
            print("BLOCK ERROR: block {} is not defined.".format(blockId))
            exit()
    
    def add_blocks(self, definitions, conditions, grouping=None):
        # a block definition looks like:
        # [('X', ['i', 'j']), [((sign, name), indices), ...]]
        ids_for_grouping = []
        for definition in definitions:
            left = definition[0]
            bricks = definition[1]
            name = left[0]
            for values in self.iterate(conditions):
                left_values = values.copy()
                substitutedIndices = self.substitute(left[1], left_values)
                new_left = dict()
                for ix in left_values:
                    if ix in left[1]:
                        new_left[ix] = left_values[ix]
                left_values = new_left
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
                        contents.append(self.get_bricks_in_grouping(bricks[i][1]))
                    else:
                        contents.append([])

                for i in range(len(bricks)):     
                    for valuedIndices in self.iterate(conditions, left_values):
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
            exit()

    def save_block(self, normBlockName):
        if normBlockName in self.blocks:
            print("BLOCK ERROR: Block {} is being declared more than once!".format(normBlockName))
            exit()
        else:
            self.idCounter = self.idCounter + 1
            self.blocks[normBlockName] = self.idCounter
            
    def save_block_contents(self, normName, contents, grp):
        bId = self.get_brick_id(normName)
        self.block_contents[bId] = Block(normName, bId, contents, grp)
        
    def save_grouping(self, grp, ids):
        if grp:
            self.groupings[grp] = ids
    
    def get_bricks_in_grouping(self, grp):
        try:
            return self.groupings[grp]
        except:
            print("GROUPING ERROR: grouping {} does not exist.".format(grp))
    
    def update_block_with_attribute(self, blockId, att):
        block = self.get_block(blockId)
        block.add_attribute(att)
        self.block_contents[blockId] = block
    
    # ===================== Attributes =====================
    def add_attribute(self, blockName, blockIndices, att):
        normName = self.normalize_name(blockName, blockIndices)
        blockId = self.get_brick_id(normName)
        self.update_block_with_attribute(blockId, att)
        
    def add_attributes_grp(self, grp, att):
        if grp not in self.groupings:
            print("GROUPING ERROR: grouping name {} is not defined".format(grp))
            exit()
        else:
            for block_id in self.groupings[grp]:
                self.update_block_with_attribute(block_id, att)
                
    # =================== Final block ======================
    def save_final_block(self, name, indices):
        normName = self.normalize_name(name, indices)
        blockId = self.get_brick_id(normName)
        self.final = blockId
    
    # ===================== Outputs ========================

    # _______________________ QCIR _________________________

    """
        Generates a string with the formula written in QCIR.
    """
    def get_QCIR_string(self):
        if self.format == Format.circuit_NON_PRENEX:
            print("FORMAT ERROR: the given formula is in non-prenex format; the only possible output is non-prenex QCIR.")
            exit()
        if self.format == Format.CNF or self.format == Format.circuit_PRENEX:
            if not self.QCIR_str:
                self.generate_QCIR()
            return self.QCIR_str

    def generate_QCIR(self):

        # opening line
        in_qcir_str = "#QCIR-G14\n"

        final = self.final
        final_contents = self.block_contents[final].get_body()
        
        # add quantifiers:
        prefix = [self.block_contents[final_contents[0]]]
        for brick in prefix:
            in_qcir_str += self.process_quant_block(brick)

        # add output gate
        in_qcir_str += "output({})\n".format(final_contents[1])

        # add gates
        gates = [self.block_contents[final_contents[1]]]
        in_qcir_str += self.get_gates_str_list(gates)

        self.QCIR_str = in_qcir_str
        return in_qcir_str

    def process_quant_block(self, block):
        if block.has_attribute():
            q_block_str = "{}(".format(block.get_attribute_str())
            q_block_str += self.to_str_list(block.get_body())
            q_block_str = q_block_str[:-2] + ")\n"
            return q_block_str
        else:
            body = block.get_body()
            several_str = ""
            for brick in body:
                several_str += self.process_quant_block(self.block_contents[brick])
            return several_str

    def to_str_list(self, bricks):
        str_list = ""
        for brick in bricks:
            ref = abs(brick)
            sign = -1 if brick < 0 else 1
            if ref in self.variables.values():
                str_list += str(brick) + ", "
            else:
                block = self.block_contents[ref]
                body = block.get_body()
                sub_list = self.to_str_list(body)
                sub_list = sub_list.split(",")
                sub_list = sub_list[:-1]
                for lit in sub_list:
                    lit_int = int(lit)
                    str_list += str(sign*lit_int) + ", "
        return str_list

    def get_gates_str_list(self, gates):
        gates_str_list = []
        gate_str = ""
        processed = set()
        while gates:
            g = gates.pop(0)
            if g.get_name() in processed:
                continue
            else:
                processed.add(g.get_name())
            if g.get_attribute_str() == "None":
                gate_str = str(g.get_id()) + " = " + "or" + "("

            elif g.get_attribute_str() == "imp":
                gate_str = str(g.get_id()) + " = " + "or" + "("
                imp1 = ""
                imp2 = ""
                i = 0
                for sub_gate in g.get_body():
                    if i == 0:
                        imp1 = sub_gate
                        i = 1
                    else:
                        imp2 = sub_gate
                    #gate_str += str(sub_gate) + ", "
                    if abs(sub_gate) in self.block_contents:
                        gates.append(self.block_contents[abs(sub_gate)])
                gate_str += str(-1 * int(imp1)) + ", " + str(imp2) + ", "

            elif g.get_attribute_str() == "dimp":
                aux2 = self.idCounter + 1
                self.idCounter += 1
                aux1 = self.idCounter + 1
                self.idCounter += 1
                imp1 = ""
                imp2 = ""
                i = 0
                for sub_gate in g.get_body():
                    if i == 0:
                        imp1 = sub_gate
                        i = 1
                    else:
                        imp2 = sub_gate
                    #gate_str += str(sub_gate) + ", "
                    if abs(sub_gate) in self.block_contents:
                        gates.append(self.block_contents[abs(sub_gate)])

                gate_str = str(g.get_id()) + " = " + "and" + "(" + str(aux1) + ", " + str(aux2) + ")\n" 
                gates_str_list.append(gate_str)
                left =  str(aux1) + " = or(" + str(-1 * int(imp1)) + ", " + str(imp2) + ")\n"
                gates_str_list.append(left)
                gate_str = str(aux2) + " = or(" + str(-1 * int(imp2)) + ", " + str(imp1) + ")\n"


            else:
                gate_str = str(g.get_id()) + " = " + g.get_attribute_str() + "("
                for sub_gate in g.get_body():
                    gate_str += str(sub_gate) + ", "
                    if abs(sub_gate) in self.block_contents:
                        gates.append(self.block_contents[abs(sub_gate)])

            if g.get_body():
                gate_str = gate_str[:-2] + ")\n"
            else:
                gate_str += ")\n"
            gates_str_list.append(gate_str)
        gates_str_list.reverse()
        return_str = ""
        for gate_str in gates_str_list:
            return_str += gate_str
        return return_str

    # __________________ Non-prenex QCIR ____________________
    """
        Generates a string with the formula written in non-prenex QCIR.
    """
    def get_non_prenex_QCIR_string(self):
        if self.format == Format.CNF or self.format == Format.circuit_PRENEX:
            print("OUTPUT ERROR: Non-prenex QCIR output format unavailable for prenex formulae.")
            exit()

        if not self.non_prenex_QCIR_str:
            self.non_prenex_QCIR_str = self.generate_non_prenex_QCIR()
        return self.non_prenex_QCIR_str

    def generate_non_prenex_QCIR(self):
        preamble = "#QCIR-G14\n" + "output({})\n".format(self.final)

        gates = [self.block_contents[self.final]]
        gates_str_list = []
        gate_str = ""
        processed = set()
        while gates:
            g = gates.pop(0)
            
            if g.get_name() in processed:
                continue
            else:
                processed.add(g.get_name())

            gate_contents = g.get_body()

            if len(gate_contents) == 2 and (gate_contents[0] in self.block_contents):
                att = self.block_contents[gate_contents[0]].get_attribute()
                if att == Quantifier.FORALL or att == Quantifier.EXISTS:
                    q_vars = self.to_str_list([gate_contents[0]])
                    processed.add(gate_contents[0])
                    gate_str = "{} = {}({}; {})\n".format(self.blocks[g.get_name()], att.value, q_vars[:-2], gate_contents[1])
                    gates_str_list.append(gate_str)
                    gates.append(self.block_contents[gate_contents[1]])
                    continue

            if g.get_attribute_str() == "None":
                gate_str = str(g.get_id()) + " = " + "or" + "("
            else:
                gate_str = str(g.get_id()) + " = " + g.get_attribute_str() + "("
            for sub_gate in g.get_body():
                gate_str += str(sub_gate) + ", "
                if abs(sub_gate) in self.block_contents:
                    gates.append(self.block_contents[abs(sub_gate)])
            if g.get_body():
                gate_str = gate_str[:-2] + ")\n"
            else:
                gate_str += ")\n"

            gates_str_list.append(gate_str)

        gates_str_list.reverse()
        return_str = ""
        for gate_str in gates_str_list:
            return_str += gate_str
        
        return preamble + return_str






    # _______________________ QDIMACS _______________________
    def get_QDIMACS_string(self):
        if self.format == Format.circuit_NON_PRENEX:
            print("FORMAT ERROR: the given formula is in non-prenex format; the only possible output is non-prenex QCIR.")
            exit()
        if self.format == Format.CNF:
            if not self.QDIMACS_str:
                self.generate_QDIMACS_from_prenex_QCIR()
            return self.QDIMACS_str

        elif self.format == Format.circuit_PRENEX:
            f1 = open("input.qcir", "w")
            f2 = open("output.qdimacs", "w")
            f2.close()
            f1.write(self.get_QCIR_string())
            f1.close()
            if not exists("qcir-to-qdimacs.py"):
                print("CONVERSION ERROR: to convert to QDIMACS William Klieber's qcir-to-qdimacs.py script is needed in this directory. Download it from https://www.wklieber.com/ghostq/qcir-to-qdimacs.py")
                exit()

            system("python2 qcir-to-qdimacs.py input.qcir -o output.qdimacs --reclim 25000")
            f2 = open("output.qdimacs", "r")
            self.QDIMACS_str = f2.read()
            f2.close()
            remove("input.qcir")
            remove("output.qdimacs")
            return self.QDIMACS_str

        elif self.format == Format.circuit_NON_PRENEX:
            print("Prenexing not yet supported!")
    
    def generate_QDIMACS_from_prenex_QCIR(self):
        # if QCIR was not generated yet, do it
        if not self.QCIR_str:
            self.generate_QCIR()
        
        split_QCIR = self.QCIR_str.splitlines()
        qdimacs_str = ""
        currentQuant = ""
        currentLine = ""
        nClauses = 0
        for line in split_QCIR:
            if line.startswith("exists"):
                lits = self.get_lits_from_line(line)
                if currentQuant == "e":
                    for lit in lits:
                        currentLine += " " + str(lit)
                else:
                    if currentLine != "":
                        qdimacs_str += currentLine + " 0\n"
                    currentQuant = "e"
                    currentLine = "e"
                    for lit in lits:
                        currentLine += " " + str(lit)


            elif line.startswith("forall"):
                lits = self.get_lits_from_line(line)
                if currentQuant == "a":
                    for lit in lits:
                        currentLine += " " + str(lit)
                else:
                    if currentLine != "":
                        qdimacs_str += currentLine + " 0\n"
                    currentQuant = "a"
                    currentLine = "a"
                    for lit in lits:
                        currentLine += " " + str(lit)

            elif "or" in line:
                nClauses += 1
                qdimacs_str += currentLine + " 0\n"
                currentLine = ""
                lits = self.get_lits_from_line(line)
                for lit in lits:
                    if currentLine != "":
                        currentLine += " " + lit
                    else:
                        currentLine += lit

        qdimacs_str += currentLine + " 0\n"
        preamble = "c Formula Family: {}\n".format(self.get_name())
        preamble += "c Values: {}\n".format(self.get_values())
        preamble += "p cnf {} {}\n".format(len(self.variables), nClauses)
        self.QDIMACS_str = preamble + qdimacs_str
        return self.QDIMACS_str
    
    def get_lits_from_line(self, line):
        p1 = line.find("(")
        p2 = line.find(")")
        lits = line[p1+1:p2]
        return lits.split(", ")
        
    # ================= Additional methods =================

    """
        Evaluates the expression expr bringing into scope the existing
        values. Additional valued variables can be added in extraValues.
    """
    def evaluate(self, expr, extraValues={}):
        variables = [var for var in self.values] + [var for var in extraValues]
        assigned_values = [val for val in self.values.values()] + [val for val in extraValues.values()]
        pairs = zip(variables, assigned_values)
        for p in pairs:
            assignment = "{} = {}".format(p[0], p[1])
            try:
                exec(assignment)
            except:
                print("EVALUATION ERROR: unable to execute {}".format(assignment))
                exit()

        try: 
            return eval(expr)
        except:
            print("EVALUATION ERROR: unable to evaluate {}".format(expr))
            exit()

    """
        Normalizes a variable name given some indices and valued indices.
    """
    def normalize_name(self, varName, varIndices, valuedIndices={}):
        varName = varName + '('
        for index in varIndices:
            varName = varName + ' ' + str(valuedIndices[index]) if index in valuedIndices else varName + ' ' + str(index)
        varName = varName + ' )'
        return varName

    """
        Iterates over a list of conditions, generating all possible tuples of values
        for the given indices.
    """
    def iterate(self, conditions, extra_valued_indices={}):
        stack = [[{}, 0]]
        while stack:
            valuedIndices, currentCondition = stack.pop(0)
            if currentCondition < len(conditions):
                condition = conditions[currentCondition]
                if condition[0] == 'other':
                    booleanCondition = self.evaluate(condition[1], valuedIndices)
                    if booleanCondition:
                        stack.append([valuedIndices.copy(), currentCondition + 1])
                    else:
                        continue
                else:
                    index = condition[0]
                    if index not in extra_valued_indices:
                        lim1 = self.evaluate(condition[1][0], valuedIndices)
                        lim2 = self.evaluate(condition[1][1], valuedIndices)
                        for ix in range(lim1, lim2 + 1):
                            valuedIndices[index] = ix
                            stack.append([valuedIndices.copy(), currentCondition + 1])
                    else:
                        valuedIndices[index] = extra_valued_indices[index]
                        stack.append([valuedIndices.copy(), currentCondition + 1])
            else:
                yield valuedIndices

    """
        Substitues indices for values.
    """    
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
    
    """
        Checks whether a certain name is already used for a block or a variable.
    """
    def is_defined(self, name):
        return (name in self.variables) or (name in self.blocks)
    
    """
        Prints the internal representation of the formula
    """
    def print_formula(self):
        my_formula = "========== Printed QBF ==========\n"
        my_formula = my_formula + "Printing the formula of the family {}, defined in {} format, for the VALUES:\n".format(self.get_name(), self.get_format_str()) 
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


verbose = False
formula = QBF()

#==============================================================================
#=============================== Traversal Class ==============================
#==============================================================================
"""
    A set of functions triggered from the grammar that handle tokens read
    in the input file.

    It generates a QBF object that is updated with the information gathered
    from the parsed definition.

"""
@v_args(inline=True)
class TraverseTree(Transformer):

    """ Creates an empty QBF object that will be updated as parsing proceeds """
    def __init__(self):
        if formula:
            self.formula = formula
        else:
            self.formula = QBF()
    
    """ Handles a value assignment such as 'value: k = 10;' """
    def handle_value(self, name, expr):
        if verbose:
            print("VALUE: Handling parameter {} with value {}.".format(name, expr))
        
        self.formula.add_value(str(name), str(expr))

    """ Sets the name of the formula family """
    def set_name(self, name):
        if verbose:
            print("NAME: setting name \"{}\".".format(name))
        
        self.formula.set_name(str(name))
    
    """ Sets the format of the formula family """
    def set_format(self, f):
        if verbose:
            print("FORMAT: setting format \'{}\'.".format(f))
        
        self.formula.set_format(str(f))
    
    """ Handles a parameter declaration """    
    def add_parameter(self, p, t, *c):
        constr = []
        for elem in c:
            constr.append(str(elem))
        
        if verbose:
            print("PARAMETER: adding parameter {} of type {} with constraints {}".format(p, t, constr))
        
        self.formula.add_parameter(str(p), str(t), constr)
        
    """ Hanldes a variable declaration """    
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
        
        if verbose:
            print("VARIABLE: adding variable {} with indices {} and ranges {}".format(varName, varIndices, completeRanges))
        
        self.formula.add_variables(varName, varIndices, completeRanges)
    
    """ Hanldes block definitions """    
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
    
    """ Hanldes attribute declarations """   
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
        
        for block in name_indices_pairs:
            if verbose:
                print("ATTRIBUTE: adding attribute {} to block {} with indices {}".format(att, block[0], block[1]))

            self.formula.add_attribute(block[0], block[1], att)

    """ Hanldes attributes for groupings """   
    def add_attribute_to_grouping(self, grp, att):
        grp_name = str(grp)
        att = str(att)
        if verbose:
            print("ATTRIBUTE: adding attribute {} to all blocks in grouping {}".format(att, grp_name))
        self.formula.add_attributes_grp(grp, att)
    
    """ Hanldes conditions in block definitions """   
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
        
    """ Hanldes block definition individually """   
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
        
        if verbose:
            print("BLOCK: adding block {} with body {}.".format(block_name, bricks_to_send))

        return [block_name, bricks_to_send]
    
    """ Hanldes groupings """   
    def handle_grouping(self, grp):
        if grp:
            return str(grp.children[0])
        else:
            return grp

    """ Sets the output block """   
    def add_final_block(self, name, indices=[]):
        if indices:
            indices = [str(ix) for ix in indices.children]

        if verbose:
            print("FINAL BLOCK: block {} with indices {} saves as output block".format(name, indices))
        
        self.formula.save_final_block(name, indices)
        
            
    """ Returns the built QBF object """
    def return_formula(self, *r):
        return self.formula

#==============================================================================
#=============================== Script functions =============================
#==============================================================================

def generate(input_file, values_file, internal, output_formats):
    # Generate the parsing function from the grammar and the traversal class
    #grammar_file = open("grammar.lark", "r")
    #grammar = grammar_file.read()
    parser_obj = Lark(grammar, parser='lalr', transformer=TraverseTree())
    parse = parser_obj.parse

    # Read values file
    try:
        f = open(values_file, "r")
    except:
        print("FILE ERROR: the values file {} does not exist or could not be opened.".format(values_file))
        exit()
    v = f.read()
    f.close()

    # Parse values:
    try:
        formula = parse(v)
    except Exception as e:
        s = str(e)
        #print(s)
        start = s.find("at line")
        finish = s.find("Expected one")
        print("PARSING ERROR: invalid syntax when parsing the values {}".format(s[start:finish-1]))
        exit()


    # Read input definition file
    try:
        f = open(input_file, "r")
    except:
        print("FILE ERROR: the input file {} does not exist or could not be opened.".format(input_file))
        exit()
    s = f.read()
    f.close()

    # Parse the definition and get a QBF object with the internal repr.
    try:
        formula = parse(s)
    except Exception as e:
        s = str(e)
        #print(s)
        start = s.find("at line")
        finish = s.find("Expected one")
        print("PARSING ERROR: invalid syntax when parsing the definition {}".format(s[start:finish-1]))
        exit()

    # Output the formula
    if internal:
        formula.print_formula() # basic readable form of the internal repr.

    for output in output_formats: # user-given formats
        form = output[0]
        outp = output[1]
        formula_str = ""
        if output[0] == "-QDIMACS":
            formula_str = formula.get_QDIMACS_string()
        elif output[0] == "-QCIR":
            formula_str = formula.get_QCIR_string()
        elif output[0] == "-non-prenex-QCIR":
            formula_str = formula.get_non_prenex_QCIR_string()

        if outp == "-stdIO":
            print("")
            print(formula_str)
            print("")
        else:
            f = open(outp, "w")
            f.write(formula_str)
            f.close()
    
def read_arguments():
    global verbose
    input_file = argv[1]
    values_file = argv[2]
    internal = False
    outputs = []
    current_format = [[], []]
    for arg in argv[3::]:
        if arg == "-internal":
            internal = True
        elif arg == "-verbose":
            verbose = True
        elif arg in ["-QDIMACS", "-QCIR", "-non-prenex-QCIR"]:
            if current_format[0]:
                if not current_format[1]:
                    current_format[1] = "-stdIO"
                outputs.append(current_format)
                current_format = [[], []]
            current_format[0] = arg
        elif current_format[0]:
            current_format[1] = arg
            outputs.append(current_format)
            current_format = [[], []]
        else:
            print("Invalid arguments: {}".format(arg))
            exit()
        
    if current_format[0]:
        if not current_format[1]:
            current_format[1] = "-stdIO"
        outputs.append(current_format)   

    if len(outputs) == 0 and not internal:
        print("Invalid arguments")
        exit()

    return input_file, values_file, internal, outputs

def print_help():
    print("")
    print("Input should be of the form:")
    print("")
    print("python main.py input_file [-internal] [-QDIMACS {file.qdimacs | [-stdIO]}] [-QCIR {file.QCIR | [-stdIO]}] [-non-prenex-QCIR {file.QCIR | [-stdIO]}]")
    print("")

def run_generator():

    # Preliminary check of arguments:
    if len(argv) <= 1:
        print("Missing arguments!")
        return
    elif len(argv) > 11:
        print("Too many arguments!")
        return
    elif len(argv) == 2 and argv[1] in ["-help", "--help", "-h", "--h"]:
        print_help()
        return

    # Process arguments:
    input_file, values_file, internal, output_formats  = read_arguments()
    generate(input_file, values_file,  internal, output_formats)

run_generator()


#if __name__ == '__main__':
#    main()