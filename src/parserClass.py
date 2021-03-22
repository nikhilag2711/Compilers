# import necessary libraries
import ply.yacc as yacc
import pygraphviz as pgv
import sys

# Get the token map from lexer
from lexer import tokens

############## Helper Functions ###########
def new_node():
    global itr
    G.add_node(itr)
    n = G.get_node(itr)
    itr += 1
    return n

########### Classes Required ###########

# This class denotes the Node of our Functional AST
class Node:
    def __init__(self,label,children=None,leaf=None,node=None,attributes=None):
        self.label = label
        self.leaf = leaf

        if children:
            self.children = children
        else:
            self.children = []

        if attributes:
            self.attributes = attributes
        else:
            self.attributes = {}
        
        self.attributes["err"] = False  # determines if AST subtree has an error
        self.makeGraph()
    
    # def print_val(self):
    #     for child in self.children:
    #         child.print_val()
    #     print(self.label)
    
    # def should_make_node(self):
    #     for child in self.children:
    #         if child.node:
    #             return True
    #     return False
    
    def makeGraph(self): # for creating the dot dump
        self.node = new_node()
        self.node.attr['label'] = self.label
        listNode = []
        for child in self.children:
            G.add_edge(self.node,child.node)
            listNode.append(child.node)
        for i in range(0,len(self.children)-1):
            G.add_edge(self.children[i].node,self.children[i+1].node,style='invis')

        G.add_subgraph(listNode,rank='same')

# This denotes an entry of the symbol table
class SymTabEntry:

    def __init__(self, name, type=None, attributes=None):
        self.name = name
        if type:
            self.type = type
        else:
            self.type = None
        
        if attributes:
            self.attributes = attributes
        else:
            attributes = {}

######## Important Global Variables

symtab = {}  # right now a global var. If class based parser, then it will become an attribute
ast_root = None # this will contain the root of the AST after it is built
############## Grammar Rules ##############
### Might have to convert it into class based code
def p_primary_expression(p):
    '''
    primary_expression : ID
                       | CONSTANT
                       | STRING_LITERAL
                       | '(' expression ')'
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = Node(str(p[1]))
    elif (len(p) == 4):
        p[0] = p[2]


def p_postfix_expression(p):
    '''
    postfix_expression : primary_expression
                       | postfix_expression INC_OP
                       | postfix_expression DEC_OP
                       | postfix_expression '.' ID
                       | postfix_expression '(' ')'
                       | postfix_expression PTR_OP ID
                       | postfix_expression '[' expression ']'
                       | postfix_expression '(' argument_expression_list ')'
    '''
    # AST Done - see sheet for rules 2-postinc,3-postdec 5,7 and 8
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = Node('POST' + str(p[2]),[p[1]])
    elif (len(p) == 4):
        if p[2] == '.':
            p3val = p[3]
            p[3] = Node(str(p3val))
            
            p[0] = Node('.',[p[1],p[3]])

        elif p[2] == '(':
            p[0] = Node('FuncCall',[p[1]])

        elif p[2] == '->':
            p3val = p[3]
            p[3] = Node(str(p3val))
            
            p[0] = Node('->',[p[1],p[3]])

    elif (len(p) == 5):
        if p[2] == '(':
            p[0] = Node('FuncCall',[p[1],p[3]])
        elif p[2] == '[':
            p[0] = Node('ArrSub',[p[1],p[3]])

def p_argument_expression_list(p):
    '''
    argument_expression_list : assignment_expression
	                         | argument_expression_list ',' assignment_expression
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(',',[p[1],p[3]])

def p_unary_expression(p):
    '''
    unary_expression : postfix_expression
                     | INC_OP unary_expression
                     | DEC_OP unary_expression
                     | SIZEOF unary_expression
                     | unary_operator cast_expression
                     | SIZEOF '(' type_name ')'
    '''
    # AST DONE - check sheet for rule 2- preinc,3- predec,5
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        if p[1] == '++' or p[1] == '--':
            p[0] = Node('PRE' + str(p[1]),[p[2]])
        elif p[1] == 'sizeof':
            p[0] = Node('SIZEOF',[p[2]])
        else:
            p[0] = p[1]
            p[0].children.append(p[2])
            G.add_edge(p[0].node,p[2].node)
    elif (len(p) == 5):
        p[0] = Node('SIZEOF',[p[3]])


