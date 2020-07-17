import sys
import ply.yacc as yacc
from lekser import tokens
import re

mem_iterator = 16
variab = {}
delcared = {}
tables = {}
markers_val = []

def p_program(p):
    '''program : DECLARE declarations BEGIN commands END'''
    p[0] = delete_markers("SUB 0 \nINC \nSTORE 6 \nDEC \nDEC \nSTORE 12 \n" + p[4] + "HALT")
def p_program_noD(p):
    '''program : BEGIN commands END'''
    p[0] = delete_markers("SUB 0 \nINC \nSTORE 6 \nDEC \nDEC \nSTORE 12 \n" + p[2] + "HALT")


def p_declarations_variable(p):
    '''declarations : declarations ID COMMA '''
    id= p[2]
    lineno = str(p.lineno(2))
    create_variable(id, lineno)

def p_declarations_variable_last(p):
    '''declarations : declarations ID  '''
    id = p[2]
    lineno = str(p.lineno(2))
    create_variable(id, lineno)

def p_declarations_table_neg_pos(p):
    '''declarations : declarations ID LBR NEG NUM COLON NUM RBR COMMA '''
    id= p[2]
    lineno = str(p.lineno(2))
    start = 0
    stop = p[7] + p[5]
    move = p[5]
    create_table(id, start, stop, move, lineno)

def p_declarations_table_neg_pos_last(p):
    '''declarations : declarations ID LBR NEG NUM COLON NUM RBR '''
    id = p[2]
    lineno = str(p.lineno(2))
    start = 0
    stop = p[7] + p[5]
    move = p[5]
    create_table(id, start, stop, move, lineno)


def p_declarations_table_pos_neg(p):
    '''declarations : declarations ID LBR NUM COLON NEG NUM RBR COMMA '''
    id = p[2]
    lineno =  str(p.lineno(2))
    raise Exception("ERROR in line: " + lineno + '. Niewłaściwy zakres tablicy ' + id)

def p_declarations_table_pos_neg_last(p):
    '''declarations : declarations ID LBR NUM COLON NEG NUM RBR '''
    id = p[2]
    lineno =  str(p.lineno(2))
    raise Exception("ERROR in line: " + lineno + '. Niewłaściwy zakres tablicy ' + id)

def p_declarations_table_neg_neg(p):
    '''declarations : declarations ID LBR NEG NUM COLON NEG NUM RBR COMMA '''
    id = p[2]
    start = 0
    stop = p[5] - p[8]
    move = p[5]
    lineno = str(p.lineno(2))
    create_table(id, start, stop, move, lineno)

def p_declarations_table_neg_neg_last(p):
    '''declarations : declarations ID LBR NEG NUM COLON NEG NUM RBR  '''
    id= p[2]
    start = 0
    stop = p[5] - p[8]
    move = p[5]
    lineno = str(p.lineno(2))
    create_table(id, start, stop, move, lineno)

def p_declarations_table_pos_pos(p):
    '''declarations : declarations ID LBR NUM COLON NUM RBR COMMA '''
    id = p[2]
    start = p[4]
    stop = p[6]
    move = 0
    lineno= str(p.lineno(2))
    create_table(id, start, stop, move, lineno)

def p_declarations_table_pos_pos_last(p):
    '''declarations : declarations ID LBR NUM COLON NUM RBR '''
    id = p[2]
    start = p[4]
    stop = p[6]
    move = 0
    lineno = str(p.lineno(2))
    create_table(id, start, stop, move, lineno)


def p_declarations_empty(p):
    '''declarations : '''



def p_commands_mult(p):
    '''commands : commands command '''
    p[0] = p[1] + p[2]


def p_commands_one(p):
    '''commands : command'''
    p[0] = p[1]

def p_command_assign(p):
    '''command : identifier ASSIGN expression SEMICOLON '''
    identifier = p[1]
    expression = p[3]
    lineno = str(p.lineno(1))
    p[0] = get_address(identifier, 0, lineno) + \
           "STORE 2\n" + \
           expression + \
           "STOREI 2\n"
    delcared[identifier[1]] = True


def p_command_if(p):
    '''command : IF condition THEN commands ENDIF'''
    condition = p[2]
    commands_if = p[4]
    lineno = str(p.lineno(1))
    p[0] =  condition[0] + \
           commands_if + \
           condition[1]


