# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>)

#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VENTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

MONEDAS = (
    {'country': 'Colombia', 'currency': 'COP', 'singular': 'PESO COLOMBIANO',
     'plural': 'PESOS COLOMBIANOS', 'symbol': '$'},
    {'country': 'Estados Unidos', 'currency': 'USD', 'singular': 'DÓLAR',
     'plural': 'DÓLARES', 'symbol': 'US$'},
    {'country': 'Europa', 'currency': 'EUR', 'singular': 'EURO',
     'plural': 'EUROS', 'symbol': '€'},
    {'country': 'México', 'currency': 'MXN', 'singular': 'PESO MEXICANO',
     'plural': 'PESOS MEXICANOS', 'symbol': '$'},
    {'country': 'Perú', 'currency': 'PEN', 'singular': 'NUEVO SOL',
     'plural': 'NUEVOS SOLES', 'symbol': 'S/.'},
    {'country': 'Reino Unido', 'currency': 'GBP', 'singular': 'LIBRA',
     'plural': 'LIBRAS', 'symbol': '£'},
    {'country': 'Rep Dom', 'currency': 'DOP', 'singular': 'peso',
     'plural': 'pesos', 'symbol': 'RD$'}
)
# Para definir la moneda me estoy basando en los código que establece el
# ISO 4217

# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas
# sin importar el país

# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor
# para la clave.


def to_word(number, mi_moneda=None):
    """Converts a number into string representation"""
    converted = ''

    if not (0 < number < 999999999):
        return 'No es posible convertir el numero a letras'

    if "." in str(number):
        number = "{:.2f}".format(number)
        number, decimal = str(number).split(".")
    else:
        number = str(number)
        decimal = "00"

    number_str = str(number).zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if(millones):
        if(millones == '001'):
            converted += 'UN MILLON '
        elif(int(millones) > 0):
            converted += '%sMILLONES ' % __convert_group(millones)

    if(miles):
        if(miles == '001'):
            converted += 'MIL '
        elif(int(miles) > 0):
            converted += '%sMIL ' % __convert_group(miles)

    if(cientos):
        if(cientos == '001'):
            converted += 'UN '
        elif(int(cientos) > 0):
            converted += '%s' % __convert_group(cientos)

    # converted += moneda

    if decimal:
        decimal = "con %s%s" % (decimal, "/100")
        converted += decimal

    converted = "%s" % (converted.lower().capitalize())
    return converted.upper()


def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if(n == '100'):
        output = "CIEN "
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output