def p_unary_operator(p):
    '''
    unary_operator : '&'
                   | '*'
                   | '+'
                   | '-'
                   | '~'
                   | '!'
    '''
    # AST DONE
    p[0] = Node('UNARY' + str(p[1]))

def p_cast_expression(p):
    '''
    cast_expression : unary_expression
	                | '(' type_name ')' cast_expression
    '''
    #AST DONE - rule for 2 in sheet
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 5):
        p[0] = Node('CAST',[p[2],p[4]])

def p_mulitplicative_expression(p):
    '''
    multiplicative_expression : cast_expression
	                          | multiplicative_expression '*' cast_expression
	                          | multiplicative_expression '/' cast_expression
	                          | multiplicative_expression '%' cast_expression
    '''
    #AST DOne
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(str(p[2]),[p[1],p[3]])

def p_additive_expression(p):
    '''
    additive_expression : multiplicative_expression
	                    | additive_expression '+' multiplicative_expression
	                    | additive_expression '-' multiplicative_expression
    '''
    # AST DOne
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(str(p[2]),[p[1],p[3]])

def p_shift_expression(p):
    '''
    shift_expression : additive_expression
	                 | shift_expression LEFT_OP additive_expression
	                 | shift_expression RIGHT_OP additive_expression
    '''
    #AST DOne
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(str(p[2]),[p[1],p[3]])

def p_relational_expression(p):
    '''
    relational_expression : shift_expression
	                      | relational_expression '<' shift_expression
	                      | relational_expression '>' shift_expression
	                      | relational_expression LE_OP shift_expression
	                      | relational_expression GE_OP shift_expression
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(str(p[2]),[p[1],p[3]])

# 10 rules done till here

def p_equality_expression(p):
    '''
    equality_expression : relational_expression
	                    | equality_expression EQ_OP relational_expression
	                    | equality_expression NE_OP relational_expression
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(str(p[2]),[p[1],p[3]])

def p_and_expression(p):
    '''
    and_expression : equality_expression
	               | and_expression '&' equality_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('&',[p[1],p[3]])

def p_exclusive_or_expression(p):
    '''
    exclusive_or_expression : and_expression
	                        | exclusive_or_expression '^' and_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('^',[p[1],p[3]])

def p_inclusive_or_expression(p):
    '''
    inclusive_or_expression : exclusive_or_expression
	                        | inclusive_or_expression '|' exclusive_or_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('|',[p[1],p[3]])

def p_logical_and_expression(p):
    '''
    logical_and_expression : inclusive_or_expression
	                       | logical_and_expression AND_OP inclusive_or_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('&&',[p[1],p[3]])

def p_logical_or_expression(p):
    '''
    logical_or_expression : logical_and_expression
	                      | logical_or_expression OR_OP logical_and_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('||',[p[1],p[3]])


def p_conditional_expression(p):
    '''
    conditional_expression : logical_or_expression
	                       | logical_or_expression '?' expression ':' conditional_expression
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 6):
        p[0] = Node('TERNARY',[p[1],p[3],p[5]])

