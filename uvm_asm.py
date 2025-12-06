asm_clean = r''

import argparse
from typing import List, Tuple

OP_LOAD_CONST = 35
OP_READ = 32
OP_WRITE = 17
OP_MIN = 58

def mask(n):
    return (1<<n)-1

def pack_load_const(B: int, C: int) -> bytes:
    A = OP_LOAD_CONST & mask(6)
    val = A | ((B & mask(7)) << 6) | ((C & mask(26)) << 13)
    return val.to_bytes(5, 'little')

def pack_read(B: int, C: int) -> bytes:
    A = OP_READ & mask(6)
    val = A | ((B & mask(7)) << 6) | ((C & mask(21)) << 13)
    return val.to_bytes(5, 'little')

def pack_write(B: int, C: int, D: int) -> bytes:
    A = OP_WRITE & mask(6)
    val = A | ((B & mask(7)) << 6) | ((C & mask(7)) << 13) | ((D & mask(7)) << 20)
    return val.to_bytes(4, 'little')

def pack_min(B: int, C: int, D: int) -> bytes:
    A = OP_MIN & mask(6)
    val = A | ((B & mask(7)) << 6) | ((C & mask(7)) << 13) | ((D & mask(21)) << 20)
    return val.to_bytes(6, 'little')

def parse_line(line: str):
    parts = line.strip().split()
    if not parts:
        return None
    instr = parts[0].lower()
    args = []
    for token in parts[1:]:
        if '=' in token:
            _, val = token.split('=',1)
            args.append(int(val.rstrip(',')))
        else:
            args.append(int(token.rstrip(',')))
    return (instr, args)

def assemble_text(text: str):
    bytecode = bytes()
    IR = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or s.startswith('//'):
            continue
        parsed = parse_line(s)
        if parsed is None:
            continue
        instr, args = parsed
        IR.append((instr, args))

        if instr == 'load_const':
            B,C = args
            bytecode += pack_load_const(B,C)
        elif instr == 'read_value':
            B,C = args
            bytecode += pack_read(B,C)
        elif instr == 'write_value':
            B,C,D = args
            bytecode += pack_write(B,C,D)
        elif instr == 'min':
            B,C,D = args
            bytecode += pack_min(B,C,D)
        else:
            raise ValueError("Unknown instruction: " + instr)
    return bytecode, IR

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', required=True)
    parser.add_argument('-o','--output', required=True)
    parser.add_argument('-t','--test', default='0')
    args = parser.parse_args()

    with open(args.input) as f:
        text = f.read()

    bytecode, IR = assemble_text(text)

    with open(args.output,'wb') as out:
        out.write(bytecode)

    if args.test == '1':
        print("IR:")
        for item in IR:
            print(item)
        print("bytecode hex:")
        print(" ".join(f"{b:02X}" for b in bytecode))

if __name__ == "__main__":
    main()