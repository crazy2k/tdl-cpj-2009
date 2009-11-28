from pyparsing import *

nombre = Word(alphanums)
# natural contempla tambien el 0
natural = Word(nums)
realpositivo = Combine(natural + Optional(Combine("." + Word(nums)))) | Combine("." + Word(nums))
real = realpositivo | Combine(Literal("-") + realpositivo)

expresion = Forward()
grafico = Group(OneOrMore(Group(expresion))) | nombre

funcion = Literal("circle") + realpositivo | \
    Literal("box") + realpositivo + realpositivo | \
    Literal("move") + real + real + grafico | \
    Literal("scale") + real + real + grafico | \
    Literal("rotate") + real + grafico | \
    Literal("repeat") + natural + real + real + grafico | \
    Literal("define") + nombre + grafico

expresion << (funcion | \
    Literal("(").suppress() + funcion + Literal(")").suppress() | \
    nombre)
    #(grafico + grafico) | \
    #(Literal("(") + expresion + Literal(")")) | \


l = ["circle .5 box 1 1",
    "circle .5 move 1.5 0 box 1 1",
    "circle .5 move -1.5 0 rotate 45 box 1 1",
    "rotate 45 (scale 1 2 circle .5 move -2 -.5 box 1 1)"
    ]

for exp in l:
    print (OneOrMore(Group(expresion)) + stringEnd).parseString(exp)