def p_assignment_expression(p):
    '''
    assignment_expression : conditional_expression
	                      | unary_expression assignment_operator assignment_expression
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = p[2]
        G.add_edge(p[0].node,p[1].node)
        G.add_edge(p[0].node,p[3].node)

        G.add_edge(p[1].node,p[3].node,style='invis')
        G.add_subgraph([p[1].node,p[3].node], rank='same')
        p[0].children.append(p[1])
        p[0].children.append(p[3])

def p_assignment_operator(p):
    '''
    assignment_operator : '='
	                    | MUL_ASSIGN
	                    | DIV_ASSIGN
	                    | MOD_ASSIGN
	                    | ADD_ASSIGN
	                    | SUB_ASSIGN
	                    | LEFT_ASSIGN
	                    | RIGHT_ASSIGN
	                    | AND_ASSIGN
	                    | XOR_ASSIGN
	                    | OR_ASSIGN
    '''
    # AST Done
    p[0] = Node(str(p[1]))

def p_expression(p):
    '''
    expression : assignment_expression
	           | expression ',' assignment_expression
    '''
    # AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(',',[p[1],p[3]])

# 20 done here

def p_constant_expression(p):
    '''
    constant_expression : conditional_expression
    '''
    p[0] = p[1]

## grammar for all expressions done

def p_declaration(p):
    '''
    declaration : declaration_specifiers ';'
	            | declaration_specifiers init_declarator_list ';'
    '''
    if (len(p) == 3):
        p[0] = Node('TypeDecl',[p[1]])
    elif (len(p) == 4):
        p[0] = Node('TypeDecl',[p[1],p[2]])

def p_declaration_specifiers(p):
    '''
    declaration_specifiers : storage_class_specifier
	                       | storage_class_specifier declaration_specifiers
	                       | type_specifier
	                       | type_specifier declaration_specifiers
	                       | type_qualifier
	                       | type_qualifier declaration_specifiers
    '''

    # May cause issues due to enum specifiers
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = p[1]
        G.add_edge(p[0].node, p[2].node)
        p[0].children.append(p[2])

def p_init_declarator_list(p):
    '''
    init_declarator_list : init_declarator
	                     | init_declarator_list ',' init_declarator
    '''
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(',',[p[1],p[3]])

def p_init_declarator(p):
    '''
    init_declarator : declarator
	                | declarator '=' initializer
    '''
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('=',[p[1],p[3]])

def p_storage_class_specifier(p):
    '''
    storage_class_specifier : TYPEDEF
	                        | EXTERN
	                        | STATIC
	                        | AUTO
	                        | REGISTER
    '''
    p[0] = Node(str(p[1]))

def p_type_specifier(p):
    '''
    type_specifier : VOID
	               | CHAR
	               | SHORT
	               | INT
	               | LONG
	               | FLOAT
                   | BOOL
	               | DOUBLE
	               | SIGNED
	               | UNSIGNED
	               | struct_or_union_specifier
	               | enum_specifier
    '''
    if str(p[1]) in ['void' , 'char', 'int', 'long', 'float', 'bool', 'double', 'signed', 'unsigned']:
        p[0] = Node(str(p[1]))
    else:
        p[0] = p[1]

def p_struct_or_union_specifier(p):
    '''
    struct_or_union_specifier : struct_or_union ID '{' struct_declaration_list '}'
	                          | struct_or_union '{' struct_declaration_list '}'
	                          | struct_or_union ID
    '''
    p[0] = p[1]
    if (len(p) == 6):
        p2val = p[2]
        p[2] = Node(str(p2val))

        p[0].node.attr['label'] = p[0].node.attr['label'] + '{}'
        p[0].label = p[0].node.attr['label']

        G.add_edge(p[0].node, p[2].node)
        G.add_edge(p[0].node, p[4].node)
        G.add_edge(p[2].node, p[4].node, style='invis')
        G.add_subgraph([p[2].node, p[4].node], rank='same')
        p[0].children.append(p[2])
        p[0].children.append(p[4])
        # print("Hello")

    elif (len(p) == 5):
        p[0].node.attr['label'] = p[0].node.attr['label'] + '{}'
        p[0].label = p[0].node.attr['label']
        
        G.add_edge(p[0].node, p[3].node)
        p[0].children.append(p[3])
        # print("Hello")


    elif (len(p) == 3):
        p2val = p[2]
        p[2] = Node(str(p2val))
        G.add_edge(p[0].node, p[2].node)
        p[0].children.append(p[2])
        # print("Hello")


def p_struct_or_union(p):
    '''
    struct_or_union : STRUCT
	                | UNION
    '''
    p[0] = Node(str(p[1]))

def p_struct_declaration_list(p):
    '''
    struct_declaration_list : struct_declaration
	                        | struct_declaration_list struct_declaration
    '''

    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = p[2]
        G.add_edge(p[0].node, p[1].node)
        p[0].children.append(p[1])

def p_struct_declaration(p):
    '''
    struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''
    p[0] = Node('StructOrUnionDec',[p[1],p[2]])

def p_specifier_qualifier_list(p):
    '''
    specifier_qualifier_list : type_specifier specifier_qualifier_list
	                         | type_specifier
	                         | type_qualifier specifier_qualifier_list
	                         | type_qualifier
    '''
    # AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = p[1]
        G.add_edge(p[0].node, p[2].node)
        p[0].children.append(p[2])


def p_struct_declarator_list(p):
    '''
    struct_declarator_list : struct_declarator
	                       | struct_declarator_list ',' struct_declarator
    '''
    # AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node(',',[p[1],p[3]])

