#######################################
# Constantes
#######################################
from ast import Num, expr, keyword
from asyncio import selector_events
from cgitb import reset
from lib2to3.pgen2 import token
from math import factorial
from multiprocessing import context
import re
from select import select
#from time import clock_settime
from turtle import ondrag, pos
from unittest import result
from xml.dom import InvalidCharacterErr
from strings_with_arrows import *
import string

Digitos = '0123456789'
Letras = string.ascii_letters
LetrasyDigitos = Letras + Digitos

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

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Caracter esperado', details)

class InvalidSyntaxError(Error):
	def __init__(self, pos_start, pos_end, details=''):
		super().__init__(pos_start, pos_end, 'Syntaxis Invalida', details)

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
PALCL='PALCL'           #Keyword
ID = 'ID'               #Identificador
MAS = 'MAS'
MENOS = 'MENOS'
MULT = 'MULT'
DIV = 'DIV'
POT = 'POT'
IG = 'IG'               #Igual 
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

RESERVADAS = [
    'VAR',
    'Y',
    'O',
    'NO',
    'SI',
    'ENTONCES',
    'SINOESTO',
    'SINO',
    'POR',
    'A',
    'PASO',
    'MIENTRAS'


]
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
    
    def iguala(self, type_,value):
        return self.type == type_ and self.value == value

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
            elif self.current_char in Letras:
                tokens.append(self.crear_identificador())  
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
            elif self.current_char == '!':
                tok, error = self.crear_diferente()
                if error: return [], error
                tokens.append(tok)
            elif self.current_char == '=':
                tokens.append(self.crear_igual())
            elif self.current_char == '<':
                tokens.append(self.crear_menor())
            elif self.current_char == '>':
                tokens.append(self.crear_mayor())
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

    def crear_identificador(self):
        id_str = ''
        pos_start = self.pos.copiar()

        while self.current_char != None and self.current_char in LetrasyDigitos + '_':
            id_str += self.current_char
            self.avanzar()
        
        token_type = PALCL if id_str in RESERVADAS else ID
        return Token(token_type, id_str, pos_start, self.pos)
    
    def crear_diferente(self):
        pos_ini = self.pos.copiar()
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            return Token(NI, pos_start=pos_ini, pos_end=self.pos), None
        self.avanzar()
        return None, ExpectedCharError(pos_ini, self.pos, "'=' despues de '!'")
    
    def crear_igual(self):
        tipo_tok = IG
        pos_ini = self.pos.copiar()
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = II
        return Token(tipo_tok, pos_start=pos_ini,pos_end=self.pos)
    
    def crear_menor(self):
        tipo_tok = MEQ
        pos_ini = self.pos.copiar()
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = MEI
        return Token(tipo_tok, pos_start=pos_ini,pos_end=self.pos)

    def crear_mayor(self):
        tipo_tok = MAQ
        pos_ini = self.pos.copiar()
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = MAI
        return Token(tipo_tok, pos_start=pos_ini,pos_end=self.pos)



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

class AccesoVarNodo:
    def __init__(self, nombre_var_tok):
        self.nombre_var_tok = nombre_var_tok
        self.pos_start = self.nombre_var_tok.pos_start 
        self.pos_end = self.nombre_var_tok.pos_end

class AsignamientoVarNodo:
    def __init__(self, nombre_var_tok,val_nodo):
        self.nombre_var_tok = nombre_var_tok
        self.val_nodo = val_nodo
        self.pos_start = self.nombre_var_tok.pos_start 
        self.pos_end = self.nombre_var_tok.pos_end

class OperadorUnario:
    def __init__(self,op_tok,node):
        self.op_tok = op_tok
        self.node = node

        self. pos_start = self.op_tok.pos_start
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

class SiNodo:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case =  else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end

class PorNodo:
    def __init__(self, nom_var_tok, val_ini_nodo, val_fin_nodo, paso_nodo, cuerpo_nodo):
        self.nom_var_tok = nom_var_tok
        self.val_ini_nodo = val_ini_nodo
        self.val_fin_nodo = val_fin_nodo
        self.paso_nodo = paso_nodo
        self.cuerpo_nodo = cuerpo_nodo

        self.pos_ini = self.nom_var_tok.pos_start
        self.pos_fin = self.cuerpo_nodo.pos_end

