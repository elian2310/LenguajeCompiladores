from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
import ñ
import sys
import string

Digitos = '0123456789'
Letras = string.ascii_letters

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
CORCHDER = 'CORCHDER'
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
    'MIENTRAS',
    'FUN',
    'FIN',
    'RETORNAR',
    'CONTINUAR',
    'ROMPER'
]

class Posicion():
    def __init__(self, ln, col, idx):
        self.ln = ln
        self.col = col
        self.idx = idx

    def avanzar(self, ent=None):
        self.col += 1
        self.idx += 1

        if ent == '\n':
            self.ln += 1
            self.col = 0

        return self


class TokenIDE():
    def __init__(self, tipo, pos_start, pos_end):
        self.tipo = tipo
        self.pos_start = pos_start
        self.pos_end = pos_end

class LexerIDE():
    def __init__(self, texto):
        self.texto = texto
        self.pos = Posicion(-1, -1, 0)
        self.current_char = None
        self.avanzar()

    def avanzar(self):
        self.pos.avanzar(self.current_char)
        self.current_char = self.texto[self.pos.idx] if self.pos.idx < len(self.texto) else None

    def crear_token(self):
        tokens = []

        while self.current_char != None:
            print("char: ")
            print(self.current_char)
            if self.current_char in ' \t;\n':
                self.avanzar()
            elif self.current_char in Digitos:
                tokens.append(self.crear_num())
            elif self.current_char in Letras:
                tokens.append(self.crear_id())
            elif self.current_char == '"':
                tokens.append(self.crear_cadena())
            elif self.current_char == '+':
                tokens.append(TokenIDE(MAS, self.pos, self.pos))
                self.avanzar()
            elif self.current_char == '-':
                tokens.append(self.crear_menos_o_flecha())
            elif self.current_char == '*':
                tokens.append(TokenIDE(MULT,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == '/':
                tokens.append(TokenIDE(DIV,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == '^':
                tokens.append(TokenIDE(POT,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == '(':
                tokens.append(TokenIDE(PARENIZQ,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == ')':
                tokens.append(TokenIDE(PARENDER,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == '[':
                tokens.append(TokenIDE(CORCHIZQ,self.pos, self.pos))
                self.avanzar()
            elif self.current_char == ']':
                tokens.append(TokenIDE(CORCHDER,self.pos, self.pos))
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
            elif self.current_char == ',':
                tokens.append(TokenIDE(COMA,self.pos, self.pos))
                self.avanzar()
            else:
                pos_start = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
                char = self.current_char
                self.avanzar()
                return [], ñ.IllegalCharError(pos_start, self.pos, "'" +  char + "'")

        return tokens, None

    def crear_num(self):
        num_str = ''
        dot_count = 0
        pos_start = Posicion(self.pos.ln, self.pos.col, self.pos.idx)

        while self.current_char != None and self.current_char in Digitos + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.avanzar()

        if dot_count == 0:
            return TokenIDE(ENT,pos_start, self.pos)
        else:
            return TokenIDE(REAL,pos_start,self.pos)

    def crear_id(self):
        id_str = ''
        pos_start = Posicion(self.pos.ln, self.pos.col, self.pos.idx)

        while self.current_char != None and self.current_char in Letras + Digitos + '_':
            id_str += self.current_char
            self.avanzar()
        
        token_type = PALCL if id_str in RESERVADAS else ID
        return TokenIDE(token_type, pos_start, self.pos)

    def crear_cadena(self):
        string = ''
        pos_start = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        caracter_escape = False
        self.avanzar()

        caracteres_escape = {
            'n' : '\n',
            't' : '\t'
        }

        while self.current_char != None and self.current_char != '"' or caracter_escape :
            if caracter_escape:
                string += caracteres_escape.get(self.current_char, self.current_char)
            else:
                if self.current_char == '\\':
                    caracter_escape = True
                else:
                    string += self.current_char
            self.avanzar()
            caracter_escape = False
        
        self.avanzar()
        return TokenIDE(CADENA, pos_start, self.pos)

    def crear_menos_o_flecha(self):
        tipo_tok = MENOS
        pos_start = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        self.avanzar()
        
        if self.current_char == '>':
            self.avanzar()
            tipo_tok = FLECHA
        return TokenIDE(tipo_tok,pos_start,self.pos)
    def crear_diferente(self):
        pos_ini = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            return TokenIDE(NI, pos_ini, self.pos), None
        self.avanzar()
        return None, ñ.ExpectedCharError(pos_ini, self.pos, "'=' despues de '!'")
    
    def crear_igual(self):
        tipo_tok = IG
        pos_ini = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = II
        return TokenIDE(tipo_tok, pos_ini,self.pos)
    
    def crear_menor(self):
        tipo_tok = MEQ
        pos_ini = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = MEI
        return TokenIDE(tipo_tok, pos_ini,self.pos)

    def crear_mayor(self):
        tipo_tok = MAQ
        pos_ini = Posicion(self.pos.ln, self.pos.col, self.pos.idx)
        self.avanzar()
        if self.current_char == '=':
            self.avanzar()
            tipo_tok = MAI
        return TokenIDE(tipo_tok, pos_ini,self.pos)
    




class Logger():
    stdout = sys.stdout
    mensajes = []

    def inicio(self):
        sys.stdout = self
    
    def fin(self):
        sys.stdout = self.stdout

    def write(self, text):
        self.mensajes.append(text)

log = Logger()


ventana = Tk()
ventana.title('IDE proyecto final Compiladores')

rutaGuardado = ''

def correrCodigo():
    global rutaGuardado
    resultado.delete('1.0',END)
    if rutaGuardado == '':
        msgGuardar = Toplevel()
        msg = Label(msgGuardar, text="Porfavor guarde el archivo primero")
        msg.pack()
        return
    global log
    log.inicio()
    log.mensajes.clear()
    codigo = editorTexto.get('1.0',END)
    res, error = ñ.exe('IDE',codigo)
    if error: resultado.insert('1.0',error.como_str())
    elif res: 
        if len(res.elementos) == 1:
            resultado.insert('1.0',repr(log.mensajes[0]))
        else:
            str1 = ""
            resultado.insert('1.0',str1.join(log.mensajes))
    log.fin()

def abrirArchivo():
    ruta = askopenfilename(filetypes=[('Archivos de Texto','*.txt')])
    with open(ruta, 'r') as archivo:
        codigo = archivo.read()
        editorTexto.delete('1.0',END)
        editorTexto.insert('1.0', codigo)
        global rutaGuardado
        rutaGuardado = ruta

def guardarComo():
    global rutaGuardado
    if rutaGuardado == '':
        ruta = asksaveasfilename(filetypes=[('Archivos de Texto','*.txt')])
    else:
        ruta = rutaGuardado
    with open(ruta, 'w') as archivo:
        codigo = editorTexto.get('1.0', END)
        archivo.write(codigo)


def colorear():
    tag_cont = 0
    for tag in editorTexto.tag_names():
        editorTexto.tag_delete(tag)
    codigo = editorTexto.get('1.0',END)
    lexer = ñ.Lexer('IDE',codigo)
    tokens, error = lexer.crear_token()
    if error:
        #print("ERROR")
        editorTexto.tag_add("error", f"{error.pos_start.ln}.{error.pos_start.col}",f"{error.pos_end.ln}.{error.pos_end.col}")
        editorTexto.tag_configure("error",foreground="red")
        editorTexto.update()
    else:
        for t in tokens:
            if t.type == PALCL:
                #print(f"a: {t.pos_start.ln}.{t.pos_start.col} | {t.pos_end.ln}.{t.pos_end.col}")
                nom_tag = "tag" + str(tag_cont)
                editorTexto.tag_add(nom_tag, f"{t.pos_start.ln + 1}.{t.pos_start.col}",f"{t.pos_end.ln + 1}.{t.pos_end.col}")
                editorTexto.tag_configure(nom_tag, foreground="pink")
                
            elif t.type== CADENA:
                #print(f"b: {t.pos_start.ln}.{t.pos_start.col} | {t.pos_end.ln}.{t.pos_end.col}")
                nom_tag = "tag" + str(tag_cont)
                editorTexto.tag_add(nom_tag, f"{t.pos_start.ln + 1}.{t.pos_start.col}",f"{t.pos_end.ln + 1}.{t.pos_end.col}")
                editorTexto.tag_configure(nom_tag, foreground="salmon")
            elif t.type == ENT or t.type == REAL:
                #print(f"c: {t.pos_start.ln}.{t.pos_start.col} | {t.pos_end.ln}.{t.pos_end.col}")
                nom_tag = "tag" + str(tag_cont)
                editorTexto.tag_add(nom_tag, f"{t.pos_start.ln}.{t.pos_start.col}",f"{t.pos_end.ln + 1}.{t.pos_end.col}")
                editorTexto.tag_configure(nom_tag, foreground="yellow")
            elif t.type == ID:
                #print(f"d: {t.pos_start.ln}.{t.pos_start.col} | {t.pos_end.ln}.{t.pos_end.col}")
                nom_tag = "tag" + str(tag_cont)
                editorTexto.tag_add(nom_tag, f"{t.pos_start.ln + 1}.{t.pos_start.col}",f"{t.pos_end.ln + 1}.{t.pos_end.col}")
                editorTexto.tag_configure(nom_tag, foreground="cyan")
            editorTexto.update()
            tag_cont += 1


editorTexto = Text()
editorTexto.config(bg='#362f2e', fg='#d2ded1', insertbackground='white')
editorTexto.pack()

resultado = Text(height=7)
resultado.config(bg='#362f2e', fg='#1dd604')
resultado.pack()

barraMenu = Menu(ventana)

barraArchivo = Menu(barraMenu, tearoff=0)
barraArchivo.add_command(label='Abrir', command=abrirArchivo)
barraArchivo.add_command(label='Guardar', command=guardarComo)
barraArchivo.add_command(label='Guardar como', command=guardarComo)
barraArchivo.add_command(label='Salir', command=exit)
barraMenu.add_cascade(label='Archivo', menu=barraArchivo)

barraCorrer = Menu(barraMenu, tearoff=0)
barraCorrer.add_command(label='Correr', command=correrCodigo)
barraCorrer.add_command(label='Analizar', command=colorear)
barraMenu.add_cascade(label='Correr', menu=barraCorrer)


ventana.config(menu=barraMenu)
ventana.mainloop()