def p_struct_declarator(p):
    '''
    struct_declarator : declarator
	                  | ':' constant_expression
	                  | declarator ':' constant_expression
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = Node(':',[p[2]])
    elif (len(p) == 4):
        p[0] = Node(':',[p[1],p[3]])


# correct till here

def p_enum_specifier(p):
    '''
    enum_specifier : ENUM '{' enumerator_list '}'
	               | ENUM ID '{' enumerator_list '}'
	               | ENUM ID
    '''
    # AST done
    if (len(p) == 5):
        p[0] = Node('ENUM{}',[p[3]])
    elif (len(p) == 6):
        p2val = p[2]
        p[2] = Node(str(p2val))

        p[0] = Node('ENUM{}',[p[2],p[4]])
    elif (len(p) == 3):
        p2val = p[2]
        p[2] = Node(str(p2val))
        p[0] = Node('ENUM',[p[2]])

def p_enumerator_list(p):
    '''
    enumerator_list : enumerator
	                | enumerator_list ',' enumerator
    '''
    # AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 4):
        p[0] = Node('.',[p[1],p[3]])

def p_enumerator(p):
    '''
    enumerator : ID
	           | ID '=' constant_expression
    '''
    # AST done
    if (len(p) == 2):
        p[0] = Node(str(p[1]))
    elif (len(p) == 4):
        p1val = p[1]
        p[1] = Node(str(p1val))
        p[0] = Node('=',[p[1],p[3]])

def p_type_qualifier(p):
    '''
    type_qualifier : CONST
	               | VOLATILE
    '''
    # AST done
    p[0] = Node(str(p[1]))

# To be done from here

def p_declarator(p):
    '''
    declarator : pointer direct_declarator
	           | direct_declarator
    '''
    #AST done
    if (len(p) == 2):
        p[0] = p[1]
    elif (len(p) == 3):
        p[0] = Node('Decl',[p[1],p[2]])

def p_direct_declarator(p):
    '''
    direct_declarator : ID
	                  | '(' declarator ')'
	                  | direct_declarator '[' ']'
	                  | direct_declarator '(' ')'
	                  | direct_declarator '[' constant_expression ']'
	                  | direct_declarator '(' parameter_type_list ')'
	                  | direct_declarator '(' identifier_list ')'
    '''
    # AST doubt - # to be added or not for rule 3, 4, 5, 6, 7
    if (len(p) == 2):
        p[0] = Node(str(p[1]))
    elif (len(p) == 4):
        if (p[1] == '('):
            p[0] = p[2]
        elif (p[2] == '['):
            p[0] = Node('DDArrSub',[p[1]])
        elif (p[2] == '('):
            p[0] = Node('DDFuncCall',[p[1]])
    elif (len(p) == 5):
        if (p[2] == '('):
            p[0] = Node('DDFuncCall',[p[1],p[3]])
        elif (p[2] == '['):
            p[0] = Node('DDArrSub',[p[1],p[3]])

# correct till here

def p_pointer(p):
    '''
    pointer : '*'
	        | '*' type_qualifier_list
	        | '*' pointer
	        | '*' type_qualifier_list pointer
    '''
    # AST done
    if (len(p) == 2):
        p[0] = Node('PTR')
    elif (len(p) == 3):
        p[0] = Node('PTR',[p[2]])
    elif (len(p) == 4):
        p[0] = Node('PTR',[p[2],p[3]])

def p_type_qualifier_list(p):
    '''
    type_qualifier_list : type_qualifier
	                    | type_qualifier_list type_qualifier
    '''
    # AST doubt
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[2]
        G.add_edge(p[0].node, p[1].node)
        p[0].children.append(p[1])

def p_parameter_type_list(p):
    '''
    parameter_type_list : parameter_list
	                    | parameter_list ',' ELLIPSIS
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    else:
        # Current design choice: parent operator : ',...'
            # Single child : parameter list

        # Alternative design choice: parent operator ','
            # Left child : parameter_list
            # Right child : ELLIPSIS 
        p[0] = Node('ELLIPSIS',[p[1]])