class MientrasNodo:
    def __init__(self, condicion_nodo, cuerpo_nodo):
        self.condicion_nodo = condicion_nodo
        self.cuerpo_nodo = cuerpo_nodo

        self.pos_ini = condicion_nodo.pos_start
        self.pos_fin = cuerpo_nodo.pos_end



#######################################
# Parse Result
#######################################  

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.cuenta_avance = 0
    
    def registro_avance(self):
        self.cuenta_avance += 1

    def registrar(self,res):
        self.cuenta_avance += res.cuenta_avance
        if res.error: self.error = res.error
        return res.node

    def correcto(self,node):
        self.node = node
        return self 

    def fallo(self,error):
        if not self.error or self.cuenta_avance == 0: 
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
    def if_expr(self):
        res = ParseResult()
        cases = []
        else_case = None
        if not self.current_tok.iguala(PALCL, 'SI'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Se esperaba 'SI'"))
        res.registro_avance()
        self.avanzar()
        condicion= res.registrar(self.expr())
        if res.error: return res

        if not self.current_tok.iguala(PALCL, 'ENTONCES'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Se esperaba 'ENTONCES'"))
        res.registro_avance()
        self.avanzar()
        expr= res.registrar(self.expr())
        if res.error: return res
        cases.append((condicion,expr))

        while self.current_tok.iguala(PALCL, 'SINOESTO'):
            res.registro_avance()
            self.avanzar()

            condicion= res.registrar(self.expr())
            if res.error: return res
            if not self.current_tok.iguala(PALCL, 'ENTONCES'):
                return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Se esperaba 'ENTONCES'"))

            res.registro_avance()
            self.avanzar()

            expr= res.registrar(self.expr())
            if res.error: return res
            cases.append((condicion, expr))
        if self.current_tok.iguala(PALCL, 'SINO'):
            res.registro_avance()
            self.avanzar()

            else_case=res.registrar(self.expr())
            if res.error: return res
        return res.correcto(SiNodo(cases, else_case))

    def por_expr(self):
        res = ParseResult()

        if not self.current_tok.iguala(PALCL, 'POR'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba 'POR'"))

        res.registro_avance()
        self.avanzar()

        if self.current_tok.type != ID:
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba Identificador"))

        nom_var = self.current_tok
        res.registro_avance()
        self.avanzar()

        if self.current_tok.type != IG:
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba '='"))

        res.registro_avance()
        self.avanzar()

        val_ini = res.registrar(self.expr())
        if res.error: return res

        if not self.current_tok.iguala(PALCL, 'A'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba 'A'"))

        res.registro_avance()
        self.avanzar()

        val_fin = res.registrar(self.expr())
        if res.error : return res

        if self.current_tok.iguala(PALCL, 'PASO'):
            res.registro_avance()
            self.avanzar()

            val_paso = res.registrar(self.expr())
            if res.error: return res

        else:
            val_paso = None

        if not self.current_tok.iguala(PALCL, 'ENTONCES'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba 'ENTONCES'"))

        res.registro_avance()
        self.avanzar()

        cuerpo = res.registrar(self.expr())
        if res.error: return res

        return res.correcto(PorNodo(nom_var, val_ini, val_fin, val_paso, cuerpo))

    def mientras_expr(self):
        res = ParseResult()

        if not self.current_tok.iguala(PALCL, 'MIENTRAS'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba 'MIENTRAS'"))

        res.registro_avance()
        self.avanzar()

        condicion = res.registrar(self.expr())
        if res.error: return res

        if not self.current_tok.iguala(PALCL, 'ENTONCES'):
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Esperaba 'ENTONCES'"))

        res.registro_avance()
        self.avanzar()

        cuerpo = res.registrar(self.expr())
        if res.error: return res

        return res.correcto(MientrasNodo(condicion, cuerpo))


    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (ENT, REAL):
            res.registro_avance()
            self.avanzar()
            return res.correcto(NumeroNodo(tok))
        elif tok.type == ID:
            res.registro_avance()
            self.avanzar()
            return res.correcto(AccesoVarNodo(tok))
        elif tok.type == PARENIZQ:
            res.registro_avance()
            self.avanzar()
            expr = res.registrar(self.expr())
            if res.error: return res
            if self.current_tok.type   == PARENDER:
                res.registro_avance()
                self.avanzar()
                return res.correcto(expr)
            else:
                return res.fallo(InvalidCharacterErr(self.current_tok.pos_start, self.current_tok.pos_end,"Se esperaba ')'"))
        
        elif tok.iguala(PALCL, 'SI'):
            if_expr = res.registrar(self.if_expr())
            if res.error: return res
            return res.correcto(if_expr)

        elif tok.iguala(PALCL, 'POR'):
            por_expr = res.registrar(self.por_expr())
            if res.error: return res
            return res.correcto(por_expr)
        
        elif tok.iguala(PALCL, 'MIENTRAS'):
            mientras_expr = res.registrar(self.mientras_expr())
            if res.error: return res
            return res.correcto(mientras_expr)


        return res.fallo(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Se esperaba ENT, REAL, ID, '+', '-' o '('"))    
    
    def power(self):
        return self.bin_op(self.atom, (POT,), self.factor)
    
    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (MAS,MENOS):
            res.registro_avance()
            self.avanzar()
            factor = res.registrar(self.factor())
            if res.error: return res
            return res.correcto(OperadorUnario(tok,factor))

        return self.power()
    
    def term(self):
        return self.bin_op(self.factor, (MULT, DIV))

    def expr_arit(self):
        return self.bin_op(self.term, (MAS, MENOS))

    def expr_comp(self):
        res = ParseResult()

        if self.current_tok.iguala(PALCL, 'NO'):
            tok_op = self.current_tok
            res.registro_avance()
            self.avanzar()
            nodo = res.registrar(self.expr_comp())
            if res.error: return res
            return res.correcto(OperadorUnario(tok_op, nodo))
        
        nodo = res.registrar(self.bin_op(self.expr_arit, (II, NI, MEQ, MAQ, MEI, MAI)))

        if res.error:
            return res.fallo(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Se esperaba ENT, REAL, ID, '+', '-', '(' o 'NO'"
            ))

        return res.correcto(nodo)

    def expr(self):
        res=ParseResult()
        if self.current_tok.iguala(PALCL,'VAR'):
            res.registro_avance()
            self.avanzar()
            if self.current_tok.type != ID:
                return res.fallo(InvalidSyntaxError(
                    self.current_tok.pos_start,self.current_tok.pos_end,"Se esperaba UN identificador"))

            nombre_variable = self.current_tok
            res.registro_avance()
            self.avanzar()

            if self.current_tok.type != IG:
                return res.fallo(InvalidSyntaxError(
                    self.current_tok.pos_start,self.current_tok.pos_end,"Se esperaba '='"))
            
            res.registro_avance()
            self.avanzar()
            expresion = res.registrar(self.expr())
            if res.error: return res
            return res.correcto(AsignamientoVarNodo(nombre_variable, expresion))

        node =  res.registrar(self.bin_op(self.expr_comp, ((PALCL, "Y"), (PALCL, "O"))))
        if res.error: 
            return res.fallo(InvalidSyntaxError(self.current_tok.pos_start,self.current_tok.pos_end,
                "Se esperaba 'VAR, 'ENT, REAL, ID, '+', '-' o '('"))
        return res.correcto(node)

#######################################
    def bin_op(self, func_a, ops, func_b = None):
        if func_b == None:
            func_b = func_a
        res = ParseResult()
        left = res.registrar(func_a())
        if res.error: return res
        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.registro_avance()
            self.avanzar()
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

    def comparacion_ig(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value == otro.value)).set_contexto(self.contexto), None
    
    def comparacion_dif(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value != otro.value)).set_contexto(self.contexto), None
    
    def comparacion_meq(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value < otro.value)).set_contexto(self.contexto), None

    def comparacion_maq(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value > otro.value)).set_contexto(self.contexto), None

    def comparacion_mei(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value <= otro.value)).set_contexto(self.contexto), None

    def comparacion_mai(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value >= otro.value)).set_contexto(self.contexto), None

    def y_por(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value and otro.value)).set_contexto(self.contexto), None

    def o_por(self, otro):
        if isinstance(otro, Numero):
            return Numero(int(self.value or otro.value)).set_contexto(self.contexto), None

    def negado(self):
        return Numero(1 if self.value == 0 else 0).set_contexto(self.contexto), None

    def copiar(self):
        copiar = Numero(self.value)
        copiar.set_posicion(self.pos_start, self.pos_end)
        copiar.set_contexto(self.contexto)
        return copiar
    
    def es_verdad(self):
        return self.value !=0

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
        self.tabla_simbolos = None

