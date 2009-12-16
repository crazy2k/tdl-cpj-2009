#!/usr/bin/env python
#coding: utf8

import sys

from pyparsing import *
from optparse import OptionParser


# ================================
# Definicion de gramatica y tokens
# ================================

LPAREN = Literal("(").suppress()
RPAREN = Literal(")").suppress()

natural = Word(nums) # natural contempla tambien el 0
realpositivo = Combine(natural + Optional(Combine("." + Word(nums)))) | Combine("." + Word(nums))
real = realpositivo | Combine(Literal("-") + realpositivo)

grafico = Forward()
grafico_agr = Forward()

nombre_a_definir = Word(alphanums)
nombre_definido = Word(alphanums)

circulo = Literal("circle") + realpositivo 
caja = Literal("box") + realpositivo + realpositivo
mover = Literal("move") + real + real + grafico_agr
escalar = Literal("scale") + real + real + grafico_agr
rotar = Literal("rotate") + real + grafico_agr
repetir = Literal("repeat") + natural + real + real + grafico_agr
definir = Literal("define") + nombre_a_definir + grafico_agr

funcion = circulo | caja | mover | escalar | rotar | repetir | definir

funcion_agr = Group(funcion)

expresion = funcion_agr | nombre_definido

grafico << (Group(OneOrMore(Group(expresion) | Group(LPAREN + expresion + RPAREN))) |
    Group(OneOrMore(Group(LPAREN + grafico + RPAREN))))

grafico_agr << (expresion | LPAREN + grafico + RPAREN)

# =================================================
# Funciones auxiliares de las "acciones de parsing"
# =================================================

ps_save = "\n" + "gsave" + "\n"
ps_restore = "\n" + "grestore" + "\n"

tabla_nombres = {}

def aislar(ps):
    return ps_save + ps + ps_restore

def presult_a_string(pr):
    r = ""
    if isinstance(pr, ParseResults):
        for x in pr:
            r += presult_a_string(x)
        return r

    if isinstance(pr, str):
        return pr + "\n"

# ===================================
# Definicion de "acciones de parsing"
# ===================================

def traducir_caja(tokens):
    ancho = tokens[1]
    altura = tokens[2]
    ps = "%s %s scale box" % (ancho, altura)
    return aislar(ps)

def traducir_circulo(tokens):
    radio = tokens[1]
    ps = "%s %s scale circ" % (radio, radio)
    return aislar(ps)

def traducir_mover(tokens):
    dx = tokens[1]
    dy = tokens[2]
    g = presult_a_string(tokens[3])
    ps = "%s %s translate %s" % (dx, dy, g)
    return aislar(ps)

def traducir_rotar(tokens):
    a = tokens[1]
    g = presult_a_string(tokens[2])
    ps = "%s rotate %s" % (a, g)
    return aislar(ps)

def traducir_escalar(tokens):
    fx = tokens[1]
    fy = tokens[2]
    g = presult_a_string(tokens[3])
    ps = "%s %s scale %s" % (fx, fy, g)
    return aislar(ps)

def traducir_repetir(tokens):
    n = tokens[1]
    dx = tokens[2]
    dy = tokens[3]
    g = presult_a_string(tokens[4])
    ps = """%s {
%s
%s %s translate
} repeat""" % (n, g, dx, dy)

    return aislar(ps)

def traducir_definir(tokens):
    nombre = tokens[1]
    g = presult_a_string(tokens[2])

    psclave = ["circle", "box", "rotate", "move", "scale", "repeat", "define"]

    if nombre in psclave:
        raise ErrorTP("La palabra " + nombre + " es una palabra reservada" +
            " y no puede usarse como nombre de un grafico.")
    
    tabla_nombres[nombre] = g
    return ""

def traducir_nombre(tokens):
    nombre = tokens[0]

    if nombre in tabla_nombres:
        return tabla_nombres[nombre]

    raise ErrorTP("El nombre " + nombre + " no ha sido definido.")

# =====================================================
# Correspondencias entre tokens y "acciones de parsing"
# =====================================================