def p_command_if_else(p):
    '''command : IF condition THEN commands ELSE commands ENDIF'''
    condition = p[2]
    commands_if = p[4]
    commands_else = p[6]
    lineno = str(p.lineno(1))
    labels, jumps = add_markers(1)
    p[0] =  condition[0] + \
           commands_if + \
           "JUMP " + jumps[0] + "\n" + \
           condition[1] + \
           commands_else + \
           labels[0]

def p_command_while(p):
    '''command : WHILE condition DO commands ENDWHILE'''
    labels, jumps = add_markers(1)
    condition = p[2]
    commands = p[4]
    lineno = str(p.lineno(1))
    p[0] =  labels[0] + \
           condition[0] + \
           commands + \
           "JUMP " + jumps[0] + "\n" + \
           condition[1]


def p_command_dowhile(p):
    '''command : DO commands WHILE condition ENDDO '''
    labels, jumps = add_markers(1)
    commands = p[2]
    condition = p[4]
    lineno =  str(p.lineno(1))
    p[0] = labels[0] + \
           commands + \
           condition[0] + \
           "JUMP " + jumps[0] + "\n" + \
           condition[1]


def p_iterator(p):
    '''iterator : ID '''
    id= p[1]
    lineno = str(p.lineno(1))
    p[0] = id
    create_variable(id, lineno)
    delcared[id] = True


def p_command_for_to_pp(p):
    '''command : FOR iterator FROM value TO value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    temp = create_temp()
    iterator = p[2]
    start_val = p[4]
    stop_val = p[6]
    commands = p[8]
    lineno = str(p.lineno(1))

    p[0] = get_address(("id", temp), 0, lineno) + \
          "STORE 9\n" + \
           get_value(stop_val, "0", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "0", 0, lineno) + \
           "DEC \nSTORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "INC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JPOS " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)


def p_command_for_to_np(p):
    '''command : FOR iterator FROM NEG value TO value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    temp = create_temp()
    iterator = p[2]
    start_val = p[5]
    stop_val = p[7]
    commands = p[9]
    lineno = str(p.lineno(1))

    p[0] = get_address(("id", temp), 0, lineno) + \
           "STORE 9\n" + \
           get_value(stop_val, "0", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "N", 0, lineno) + \
           "DEC \nSTORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "INC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JPOS " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)