#######################################
# Tabla de simbolos
#######################################

class tabladeSimbolos:
    def __init__(self):
        self.simbolos = {}
        self.padre = None

    def get(self, nombre):
        valor = self.simbolos.get(nombre,None)
        if valor == None and self.padre:
            return self.padre.get(nombre)
        return valor

    def set(self, nombre, valor):
        self.simbolos[nombre] = valor

    def remove(self, nombre):
        del self.simbolos[nombre]

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

    def visit_AccesoVarNodo(self, node, contexto):
        res = RuntimeResult()
        nombre_var = node.nombre_var_tok.value
        value = contexto.tabla_simbolos.get(nombre_var)

        if not value:
            return res.failure(RTError(node.pos_start, node.pos_end,f"'{nombre_var}' no esta definido", contexto))

        value = value.copiar().set_posicion(node.pos_start, node.pos_end)
        return res.success(value)

    def visit_AsignamientoVarNodo(self, node, contexto):
        res = RuntimeResult()
        nombre_var = node.nombre_var_tok.value
        value = res.register(self.visit(node.val_nodo,contexto))

        if res.error: return res
        contexto.tabla_simbolos.set(nombre_var, value)
        return res.success(value)

    def visit_OperadorUnario(self, node, contexto):
        res = RuntimeResult()
        numero = res.register(self.visit(node.node, contexto))
        if res.error: return res

        error = None
        
        if node.op_tok.type == MENOS:
            numero, error = numero.multiplicado_Por(Numero(-1))
        elif node.op_tok.iguala(PALCL, 'NO'):
            numero, error = numero.negado()
        
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
        elif node.op_tok.type == II:
            result, error = left.comparacion_ig(right)
        elif node.op_tok.type == NI:
            result, error = left.comparacion_dif(right)
        elif node.op_tok.type == MEQ:
            result, error = left.comparacion_meq(right)
        elif node.op_tok.type == MAQ:
            result, error = left.comparacion_maq(right)
        elif node.op_tok.type == MEI:
            result, error = left.comparacion_mei(right)
        elif node.op_tok.type == MAI:
            result, error = left.comparacion_mai(right)
        elif node.op_tok.iguala(PALCL, 'Y'):
            result, error = left.y_por(right)
        elif node.op_tok.iguala(PALCL, 'O'):
            result, error = left.o_por(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_posicion(node.pos_start, node.pos_end))
    def visit_SiNodo(self, node, contexto):
        res = RuntimeResult()
        for condition, expr in node.cases:
            condition_value = res.register(self.visit(condition,contexto))
            if res.error: return res

            if condition_value.es_verdad():
                expr_value= res.register(self.visit(expr,contexto))
                if res.error: return res
                return res.success(expr_value)
        if node.else_case:
            else_value= res.register(self.visit(node.else_case, contexto))
            if res.error: return res
            return res.success(else_value)   
        return res.success(None)     

    def visit_PorNodo(self, nodo, contexto):
        res = RuntimeResult()

        val_ini = res.register(self.visit(nodo.val_ini_nodo, contexto))
        if res.error: return res

        val_fin = res.register(self.visit(nodo.val_fin_nodo, contexto))
        if res.error: return res

        if nodo.paso_nodo:
            paso = res.register(self.visit(nodo.paso_nodo, contexto))
            if res.error: return res
        else:
            paso = Numero(1)

        i = val_ini.value

        if paso.value >= 0:
            condicion = lambda: i < val_fin.value
        else:
            condicion = lambda: i > val_fin.value

        while condicion():
            contexto.tabla_simbolos.set(nodo.nom_var_tok.value, Numero(i))
            i += paso.value

            res.register(self.visit(nodo.cuerpo_nodo, contexto))
            if res.error: return res

        return res.success(None)

    def visit_MientrasNodo(self, nodo, contexto):
        res = RuntimeResult()

        while True:
            condicion = res.register(self.visit(nodo.condicion_nodo, contexto))
            if res.error: return res

            if not condicion.es_verdad(): break

            res.register(self.visit(nodo.cuerpo_nodo, contexto))
            if res.error: return res

        return res.success(None)
#######################################
# Correr
#######################################

global_tabla_simbolos = tabladeSimbolos()
global_tabla_simbolos.set("NULO", Numero(0))
global_tabla_simbolos.set("VERDADERO", Numero(1))
global_tabla_simbolos.set("FALSO", Numero(0))

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
    contexto.tabla_simbolos = global_tabla_simbolos
    result = interpreter.visit(ast.node, contexto)

    return result.value, result.error

  