caja.setParseAction(traducir_caja)
circulo.setParseAction(traducir_circulo)
mover.setParseAction(traducir_mover)
rotar.setParseAction(traducir_rotar)
escalar.setParseAction(traducir_escalar)
repetir.setParseAction(traducir_repetir)
definir.setParseAction(traducir_definir)
nombre_definido.setParseAction(traducir_nombre)

# ===========================
# Funciones auxiliares varias
# ===========================


class ErrorTP(Exception):
    def __init__(self, msg):
        Exception.__init__(self, "ERROR: " + msg)


def agregar_contexto(codigo_ps):
    encabezado = """
5 dict begin
/box {
  0 0 moveto 0 1 lineto 1 1 lineto 1 0 lineto closepath fill
} def
/circ {
  0 0 1 0 360 arc closepath fill
} def

"""
    pie = """
end
showpage"""

    return encabezado + codigo_ps + pie

XMAX = float(612) 
YMAX = float(792)
COLS = 4
FILAS = 6
FILA_SIZE = YMAX/FILAS
COL_SIZE = XMAX/COLS
DX = COL_SIZE/2
DY = FILA_SIZE/2

def posicionar(posicion, contenido):
    posx = posicion % COLS
    posy = posicion/COLS

    x = posx*COL_SIZE + DX
    y = YMAX - (posy*FILA_SIZE + DY)

    despl = "move %d %d " % (x, y)

    return despl + "(" + contenido + ")\n"

def escalar_inicial(contenido):
    esc = "scale %s %s " % (options.scalex, options.scaley)
    return esc + "(" + contenido + ")"

def trasladar_inicial(contenido):
    trans = "move %s %s " % (options.translatex, options.translatey)
    return trans + "(" + contenido + ")"


if __name__ == "__main__":

    # Definimos las opciones del script.
    optparser = OptionParser()

    optparser.add_option("-o", "--output", dest = "archivo_salida",
        default = "-", metavar = "ARCHIVO",
        help = "escribir la salida en el archivo ARCHIVO. Si ARCHIVO es `-'," +
            " usar la salida estandar.")
    optparser.add_option("-g", "--grid", dest = "grid",
        default = False, action = "store_true",
        help = "ubicar el resultado de cada una de las entradas en una grilla")
    optparser.add_option("--scalex", dest = "scalex",
        default = "1", metavar = "FACTOR",
        help = "escalar en X la salida segun el factor FACTOR.")
    optparser.add_option("--scaley", dest = "scaley",
        default = "1", metavar = "FACTOR",
        help = "escalar en Y la salida segun el factor FACTOR.")
    optparser.add_option("--translatex", dest = "translatex",
        default = "0", metavar = "DX",
        help = "trasladar en X segun DX. (La traslacion se produce antes que" +
            " el escalamiento.)")
    optparser.add_option("--translatey", dest = "translatey",
        default = "0", metavar = "DY",
        help = "trasladar en Y segun DY. (La traslacion se produce antes que" +
            " el escalamiento.)")

    

    (options, args) = optparser.parse_args()

    if len(args) == 0:
        # No se especificaron archivos de entrada, asi que leemos de stdin.
        input = trasladar_inicial(escalar_inicial(sys.stdin.read()))

    else:
        # Se especificaron archivos de entrada. Usamos la concatenacion de
        # sus contenidos como entrada.
        input = ""
        for i, fname in enumerate(args):
            f = open(fname)
            fcontent = f.read()

            fcontent = trasladar_inicial(escalar_inicial(fcontent))

            if options.grid:
                fcontent = posicionar(i, fcontent)

            input += fcontent

            f.close()

    # El lenguaje F es case-insensitive.
    input = input.lower()

    try:
        print input

        presult = (grafico + stringEnd).parseString(input)

        codigo_ps = presult_a_string(presult)

        codigo_ps = agregar_contexto(codigo_ps)
        
        if options.archivo_salida == "-":
            # `-' quiere decir "salida estandar"
            print codigo_ps
        else:
            fname = options.archivo_salida
            f = open(fname, "w")
            f.write(codigo_ps)
            f.close()
    except Exception as e:
        print >> sys.stderr, e
        

# XXX: Ver el tema de -g con entrada estandar.
