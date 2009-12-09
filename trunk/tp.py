from pyparsing import *

# ================================
# Definicion de gramatica y tokens
# ================================

LPAREN = Literal("(").suppress()
RPAREN = Literal(")").suppress()

# natural contempla tambien el 0
natural = Word(nums)
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

grafico << (Group(OneOrMore(Group(expresion))) | LPAREN + grafico + RPAREN)
grafico_agr << (expresion | LPAREN + grafico + RPAREN)

# ===================================
# Definicion de "acciones de parsing"
# ===================================

ps_save = "gsave" + "\n"
ps_restore = "\n" + "grestore"

tabla_nombres = {}

def aislar(ps):
    return ps_save + ps + ps_restore

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
    g = pr_a_string(tokens[3])
    ps = "%s %s translate %s" % (dx, dy, g)
    return aislar(ps)

def traducir_rotar(tokens):
    a = tokens[1]
    g = pr_a_string(tokens[2])
    ps = "%s rotate %s" % (a, g)
    return aislar(ps)

def traducir_escalar(tokens):
    fx = tokens[1]
    fy = tokens[2]
    g = pr_a_string(tokens[3])
    ps = "%s %s scale %s" % (fx, fy, g)
    return aislar(ps)

def traducir_repetir(tokens):
    n = tokens[1]
    dx = tokens[2]
    dy = tokens[3]
    g = pr_a_string(tokens[4])
    ps = """%s {
%s
%s %s translate
} repeat""" % (n, g, dx, dy)

    return aislar(ps)

def traducir_definir(tokens):
    nombre = tokens[1]
    g = pr_a_string(tokens[2])

    psclave = ["circle", "box", "rotate", "move", "scale", "repeat", "define"]

    if nombre in psclave:
        raise Exception("La palabra " + nombre + " es una palabra reservada" +
            " y no puede usarse como nombre nombre de un grafico.")
    
    tabla_nombres[nombre] = g
    return ""

def traducir_nombre(tokens):
    nombre = tokens[0]

    if nombre in tabla_nombres:
        return tabla_nombres[nombre]

    raise Exception("El nombre " + nombre + " no ha sido definido.")


caja.setParseAction(traducir_caja)
circulo.setParseAction(traducir_circulo)
mover.setParseAction(traducir_mover)
rotar.setParseAction(traducir_rotar)
escalar.setParseAction(traducir_escalar)
repetir.setParseAction(traducir_repetir)
definir.setParseAction(traducir_definir)
nombre_definido.setParseAction(traducir_nombre)

# =====================================
# Funciones de generacion de Postscript
# =====================================

def pr_a_string(pr):
    r = ""
    if isinstance(pr, ParseResults):
        for x in pr:
            r += pr_a_string(x)
        return r

    if isinstance(pr, str):
        return pr + "\n"

def agregar_encabezado(tr):
    encabezado = """
5 dict begin
/box {
  0 0 moveto 0 1 lineto 1 1 lineto 1 0 lineto closepath fill
} def
/circ {
  0 0 1 0 360 arc closepath fill
} def

100 100 translate
50 50 scale
"""
    # XXX: Borrar el translate y scale de arriba que estan de mas.

    pie = """
end
showpage"""

    return encabezado + tr + pie


def guardar_traduccion(tr, i):
    tr = agregar_encabezado(tr)
    f = open("salida-" + str(i) + ".ps", "w")
    f.write(tr)
    f.close()


l = ["circle .5 box 1 1",
    "circle .5 move 1.5 0 box 1 1",
    "circle .5 move -1.5 0 rotate 45 box 1 1",
    "rotate 45 (scale 1 2 circle .5 move -2 -.5 box 1 1)",
    "move -1.75 0 scale .5 .5 repeat 8 1 0 circle .5",
    "move -2 -2 repeat 4 0 1 repeat 2 .5 .5 repeat 4 1 0 box .5 .5",
    "move -2 0 scale .25 .25 rotate 20 repeat 7 2.75 0 (circle 1 move -.25 -1 scale 1 -1 box .5 2.5 move 0 -1.5 repeat 2 0 -1.75 (move -.25 0 rotate -45 scale 1 -1 box .5 2 move .25 0 rotate 45 scale -1 -1 box .5 2 ))",
    "define CRUZ (move -.5 -.25 box 1 .5 move -.25 -.5 box .5 1 ) move 1 1 CRUZ move -1 -1 rotate 45 CRUZ",
    "define scale (move -.5 -.25 scale 1 .5 move -.25 -.5 scale .5 1 ) move 1 1 scale move -1 -1 rotate 45 scale"
    ]



i = 0
for s in l:
    pr = (grafico + stringEnd).parseString(s.lower())

    print "BLAH"
    print pr
    tr = pr_a_string(pr)

    guardar_traduccion(tr, i)

    i = i + 1



