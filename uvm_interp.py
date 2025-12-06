interp_clean = r''

import argparse

OP_LOAD_CONST = 35
OP_READ = 32
OP_WRITE = 17
OP_MIN = 58

def mask(n):
    return (1<<n)-1

def decode_command(data: bytes, offset: int):
    rem = len(data) - offset
    if rem < 4:
        raise EOFError("Incomplete command")

    first4 = int.from_bytes(data[offset:offset+4],'little')
    opcode = first4 & mask(6)

    if opcode == OP_WRITE:
        if rem < 4: raise EOFError
        full = first4
        return {
            'op':'write',
            'A': full & mask(6),
            'B': (full>>6)&mask(7),
            'C': (full>>13)&mask(7),
            'D': (full>>20)&mask(7)
        }, 4

    elif opcode == OP_LOAD_CONST:
        if rem < 5: raise EOFError
        full = int.from_bytes(data[offset:offset+5],'little')
        return {
            'op':'load_const',
            'A': full & mask(6),
            'B': (full>>6)&mask(7),
            'C': (full>>13)&mask(26)
        }, 5

    elif opcode == OP_READ:
        if rem < 5: raise EOFError
        full = int.from_bytes(data[offset:offset+5],'little')
        return {
            'op':'read',
            'A': full & mask(6),
            'B': (full>>6)&mask(7),
            'C': (full>>13)&mask(21)
        }, 5

    elif opcode == OP_MIN:
        if rem < 6: raise EOFError
        full = int.from_bytes(data[offset:offset+6],'little')
        return {
            'op':'min',
            'A': full & mask(6),
            'B': (full>>6)&mask(7),
            'C': (full>>13)&mask(7),
            'D': (full>>20)&mask(21)
        }, 6

    else:
        raise ValueError(f"Unknown opcode {opcode}")

def execute(bytecode: bytes, mem_size: int = 4096):
    memory = [0]*mem_size
    pc = 0
    while pc < len(bytecode):
        cmd, size = decode_command(bytecode, pc)

        if cmd['op'] == 'load_const':
            memory[cmd['B']] = cmd['C']

        elif cmd['op'] == 'read':
            memory[cmd['B']] = memory[cmd['C']]

        elif cmd['op'] == 'write':
            addr = cmd['C'] + cmd['D']
            memory[addr] = memory[cmd['B']]

        elif cmd['op'] == 'min':
            val1 = memory[cmd['C']]
            val2 = memory[cmd['D']]
            memory[cmd['B']] = val1 if val1 < val2 else val2

        pc += size

    return memory

def parse_range(rng: str):
    a,b = rng.split('-')
    return int(a), int(b)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', required=True)
    parser.add_argument('-o','--output', required=True)
    parser.add_argument('-r','--range', required=True)
    args = parser.parse_args()

    with open(args.input,'rb') as f:
        data = f.read()

    memory = execute(data)

    start,end = parse_range(args.range)
    with open(args.output,'w') as out:
        out.write("addr,value\n")
        for i in range(start, end+1):
            out.write(f"{i},{memory[i]}\n")

    print("Dump written to", args.output)

if __name__ == "__main__":
    main()
