#######################################
# Constantes
#######################################
from ast import expr
from cgitb import reset
from math import factorial
from multiprocessing import context
from select import select
#from time import clock_settime
from turtle import ondrag
from unittest import result
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
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Caracter incorrecto', details)

class InvalidSyntaxError(Error):
	def __init__(self, pos_start, pos_end, details=''):
		super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, contexto):
        super().__init__(pos_start, pos_end, 'Error de ejecucion', details)
        self.contexto = contexto 
    def como_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}\n'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result   
    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.contexto
        while ctx:
            result = f'  Archivo {pos.fn}, linea: {str(pos.ln + 1)}, en {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent
        return f'Reatrear (la mas reciente ultima llamada):\n{result}'

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
            elif self.current_char == '^':
                tokens.append(Token(POT,pos_start=self.pos))
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

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end
    def __repr__(self):
        return f'{self.tok}'
class OperadorUnario:
    def __init__(self,op_tok,node):
        self.op_tok = op_tok
        self.node = node

        self. pos_start = self.left_node.pos_start
        self.pos_end = node.pos_end
    
    def __repr__(self):
        return f'({self.op_tok}, {self.node}'
class OperadorBinario:
    def __init__(self,left_node,op_tok,right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self. pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end
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
    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (ENT, REAL):
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
        return res.fallo(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Se esperaba ENT, REAL, '+', '-' o '('"))    
    
    def power(self):
        return self.bin_op(self.atom, (POT,), self.factor)
    
    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (MAS,MENOS):
            res.registrar(self.avanzar())
            factor = res.registrar(self.factor())
            if res.error: return res
            return res.correcto(OperadorUnario(tok,factor))

        return self.power()
    
    def term(self):
        return self.bin_op(self.factor, (MULT, DIV))

    def expr(self):
        return self.bin_op(self.term, (MAS, MENOS))

#######################################
    def bin_op(self, func_a, ops, func_b = None):
        if func_b == None:
            func_b = func_a
        res = ParseResult()
        left = res.registrar(func_a())
        if res.error: return res
        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.registrar(self.avanzar())
            right = res.registrar(func_b())
            if res.error: return res
            left = OperadorBinario(left, op_tok, right)
        
        return res.correcto(left)
#######################################
# Runtime result
#######################################
class RuntimeResult:
    def __init__(self):
        self.error = None
        self.value = None
    def register(self,res):
        if res.error: self.error = res.error
        return res.value
    def success(self,value):
        self.value = value
        return self
    def failure(self,error):
        self.error = error
        return self

#######################################
# Valores
#######################################
class Numero:
    def __init__(self,value):
        self.value = value
        self.set_posicion()
        self.set_contexto()
    def set_posicion(self,pos_start = None,pos_end = None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    def set_contexto(self,contexto = None):
        self.contexto = contexto
        return self
    def sumado_A(self, otro):
        if isinstance(otro, Numero):
            return Numero(self.value + otro.value).set_contexto(self.contexto), None
    def restado_Por(self, otro):
        if isinstance(otro, Numero):
            return Numero(self.value - otro.value).set_contexto(self.contexto), None
    def multiplicado_Por(self, otro):
        if isinstance(otro, Numero):
            return Numero(self.value * otro.value).set_contexto(self.contexto), None
    def dividido_Por(self, otro):
        if isinstance(otro, Numero):
            if otro.value == 0:
                return None, RTError(otro.pos_start, otro.pos_end, 'Division entre 0', self.contexto)
            return Numero(self.value / otro.value).set_contexto(self.contexto), None
    def elevado_A(self, otro):
        if isinstance(otro, Numero):
            return Numero(self.value ** otro.value).set_contexto(self.contexto), None
    def __repr__(self):
        return str(self.value)
#######################################
# Contexto
#######################################
class Contexto:
    def __init__(self,display_name,parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
#######################################
# Interpretador
#######################################
class Interpretador:
    def visit(self, node, contexto):
        metodo_nombre = f'visit_{type(node).__name__}'
        metodo = getattr(self, metodo_nombre, self.No_visitar_metodo)
        return metodo(node, contexto)
    def No_visitar_metodo(self, node, contexto):
        raise Exception(f'No visit_{type(node).__name__} method defined')
    #######################################
    def visit_NumeroNodo(self, node, contexto):
        return RuntimeResult().success(Numero(node.tok.value).set_contexto(contexto).set_posicion(node.pos_start, node.pos_end)) 
            

    def visit_OperadorUnario(self, node, contexto):
        res = RuntimeResult()
        numero = res.register(self.visit(node.node, contexto))
        if res.error: return res

        error = None
        
        if node.op_tok.type == MENOS:
            numero, error = numero.multiplicado_Por(Numero(-1))
        if error: return res.failure(error)
        else:
            return res.success(numero.set_posicion(node.pos_start, node.pos_end))

    def visit_OperadorBinario(self, node, contexto):
        res = RuntimeResult()
        left = res.register(self.visit(node.left_node, contexto))
        if res.error: return res
        right = res.register(self.visit(node.right_node, contexto))
        if res.error: return res

        if node.op_tok.type == MAS:
            result, error = left.sumado_A(right)
        elif node.op_tok.type == MENOS:
            result, error = left.restado_Por(right)
        elif node.op_tok.type == MULT:
            result, error = left.multiplicado_Por(right)
        elif node.op_tok.type == DIV:
            result, error = left.dividido_Por(right)
        elif node.op_tok.type == POT:
            result, error = left.elevado_A(right)
        
        if error:
            return res.failure(error)
        else:
            return res.success(result.set_posicion(node.pos_start, node.pos_end))

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
    if ast.error: return None, ast.error

    #Correr programa
    interpreter = Interpretador()
    contexto = Contexto('<programa>')
    result = interpreter.visit(ast.node, contexto)

    return result.value, result.error

  