def p_parameter_list(p):
    '''
    parameter_list : parameter_declaration
	               | parameter_list ',' parameter_declaration
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Node(',',[p[1],p[3]])

def p_parameter_declaration(p):
    '''
    parameter_declaration : declaration_specifiers declarator
	                      | declaration_specifiers abstract_declarator
	                      | declaration_specifiers
    '''
    # AST done
    if len(p) == 2:
        p[0] = Node('ParDecl',[p[1]])
    elif len(p) == 3:
        p[0] = Node('ParDecl',[p[1],p[2]])
     
def p_identifier_list(p):
    '''
    identifier_list : ID
	                | identifier_list ',' ID
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = Node(str(p[1]))
    else:
        p3val = p[3]
        p[3] = Node(str(p3val))
        p[0] = Node(',',[p[1],p[3]])

def p_type_name(p):
    '''
    type_name : specifier_qualifier_list
	          | specifier_qualifier_list abstract_declarator
    '''
    # AST done

    if len(p) == 2:
        p[0] = Node('TypeName',[p[1]])
    else:
        p[0] = Node('TypeName',[p[1],p[2]])

def p_abstract_declarator(p):
    '''
    abstract_declarator : pointer
	                    | direct_abstract_declarator
	                    | pointer direct_abstract_declarator
    '''
    # AST done

    if len(p) == 2:
        p[0] = Node('AbsDecl',[p[1]])
    else:
        p[0] = Node('AbsDecl',[p[1],p[2]])

def p_direct_abstract_declarator(p):
    '''
	direct_abstract_declarator : '[' ']'
	                           | '(' ')'
                               | '(' abstract_declarator ')'
	                           | '(' parameter_type_list ')'
	                           | '[' constant_expression ']'
	                           | direct_abstract_declarator '[' ']'
	                           | direct_abstract_declarator '(' ')'
	                           | direct_abstract_declarator '[' constant_expression ']'
	                           | direct_abstract_declarator '(' parameter_type_list ')'
    '''
    # AST done

    if (len(p) == 3):
        if(p[1] == '('):
            p[0] = Node('DAD()')
        elif(p[1] == '['):
            p[0] = Node('DAD[]')

    if (len(p) == 4):
        if(p[1] == '('):
            p[0] = Node('DAD()',[p[2]])
        elif(p[1] == '['):
            p[0] = Node('DAD[]',[p[2]])
        elif(p[2] == '('):
            p[0] = Node('POSTDAD()',[p[1]])
        elif(p[2] == '['):
            p[0] = Node('POSTDAD[]',[p[1]])

    elif (len(p) == 5):
        if (p[2] == '('):
            p[0] = Node('DAD()',[p[1],p[3]])
        elif (p[2] == '['):
            p[0] = Node('DAD[]',[p[1],p[3]])

#correct till here

def p_initializer(p):
    '''
    initializer : assignment_expression
	            | '{' initializer_list '}'
                | '{' initializer_list ',' '}'
    '''
    # AST done
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4 or len(p) == 5:
        p[0] = Node('{}',[p[2]])

def p_initializer_list(p):
    '''
    initializer_list : initializer
	                 | initializer_list ',' initializer
    '''
    # AST done
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node(',',[p[1],p[3]])

def p_statement(p):
    '''
    statement : labeled_statement
	          | compound_statement
	          | expression_statement
	          | selection_statement
	          | iteration_statement
	          | jump_statement
    '''
    # AST Done
    p[0] = p[1]

def p_labeled_statement(p):
    '''
    labeled_statement : ID ':' statement
	                  | CASE constant_expression ':' statement
	                  | DEFAULT ':' statement
    '''
    # AST Done
    if (len(p) == 4):
        if (p[1] == 'default'):
            p[0] = Node('DEFAULT:',[p[3]])
        else:
            p1val = p[1]
            p[1] = Node(str(p1val))
            p[0] = Node('ID:',[p[1],p[3]])
    else:
        p[0] = Node('CASE:',[p[2],p[4]])

def p_compound_statement(p):
    '''
    compound_statement : '{' '}'
	                   | '{' block_item_list '}'
    '''
    if (len(p) == 3):
        p[0] = Node('EmptySCOPE')
    elif (len(p) == 4):
        p[0] = Node('SCOPE',[p[2]])

def p_block_item_list(p):
    '''
    block_item_list : block_item
                    | block_item_list block_item
    '''
    # AST done

    if (len(p) == 2):
        p[0] = Node(';',[p[1]])
    elif (len(p) == 3):
        p[0] = Node(';',[p[1],p[2]])

def p_block_item(p):
    '''
    block_item : declaration
	            | statement
    '''
    # AST Done
    if (len(p) == 2):
        p[0] = p[1]

