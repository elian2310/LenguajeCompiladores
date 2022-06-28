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