def p_command_for_to_pn(p):
    '''command : FOR iterator FROM value TO NEG value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    temp = create_temp()
    iterator = p[2]
    start_val = p[4]
    stop_val = p[7]
    commands = p[9]
    lineno = str(p.lineno(1))

    p[0] = get_address(("id", temp), 0, lineno) + \
           "STORE 9\n" + \
           get_value(stop_val, "N", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "0", 0, lineno) + \
           "DEC \nSTORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "INC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JPOS " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_for_to_nn(p):
    '''command : FOR iterator FROM NEG value TO NEG value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    temp = create_temp()
    iterator = p[2]
    start_val = p[5]
    stop_val = p[8]
    commands = p[10]
    lineno = str(p.lineno(1))

    p[0] = get_address(("id", temp), 0, lineno) + \
           "STORE 9\n" + \
           get_value(stop_val, "N", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "N", 0, lineno) + \
           "DEC \nSTORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "INC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JPOS " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_for_downto_pp(p):
    '''command : FOR iterator FROM value DOWNTO value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    iterator = p[2]
    start_val= p[4]
    stop_val = p[6]
    commands = p[8]
    lineno = str(p.lineno(1))
    temp = create_temp()
    p[0] = get_address(("id", temp), 0, lineno) + \
          "STORE 9\n" + \
           get_value(stop_val, "0", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "0", 0, lineno) + \
           "INC\n STORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "DEC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JNEG " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_for_downto_np(p):
    '''command : FOR iterator FROM NEG value DOWNTO value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    iterator = p[2]
    start_val= p[5]
    stop_val = p[7]
    commands = p[9]
    lineno = str(p.lineno(1))
    temp = create_temp()
    p[0] = get_address(("id", temp), 0, lineno) + \
          "STORE 9\n" + \
           get_value(stop_val, "0", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "N", 0, lineno) + \
           "INC\n STORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "DEC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JNEG " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_for_downto_pn(p):
    '''command : FOR iterator FROM value DOWNTO NEG value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    iterator = p[2]
    start_val= p[4]
    stop_val = p[7]
    commands = p[9]
    lineno = str(p.lineno(1))
    temp = create_temp()
    p[0] = get_address(("id", temp), 0, lineno) + \
          "STORE 9\n" + \
           get_value(stop_val, "N", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "0", 0, lineno) + \
           "INC\n STORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "DEC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JNEG " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_for_downto_nn(p):
    '''command : FOR iterator FROM NEG value DOWNTO NEG value DO commands ENDFOR '''
    marker, jump = add_markers(3)
    iterator = p[2]
    start_val= p[5]
    stop_val = p[8]
    commands = p[10]
    lineno = str(p.lineno(1))
    temp = create_temp()
    p[0] = get_address(("id", temp), 0, lineno) + \
          "STORE 9\n" + \
           get_value(stop_val, "N", 0, lineno) + \
           "STORE 7 \n" + \
           "STOREI 9 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \n" + \
           get_value(start_val, "N", 0, lineno) + \
           "INC\n STORE 8\n" + \
           "STOREI 9\n" + \
           marker[2] + \
           get_value(("id", temp), "0", 0, lineno) + \
           "STORE 7 \n" + \
           get_value(("id", iterator), "0", 0, lineno) + \
           "DEC \n" + \
           "STORE 8 \n" + \
           get_address(("id", iterator), 0, lineno) + \
           "STORE 9 \nLOAD 8 \nSTOREI 9 \n" + \
           "SUB 7\n" + \
           "JNEG " + jump[1] + "\n" + \
           marker[0] + commands + \
           "JUMP " + jump[2] + "\n" + \
           marker[1]

    variab.pop(iterator)

def p_command_input(p):
    '''command : READ identifier SEMICOLON '''
    identifier = p[2]
    lineno =  str(p.lineno(1))
    delcared[identifier[1]] = True
    p[0] = get_address(identifier, 0, lineno) + \
           "STORE 2\n" + \
           "GET \n" + \
           "STOREI 2\n"


def p_command_output(p):
    '''command : WRITE value SEMICOLON '''
    value = p[2]
    lineno = str(p.lineno(1))
    p[0] = get_value_check(value, "0", 0, lineno) + \
           "PUT \n"


def p_command_output_neg(p):
    '''command : WRITE NEG value SEMICOLON '''
    value = p[3]
    lineno = str(p.lineno(1))
    p[0] = get_value(value, "N", 0, lineno) + \
           "PUT \n"



def p_expression_value(p):
    '''expression : value'''  #
    value = p[1]
    lineno = str(p.lineno(1))
    p[0] =  get_value_check(value, "0", 0, lineno)


def p_expression_value_neg(p):
    '''expression : NEG value'''  #
    value = p[2]
    lineno = str(p.lineno(1))
    p[0] = get_value_check(value, "N", 0, lineno)


def p_expression_plus(p):
    '''expression : value PLUS value'''
    val_a = p[1]
    val_b = p[3]
    lineno =  str(p.lineno(1))

    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 3\n" + \
           get_value(val_b, "0", 0, lineno) + \
           "ADD 3\n"


def p_expression_minus(p):
    '''expression : value MINUS value'''
    val_a = p[1]
    val_b = p[3]
    lineno =  str(p.lineno(1))
    p[0] = get_value(val_b, "0", 0, lineno) + \
           "STORE 3\n" + \
           get_value(val_a, "0", 0, lineno) + \
           "SUB 3\n"


def p_expression_mult_pp(p):
    '''expression : value MULT value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(9)
    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[4] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[4] + get_value(val_b, "0", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[5] + "\n" + \
           "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[5] + " SUB 3\n JPOS " + jump[8] + "\n " + "LOAD 4 \nSTORE 5 \nLOAD 3 \nSTORE 4 \nLOAD 5 \nSTORE 3\n" + marker[8] + \
           "SUB 0 \nSTORE 5 \n" + \
           "" + marker[3] + " LOAD 3 \nJZERO " + jump[2] + "\n" + \
           "LOAD 3 \nSHIFT 12 \nSHIFT 6 \nSUB 3 \nJNEG " + jump[0] + "\n" + \
           "JPOS " + jump[0] + "\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 5 \nADD 4 \nSTORE 5 \n" + \
           "" + marker[1] + "LOAD 3\nSHIFT 12\nSTORE 3\n" + \
           "LOAD 4 \nADD 4 \nSTORE 4\n" + \
           "JUMP " + jump[3] + "\n" + \
           "" + marker[2] + "LOAD 5\n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 3 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[6] + "\n" + \
           "LOAD 3 \nJNEG " + jump[6] + "\n" + \
           "SUB 0 \nSUB 5 \nSTORE 5 \n" + marker[6] + \
           "LOAD 3 \nJPOS " + jump[7] + "\n" + \
           "LOAD 4 \nJNEG " + jump[7] + "\n" + \
           "SUB 0 \nSUB 5\nSTORE 5 \n " + marker[7] + \
           "LOAD 5\n"

def p_expression_mult_np(p):
    '''expression : NEG value MULT value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(9)
    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[4] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[4] + get_value(val_b, "0", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[5] + "\n" + \
           "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[5] + " SUB 3\n JPOS " + jump[8] + "\n " + "LOAD 4 \nSTORE 5 \nLOAD 3 \nSTORE 4 \nLOAD 5 \nSTORE 3\n" + marker[8] + \
           "SUB 0 \nSTORE 5 \n" + \
           "" + marker[3] + " LOAD 3 \nJZERO " + jump[2] + "\n" + \
           "LOAD 3 \nSHIFT 12 \nSHIFT 6 \nSUB 3 \nJNEG " + jump[0] + "\n" + \
           "JPOS " + jump[0] + "\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 5 \nADD 4 \nSTORE 5 \n" + \
           "" + marker[1] + "LOAD 3\nSHIFT 12\nSTORE 3\n" + \
           "LOAD 4 \nADD 4 \nSTORE 4\n" + \
           "JUMP " + jump[3] + "\n" + \
           "" + marker[2] + "LOAD 5\n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 3 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[6] + "\n" + \
           "LOAD 3 \nJNEG " + jump[6] + "\n" + \
           "SUB 0 \nSUB 5 \nSTORE 5 \n" + marker[6] + \
           "LOAD 3 \nJPOS " + jump[7] + "\n" + \
           "LOAD 4 \nJNEG " + jump[7] + "\n" + \
           "SUB 0 \nSUB 5\nSTORE 5 \n " + marker[7] + \
           "LOAD 5\n"

def p_expression_mult_pn(p):
    '''expression : value MULT NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(9)
    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[4] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[4] + get_value(val_b, "N", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[5] + "\n" + \
           "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[5] + " SUB 3\n JPOS " + jump[8] + "\n " + "LOAD 4 \nSTORE 5 \nLOAD 3 \nSTORE 4 \nLOAD 5 \nSTORE 3\n" + marker[8] + \
           "SUB 0 \nSTORE 5 \n" + \
           "" + marker[3] + " LOAD 3 \nJZERO " + jump[2] + "\n" + \
           "LOAD 3 \nSHIFT 12 \nSHIFT 6 \nSUB 3 \nJNEG " + jump[0] + "\n" + \
           "JPOS " + jump[0] + "\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 5 \nADD 4 \nSTORE 5 \n" + \
           "" + marker[1] + "LOAD 3\nSHIFT 12\nSTORE 3\n" + \
           "LOAD 4 \nADD 4 \nSTORE 4\n" + \
           "JUMP " + jump[3] + "\n" + \
           "" + marker[2] + "LOAD 5\n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 3 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[6] + "\n" + \
           "LOAD 3 \nJNEG " + jump[6] + "\n" + \
           "SUB 0 \nSUB 5 \nSTORE 5 \n" + marker[6] + \
           "LOAD 3 \nJPOS " + jump[7] + "\n" + \
           "LOAD 4 \nJNEG " + jump[7] + "\n" + \
           "SUB 0 \nSUB 5\nSTORE 5 \n " + marker[7] + \
           "LOAD 5\n"

def p_expression_mult_nn(p):
    '''expression : NEG value MULT  NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(9)
    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[4] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[4] + get_value(val_b, "N", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[5] + "\n" + \
           "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[5] + " SUB 3\n JPOS " + jump[8] + "\n " + "LOAD 4 \nSTORE 5 \nLOAD 3 \nSTORE 4 \nLOAD 5 \nSTORE 3\n" + marker[8] + \
           "SUB 0 \nSTORE 5 \n" + \
           "" + marker[3] + " LOAD 3 \nJZERO " + jump[2] + "\n" + \
           "LOAD 3 \nSHIFT 12 \nSHIFT 6 \nSUB 3 \nJNEG " + jump[0] + "\n" + \
           "JPOS " + jump[0] + "\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 5 \nADD 4 \nSTORE 5 \n" + \
           "" + marker[1] + "LOAD 3\nSHIFT 12\nSTORE 3\n" + \
           "LOAD 4 \nADD 4 \nSTORE 4\n" + \
           "JUMP " + jump[3] + "\n" + \
           "" + marker[2] + "LOAD 5\n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 3 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 4 \n" + \
           "JPOS " + jump[6] + "\n" + \
           "LOAD 3 \nJNEG " + jump[6] + "\n" + \
           "SUB 0 \nSUB 5 \nSTORE 5 \n" + marker[6] + \
           "LOAD 3 \nJPOS " + jump[7] + "\n" + \
           "LOAD 4 \nJNEG " + jump[7] + "\n" + \
           "SUB 0 \nSUB 5\nSTORE 5 \n " + marker[7] + \
           "LOAD 5\n"

def p_expression_div_pp(p):
    '''expression : value DIV value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + \
           jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 4 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \n LOAD 13 \n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[10] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[12] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[13] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[13] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[11] + "LOAD 4 \n"

def p_expression_div_np(p):
    '''expression : NEG value DIV value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + \
           jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 4 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \n LOAD 13 \n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[10] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[12] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[13] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[13] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[11] + "LOAD 4 \n"

def p_expression_div_pn(p):
    '''expression : value DIV NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + \
           jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 4 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \n LOAD 13 \n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[10] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[12] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[13] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[13] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[11] + "LOAD 4 \n"

def p_expression_div_nn(p):
    '''expression : NEG value DIV NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + \
           jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 4 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \n LOAD 13 \n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[10] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[12] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[13] + " \nLOAD 4\nINC \nSTORE 4 \n" + marker[13] + "SUB 0 \nSUB 4\n STORE 4 \n" + \
           "" + marker[11] + "LOAD 4 \n"

def p_expression_mod_pp(p):
    '''expression : value MOD value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 13 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \nLOAD 13 \n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[12] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + "\nSUB 0\n SUB 3 \nSUB 13 \nSTORE 13 \n" + marker[12] + "SUB 0 \nSUB 13\n STORE 13 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[11] + " \nLOAD 3\nSUB 13 \nSTORE 13 \n" + \
           "" + marker[11] + "LOAD 13 \n "

def p_expression_mod_np(p):
    '''expression : NEG value MOD value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 13 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \nLOAD 13 \n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "0", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[12] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + "\nSUB 0\n SUB 3 \nSUB 13 \nSTORE 13 \n" + marker[12] + "SUB 0 \nSUB 13\n STORE 13 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[11] + " \nLOAD 3\nSUB 13 \nSTORE 13 \n" + \
           "" + marker[11] + "LOAD 13 \n "
def p_expression_mod_pn(p):
    '''expression : value MOD NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "0", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 13 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \nLOAD 13 \n" + \
           get_value(val_a, "0", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[12] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + "\nSUB 0\n SUB 3 \nSUB 13 \nSTORE 13 \n" + marker[12] + "SUB 0 \nSUB 13\n STORE 13 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[11] + " \nLOAD 3\nSUB 13 \nSTORE 13 \n" + \
           "" + marker[11] + "LOAD 13 \n "

def p_expression_mod_nn(p):
    '''expression : NEG value MOD NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(14)

    p[0] = get_value(val_a, "N", 0, lineno) + \
           "STORE 13 \n" + \
           "JPOS " + jump[8] + "\n" + \
           "SUB 0 \nSUB 13\n STORE 13 \nJZERO " + jump[4] + "\n" + \
           "" + marker[8] + get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[9] + "\n" + \
           "SUB 0 \nSUB 3\n STORE 3 \n" + \
           "" + marker[9] + "JZERO " + jump[4] + "\n" + \
           "SUB 0 \nSTORE 4 \n" + \
           "LOAD 3\n STORE 14\n" + \
           "JUMP " + jump[1] + "\n" + \
           "" + marker[0] + "LOAD 3 \n" + marker[1] + \
           " SHIFT 6 \nSTORE 3 \n SHIFT 6\n DEC\n SUB 13\n JZERO " + jump[0] + "\nJNEG " + jump[0] + "\n" + \
           "LOAD 3 \n" + marker[2] + "INC \n SUB 14 \n JZERO " + jump[7] + "\nJNEG " + jump[7] + "\n" + \
           "LOAD 3 \n SUB 13 \nJZERO " + jump[3] + "\nJNEG " + jump[3] + "\n" + \
           "LOAD 4 \nSHIFT 6 \nSTORE 4 \nLOAD 3 \nSHIFT 12\nSTORE 3\n JUMP " + jump[2] + "\n" + \
           "" + marker[3] + "LOAD 4\nSHIFT 6 \nINC \nSTORE 4 \nLOAD 13 \nSUB 3 \nSTORE 13\nLOAD 3\nSHIFT 12\n STORE 3\nJUMP " + jump[2] + "\n" + \
           "" + marker[4] + "SUB 0 \nSTORE 13 \n JUMP " + jump[11] + "\n" + \
           "" + marker[7] + "LOAD 3 \n LOAD 5 \nLOAD 13 \n" + \
           get_value(val_a, "N", 0, lineno) + \
           "STORE 15 \n" + \
           get_value(val_b, "N", 0, lineno) + \
           "STORE 3 \n" + \
           "JPOS " + jump[10] + "\n" + \
           "LOAD 15 \n JNEG " + jump[12] + "\n" + \
           "LOAD 13 \n JZERO " + jump[12] + "\nSUB 0\n SUB 3 \nSUB 13 \nSTORE 13 \n" + marker[12] + "SUB 0 \nSUB 13\n STORE 13 \n" + \
           "" + marker[10] + \
           "LOAD 15 \n JPOS " + jump[11] + "\n" + \
           " LOAD 3 \n JNEG " + jump[11] + "\n" + \
           "LOAD 13 \nJZERO " + jump[11] + " \nLOAD 3\nSUB 13 \nSTORE 13 \n" + \
           "" + marker[11] + "LOAD 13 \n "

def p_condition_eq_pp(p):
    '''condition : value EQ value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n",
            "LOAD 6\n" + marker[0])
def p_condition_eq_np(p):
    '''condition : NEG value EQ value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n",
            "LOAD 6\n" + marker[0])
def p_condition_eq_pn(p):
    '''condition : value EQ NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n",
            "LOAD 6\n" + marker[0])
