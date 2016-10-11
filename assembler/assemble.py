#!/usr/bin/env python3
"""
Compile assembler program to Logisim ram file.
"""

_usage = """
Usage
  $python3 assemble.py FILE [OUTPUT_FILE]
"""
from pprint import pprint
import re
import sys

from ply import lex


RAM_FILE_HEADER = 'v2.0 raw'

tokens = (
    "ADDR_SET",
    "INST",
    "REGISTER",
    "ADDR_EXPR",
    "ADDR_VAR",
    "HEX_NUM",
    "COMMA",
    "NEWLINE",
    "WHITESPACE",
)

t_COMMA = r','

def t_INST(t):
    'sto|lod|add|sub|adc|hlt|jmp|jz|jnz|jc|jnc'
    return t

def t_ADDR_SET(t):
    r'[a-z][a-z0-9]*:'
    return t

def t_ADDR_EXPR(t):
    r'\[[^\[]+\]'
    return t

def t_HEX_NUM(t):
    r'[0-9a-f]{1,2}h'
    t.value = t.value[:-1]
    return t

def t_REGISTER(t):
    r'a'
    return t

def t_ADDR_VAR(t):
    r'[a-z][a-z0-9]*'
    t.value = '[' + t.value + ']'
    return t

def t_COMMENT(t):
    r';.*'
    pass  # Discard comments

def t_NEWLINE(t):
    r'\n+'
    return t

def t_WHITESPACE(t):
    r'\s+'
    pass

def t_error(t):
    raise TypeError('Unknown text: "%s"' % t.value)


def format_addr(addr):
    hexval = hex(addr)[2:]
    if len(hexval) > 4:
        raise ValueError('Addresses cannot be > 16 bits')
    hexval = '0' * (4 - len(hexval)) + hexval
    return [hexval[0:2], hexval[2:4]]


opcodes = {
    'lod': '10',
    'sto': '11',
    'add': '20',
    'sub': '21',
    'adc': '22',
    'sbb': '23',
    'jmp': '30',
    'jz': '31',
    'jc': '32',
    'jnz': '33',
    'jnc': '34',
    'hlt': 'ff',
}


def parse_inst(line):
    bytes_ = []
    written = 0
    for tok in line:
        if tok.type == 'INST':
            bytes_.append(opcodes[tok.value])
            written += 1
            if tok.value == 'hlt':
                bytes_ += ['00', '00']
                return bytes_, 3
        elif tok.type == 'HEX_NUM':
            bytes_.append(tok.value)
            written += 1
        elif tok.type in ('ADDR_VAR', 'ADDR_EXPR'):
            bytes_.append(tok.value)
            written += 2
        else:
            continue
    if written != 3:
        raise ValueError('Syntax error at %s' % repr(line))
    return bytes_, 3


def parse_const(line):
    bytes_ = []
    exp_type = 'HEX_NUM'
    for tok in line:
        if not tok.type == exp_type:
            raise ValueError('Syntax error at %s' % repr(line))
        if tok.type == 'HEX_NUM':
            bytes_.append(tok.value)
            exp_type = 'COMMA'
        elif tok.type == 'COMMA':
            exp_type = 'HEX_NUM'
    return bytes_, len(bytes_)


def format_bytes_to_ram(bytes_):
    lines = [RAM_FILE_HEADER]
    while bytes_:
        line = bytes_[:8]
        bytes_ = bytes_[8:]
        lines.append(' '.join(line))
    return '\n'.join(lines) + '\n'


def parse():
    var_map = {}
    tokens = []
    line = []
    bytes_ = []
    addr_ct = 0
    for tok in iter(lex.token, None):
        if tok.type != "NEWLINE":
            line.append(tok)
        else:
            tokens.append(line)
            line = []
    for line in tokens:
        if not line:
            continue
        if line[0].type == 'ADDR_SET':
            var_map[line[0].value.strip(':')] = addr_ct
            if line[1].type == 'HEX_NUM':
                bs, ct = parse_const(line[1:])
                addr_ct += ct
                bytes_ += bs
            elif line[1].type == 'INST':
                bs, ct = parse_inst(line[1:])
                addr_ct += ct
                bytes_ += bs
        elif line[0].type == 'INST':
            bs, ct = parse_inst(line)
            addr_ct += ct
            bytes_ += bs
        else:
            raise ValueError('Invalid syntax at %s' % repr(tok))
    for i, b in enumerate(bytes_):
        # Replace vars by addresses
        if b[0] == '[':
            bytes_[i:i+1] = format_addr(eval(b.strip('[]'), var_map))
    return bytes_


def main(o_in, o_out):
    lex.lex()
    with open(o_in, 'r') as f:
        lex.input(f.read())
    bytes_ = parse()
    with open(o_out, 'w') as f:
        f.write(format_bytes_to_ram(bytes_))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(_usage)
        sys.exit(1)
    elif len(sys.argv) == 2:
        sys.argv.append('out.ram')
    main(sys.argv[1], sys.argv[2])
    sys.exit(0)