def p_expression_statement(p):
    '''
    expression_statement : ';'
	                     | expression ';'
    '''
    # AST Done
    if len(p) == 2:
        p[0] = Node('EmptyExprStmt')
    if (len(p) == 3):
        p[0] = p[1]

def p_selection_statement(p):
    '''
    selection_statement : IF '(' expression ')' statement
	                    | IF '(' expression ')' statement ELSE statement
	                    | SWITCH '(' expression ')' statement
    '''
    # AST done
    if(len(p) == 6):
        p[0] = Node(str(p[1]).upper(),[p[3],p[5]])
    else:
        p[0] = Node('IF-ELSE',[p[3],p[5],p[7]])

# Correct till here

def p_iteration_statement(p):
    '''
    iteration_statement : WHILE '(' expression ')' statement
	                    | DO statement WHILE '(' expression ')' ';'
	                    | FOR '(' expression_statement expression_statement ')' statement
	                    | FOR '(' expression_statement expression_statement expression ')' statement
	                    | FOR '(' declaration expression_statement ')' statement
	                    | FOR '(' declaration expression_statement expression ')' statement
    '''
    # AST done
    if len(p) == 6:
        p[0] = Node('WHILE',[p[3],p[5]])
    elif len(p) == 7:
        p[0] = Node('FOR',[p[3],p[4],p[6]])
    else:
        if (p[1] == 'do'):
            p[0] = Node('DO-WHILE',[p[2],p[5]])
        else:
            p[0] = Node('FOR',[p[3],p[4],p[5],p[7]])

def p_jump_statement(p):
    '''
    jump_statement : GOTO ID ';'
	               | CONTINUE ';'
	               | BREAK ';'
	               | RETURN ';'
	               | RETURN expression ';'
    '''
    # AST done
    if (len(p) == 3):
        p[0] = Node(str(p[1]).upper())
    else:
        if(p[1] == 'return'):
            p[0] = Node('RETURN',[p[2]])
        else:
            p2val = p[2]
            p[2] = Node(str(p2val))
            p[0] = Node('GOTO',[p[2]])

def p_translation_unit(p):
    '''
    translation_unit : external_declaration
	                 | translation_unit external_declaration
    '''
    # AST done
    # Here
    # Hack to restrict single source node
    p[0] = 'SourceNode'

    if (len(p) == 2):
        G.add_edge(p[0] , p[1].node)
    elif (len(p) == 3):
        G.add_edge(p[0], p[2].node)


def p_external_declaration(p):
    '''
    external_declaration : function_definition
	                     | declaration
    '''
    # AST Done
    p[0] = p[1]

def p_function_definition(p):
    '''
    function_definition : declaration_specifiers declarator declaration_list compound_statement
	                    | declaration_specifiers declarator compound_statement
	                    | declarator declaration_list compound_statement
	                    | declarator compound_statement
    '''
    # AST doubt
    if (len(p) == 3):
        p[0] = Node('FUNC',[p[1],p[2]])
    elif (len(p) == 4):
        p[0] = Node('FUNC',[p[1],p[2],p[3]])
    elif (len(p) == 5):
        p[0] = Node('FUNC',[p[1],p[2],p[3],p[4]])

def p_declaration_list(p):
    '''
    declaration_list : declaration
	                 | declaration_list declaration
    '''
    # AST done
    if (len(p) == 2):
        p[0] = Node(';',[p[1]])
    elif (len(p) == 3):
        p[0] = Node(';',[p[1],p[2]])

def p_error(p):
    print('Error found while parsing!')
    global isError
    isError = 1

# driver code
parser = yacc.yacc(start='translation_unit', outputdir='./tmp')

G = pgv.AGraph(strict=False, directed=True)
G.layout(prog='circo')

itr = 0 # Global var to give unique IDs to nodes of the graph

isError = 0
if len(sys.argv) == 1:
    print('No file given as input')
    sys.exit(1)

file = open(sys.argv[1], 'r')
data = file.read()
result = parser.parse(data)

fileNameCore = str(sys.argv[1]).split('/')[-1].split('.')[0]
outputFile = 'dot/' + fileNameCore + '.dot'

if isError == 1:
    print(f'Error found. Aborting parsing of {sys.argv[1]}....')
    sys.exit(1)
else:
    print('Output file is: ' + fileNameCore + '.ps')
    G.write(outputFile)