def p_condition_eq_nn(p):
    '''condition : NEG value EQ NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n",
            "LOAD 6\n" + marker[0])

def p_condition_neq_pp(p):
    '''condition : value NEQ value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6\n" + marker[0])
def p_condition_neq_np(p):
    '''condition : NEG value NEQ value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6\n" + marker[0])
def p_condition_neq_pn(p):
    '''condition : value NEQ NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6\n" + marker[0])
def p_condition_neq_nn(p):
    '''condition : NEG value NEQ NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6\n" + marker[0])
def p_condition_le_pp(p):
    '''condition : value LE value'''
    val_a= p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])
def p_condition_le_np(p):
    '''condition : NEG value LE value'''
    val_a= p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])

def p_condition_le_pn(p):
    '''condition : value LE NEG value'''
    val_a= p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])
def p_condition_le_nn(p):
    '''condition : NEG value LE NEG value'''
    val_a= p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])

def p_condition_ge_pp(p):
    '''condition : value GE value'''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6 \n" + marker[0])
def p_condition_ge_np(p):
    '''condition : NEG value GE value'''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6 \n" + marker[0])
def p_condition_ge_pn(p):
    '''condition : value GE NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6 \n" + marker[0])

def p_condition_ge_nn(p):
    '''condition : NEG value GE NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JPOS " + jump[0] + "\n" + \
            "JZERO " + jump[0] + "\n" ,
            "LOAD 6 \n" + marker[0])

def p_condition_leq_pp(p):
    '''condition : value LEQ value'''
    val_a = p[1]
    val_b = p[3]
    lineno =  str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" ,
             "LOAD 6 \n" + marker[0])

def p_condition_leq_np(p):
    '''condition : NEG value LEQ value'''
    val_a = p[2]
    val_b = p[4]
    lineno =  str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" ,
             "LOAD 6 \n" + marker[0])

def p_condition_leq_pn(p):
    '''condition : value LEQ NEG value'''
    val_a = p[1]
    val_b = p[4]
    lineno =  str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" ,
             "LOAD 6 \n" + marker[0])

def p_condition_leq_nn(p):
    '''condition : NEG value LEQ NEG value'''
    val_a = p[2]
    val_b = p[5]
    lineno =  str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 16\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 16\n" + \
            "JNEG " + jump[0] + "\n" ,
             "LOAD 6 \n" + marker[0])

def p_condition_geq_pp(p):
    '''condition : value GEQ value '''
    val_a = p[1]
    val_b = p[3]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 2\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 2\n" + \
            "JPOS " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])

def p_condition_geq_np(p):
    '''condition : NEG value GEQ value '''
    val_a = p[2]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 2\n" + \
            get_value(val_b, "0", 0, lineno) + \
            "SUB 2\n" + \
            "JPOS " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])
def p_condition_geq_pn(p):
    '''condition : value GEQ NEG value '''
    val_a = p[1]
    val_b = p[4]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "0", 0, lineno) + \
            "STORE 2\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 2\n" + \
            "JPOS " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])
def p_condition_geq_nn(p):
    '''condition : NEG value GEQ NEG value '''
    val_a = p[2]
    val_b = p[5]
    lineno = str(p.lineno(1))
    marker, jump = add_markers(1)
    p[0] = (get_value(val_a, "N", 0, lineno) + \
            "STORE 2\n" + \
            get_value(val_b, "N", 0, lineno) + \
            "SUB 2\n" + \
            "JPOS " + jump[0] + "\n",
            "LOAD 6 \n" + marker[0])

def p_value_NUM(p):
    '''value : NUM '''
    p[0] = ("num", p[1])

def p_value_identifier(p):
    '''value : identifier '''
    p[0] = (p[1])

def p_identifier_id(p):
    '''identifier : ID '''
    p[0] = ("id", p[1])

def p_identifier_tab_id(p):
    '''identifier : ID LBR ID RBR '''
    p[0] = ("tab", p[1], ("id", p[3]))

def p_identifier_tab_id_neg(p):
    '''identifier : ID LBR NEG ID RBR '''
    p[0] = ("tab", p[1], ("id", -p[4]))

def p_identifier(p):
    '''identifier : ID LBR NUM RBR '''
    p[0] = ("tab", p[1], ("num", p[3]))

def p_identifier_neg(p):
    '''identifier : ID LBR NEG NUM RBR '''
    p[0] = ("tab", p[1], ("num", -p[4]))


def generate_number(num, is_neg):
    message = ""
    if is_neg == "N":
        if num < 0:
            num = -num
        while num != 0:
            if num % 2 == 0:
                num = num // 2
                message = "SHIFT 6 \n" + message
            else:
                num = num - 1
                message = "DEC \n" + message
        message = "SUB 0 \n" + message
        return message
    else:
        while num != 0:
            if num % 2 == 0:
                num = num // 2
                message = "SHIFT 6 \n" + message
            else:
                num = num - 1
                message = "INC \n" + message
        message = "SUB 0 \n" + message
        return message


def create_table(id, start, stop, move, lineno):
    if stop < start:
        raise Exception("ERROR in line: " + lineno + '. Błędny zakres tablicy ' + id)
    global mem_iterator
    position = mem_iterator + 1
    tables[id] = (position, start, stop, move)
    mem_iterator += (stop - start + 1)


def create_variable(id, lineno):
    if id in variab:
        raise Exception("ERROR in line: " + lineno + '. Ponowna deklaracja ' + id)
    global mem_iterator
    mem_iterator += 1
    variab[id] = mem_iterator


def delete_variable(id):
    variab.pop(id)

def create_temp():
    global mem_iterator
    temp_var_name = "$T" + str(mem_iterator)
    create_variable(temp_var_name, None)
    delcared[temp_var_name] = True
    return temp_var_name

def get_var_index(var_name, lineno):
    if var_name not in variab:
        raise Exception('ERROR in variables')
    else:
        return variab[var_name]

def get_tab_index(tab_name):
    if tab_name not in tables:
        raise Exception('ERROR in tables')
    else:
        return tables[tab_name]

def get_address(value, move, lineno):
    if value[0] == "id":
        if value[1] not in variab:
            if value[1] in tables:
                raise Exception("ERROR in line: " + lineno + '. Niewłaściwa użycie zmiennej tablicowej ' + value[1])
            else:
                raise Exception("ERROR in line: " + lineno + '. Niezadeklarowana zmienna ' + str(value[1]))
        return generate_number(variab[value[1]], "0")

    elif value[0] == "tab":
        if value[1] not in tables:
            if value[1] in variab:
                raise Exception("ERROR in line " + lineno + '. Niewłaściwe użycie zmiennej ' + value[1])
            else:
                raise Exception("ERROR in line: " + lineno + '. Niewłaściwe użycie zmiennej  w tablicy ' + value[1])

        tab_pos, tab_start, tab_stop, move = tables[value[1]]

        cell_index = list(value[2])
        if cell_index[0] == "num":
            cell_index[1] += move
            cell_index = tuple(cell_index)
            move = 0
        start_sign = "0"
        index_sign = "0"
        if tab_start < 0:
            start_sign = "N"
        if cell_index[0] != "id":
            if cell_index[1] < 0:
                index_sign = "N"

        return get_value(cell_index, index_sign, move, lineno) + \
               "STORE 10 \n" + \
               generate_number(tab_start, start_sign) + \
               "STORE 11 \nLOAD 10\n" + \
               "SUB 11" + "\n" + \
               "STORE 10 \n" + \
               generate_number(tab_pos + move, "0") + \
               "STORE 11\n LOAD 10 \n" + \
               "ADD 11" + "\n"
    else:
        raise Exception('ERROR ' + str(value))

def get_value(value, is_neg, move, lineno):
    if value[0] == "num":
        return generate_number(int(value[1]), is_neg)


    if is_neg == "0":
       return get_address(value, move, lineno) + \
           "LOADI 0\n"
    else:
        return get_address(value, move, lineno) + \
               "LOADI 0\nSTORE 1\nSUB 0\nSUB 1\n"

def get_value_check(value, is_neg, move, lineno):
    if value[0] == "num":
        return generate_number(int(value[1]), is_neg)

    if value[0] == "id":

        if value[1] not in delcared:
            raise Exception("ERROR in line: " + lineno + '. Wywołanie niezainicjowanej zmiennej ' + value[1])

    if is_neg == "0":
       return get_address(value, move, lineno) + \
           "LOADI 0\n"
    else:
        return get_address(value, move, lineno) + \
               "LOADI 0\nSTORE 1\nSUB 0\nSUB 1\n"

def add_markers(count):
    t_markers = []
    t_jumps = []
    for i in range(0, count):
        markers_val.append(-1)
        num = str(len(markers_val) - 1)
        t_markers.append("#_mark" + num + "_")
        t_jumps.append("#_jump" + num + "_")
    return (t_markers, t_jumps)


def delete_markers(program):
    line_num = 0
    removed_marksers = []
    for line in program.split("\n"):
        match = re.search("#_mark[0-9]+_", line)
        if match is not None:
            marker_id = int(match.group()[6:-1])
            markers_val[marker_id] = line_num
            line = re.sub("#_mark[0-9]+_", "", line)
        removed_marksers.append(line)
        line_num += 1

    removed_jumps = ""
    for line in removed_marksers:
        match = re.search("#_jump[0-9]+_", line)
        if match is not None:
            jump_id = int(match.group()[6:-1])
            jump_line = markers_val[jump_id]
            line = re.sub("#_jump[0-9]+_", str(jump_line), line)
        removed_jumps += line + "\n"
    return removed_jumps

def p_error(p):
    raise Exception("ERROR in line: " + str(p.lineno) + '. Nierozpoznany napis ' + str(p.value))


parser = yacc.yacc()
f = open(sys.argv[1], "r")
try:
    parsed = parser.parse(f.read(), tracking=True)
except Exception as e:
    print(e)
    exit(-1)
fw = open(sys.argv[2], "w")
fw.write(parsed)