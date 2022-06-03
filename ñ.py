#######################################
# Constantes
#######################################
from ast import expr
from cgitb import reset
from math import factorial
from select import select
from turtle import ondrag
from xml.dom import InvalidCharacterErr
from strings_with_arrows import *


Digitos = '0123456789'

#######################################
# Errores
#######################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def como_str(self):
        result  = f'{self.error_name}: {self.details}\n'
        result += f'Archivo: {self.pos_start.fn}, linea: {self.pos_start.ln + 1}, columna: {self.pos_start.col + 1}'
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Caracter incorrecto', details)

#######################################
# Posicion
#######################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def avanzar(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copiar(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#######################################
# Tokens
#######################################

ENT = 'ENT'
REAL = 'REAL'
CADENA = 'CADENA'
ID = 'ID'
MAS = 'MAS'
MENOS = 'MENOS'
MULT = 'MULT'
DIV = 'DIV'
POT = 'POT'
IG = 'IG'
PARENIZQ = 'PARENIZQ'
PARENDER = 'PARENDER'
CORCHIZQ = 'CORCHIZQ'
CORCHIZQ = 'CORCHDER'
II = 'II'
NI = 'NI'
MEQ = 'MEQ'
MAQ = 'MAQ'
MEI = 'MEI'
MAI = 'MAI'
COMA = 'COMA'
FLECHA = 'FLECHA'
NUEVALINEA = 'NUEVALINEA'
FDC = 'FDC'
FINALARCHIVO = 'EOF'


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        if pos_start:
            self.pos_start = pos_start.copiar()
            self.pos_end = pos_start.copiar()
            self.pos_end.avanzar()
        if pos_end: 
            self.pos_end = pos_end
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

#######################################
# Lexer
#######################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.avanzar()
    
    def avanzar(self):
        self.pos.avanzar(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def crear_token(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.avanzar()
            elif self.current_char in Digitos:
                tokens.append(self.crear_num())
            elif self.current_char == '+':
                tokens.append(Token(MAS, pos_start=self.pos))
                self.avanzar()
            elif self.current_char == '-':
                tokens.append(Token(MENOS, pos_start=self.pos))
                self.avanzar()
            elif self.current_char == '*':
                tokens.append(Token(MULT,pos_start=self.pos))
                self.avanzar()
            elif self.current_char == '/':
                tokens.append(Token(DIV,pos_start=self.pos))
                self.avanzar()
            elif self.current_char == '(':
                tokens.append(Token(PARENIZQ,pos_start=self.pos))
                self.avanzar()
            elif self.current_char == ')':
                tokens.append(Token(PARENDER,pos_start=self.pos))
                self.avanzar()
            else:
                pos_start = self.pos.copiar()
                char = self.current_char
                self.avanzar()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(FINALARCHIVO, pos_start= self.pos))
        return tokens, None

    def crear_num(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copiar()

        while self.current_char != None and self.current_char in Digitos + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.avanzar()

        if dot_count == 0:
            return Token(ENT, int(num_str),pos_start, self.pos)
        else:
            return Token(REAL, float(num_str),pos_start,self.pos)



#######################################
# Nodos 
#######################################
class NumeroNodo:
    def __init__(self,tok):
        self.tok = tok
    def __repr__(self):
        return f'{self.tok}'
class OperadorUnario:
    def __init__(self,op_tok,node):
        self.op_tok = op_tok
        self.node = node
    
    def __repr__(self):
        return f'({self.op_tok}, {self.node}'
class OperadorBinario:
    def __init__(self,left_node,op_tok,right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'

#######################################
# Parse Result
#######################################  

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def registrar(self,res):
        if isinstance(res, ParseResult):
            if res.error: self.error = res.error
            return res.node
        return res
    
    def correcto(self,node):
        self.node = node
        return self 
    def fallo(self,error):
        self.error = error
        return self


#######################################
# Parser
#######################################        
class Parser:
    def __init__(self,tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.avanzar()
    
    def avanzar(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok
    
    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != FINALARCHIVO:
            return res.fallo(IllegalCharError(self.current_tok.pos_start, self.current_tok.pos_end, "Se esperaba '+', '-', '*' or '/'"))
        return res
#######################################  

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (MAS,MENOS):
            res.registrar(self.avanzar())
            factor = res.registrar(self.factor())
            if res.error: return res
            return res.correcto(OperadorUnario(tok,factor))
        elif tok.type in (ENT, REAL):
            res.registrar(self.avanzar())
            return res.correcto(NumeroNodo(tok))
        elif tok.type == PARENIZQ:
            res.registrar(self.avanzar())
            expr = res.registrar(self.expr())
            if res.error: return res
            if self.current_tok.type   == PARENDER:
                res.registrar(self.avanzar())
                return res.correcto(expr)
            else:
                return res.fallo(InvalidCharacterErr(self.current_tok.pos_start, self.current_tok.pos_end,"Se esperaba ')'"))

        return res.fallo(IllegalCharError(tok.pos_start, tok.pos_end, "Se esperaba un entero o un numero real"))
    
    def term(self):
        return self.bin_op(self.factor, (MULT, DIV))

    def expr(self):
        return self.bin_op(self.term, (MAS, MENOS))

#######################################
    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.registrar(func())
        if res.error: return res
        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.registrar(self.avanzar())
            right = res.registrar(func())
            if res.error: return res
            left = OperadorBinario(left, op_tok, right)
        
        return res.correcto(left)

#######################################
# Correr
#######################################

def exe(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.crear_token()
    if error: return None, error
    #Generar AST
    parser = Parser(tokens)
    ast = parser.parse()
    return ast.node, ast.error

  


