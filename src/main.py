from sys import argv
from lark import Lark, Transformer, v_args
from representation import QBF
from itertools import chain
from time import time

try:
    input = raw_input   # for Python2 compatibility
except NameError:
    pass

verbose = False

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

def generate(input_file, internal, output_formats):
    # Generate the parsing function from the grammar and the traversal class
    grammar_file = open("grammar.lark", "r")
    grammar = grammar_file.read()
    parser_obj = Lark(grammar, parser='lalr', transformer=TraverseTree())
    parse = parser_obj.parse

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
        print("PARSING ERROR: invalid syntax {}".format(s[start:finish-1]))
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
    internal = False
    outputs = []
    current_format = [[], []]
    for arg in argv[2::]:
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

    return input_file, internal, outputs

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
    elif len(argv) > 10:
        print("Too many arguments!")
        return
    elif len(argv) == 2 and argv[1] in ["-help", "--help", "-h", "--h"]:
        print_help()
        return

    # Process arguments:
    input_file, internal, output_formats  = read_arguments()
    generate(input_file, internal, output_formats)

run_generator()


#if __name__ == '__main__':
#    main()
