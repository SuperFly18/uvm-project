# app.py - Flask веб-приложение для UVM
from flask import Flask, render_template, request, jsonify, send_file, Response
import io
import traceback
import os
import uvm_asm

# Проверяем импорт модулей
try:
    from uvm_asm import assemble_text as asm_assemble_text

    ASSEMBLER_AVAILABLE = True
except Exception:
    ASSEMBLER_AVAILABLE = False
    asm_assemble_text = None

try:
    from uvm_interp import execute as interp_execute

    INTERPRETER_AVAILABLE = True
except Exception:
    INTERPRETER_AVAILABLE = False
    interp_execute = None

app = Flask(__name__)


# Состояние сессии (в реальном приложении используйте сессии или базу данных)
class SessionState:
    def __init__(self):
        self.bytecode = None
        self.IR = None
        self.memory = None
        self.program_text = ""
        self.dump_range = "0-127"


# Простая база данных сессий (для демо, в продакшене используйте Redis и т.д.)
sessions = {}


def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = SessionState()
    return sessions[session_id]


def default_demo_program():
    return """# Example: small test program
load_const 81 368
read_value 13 48
write_value 6 127 15
min 92 23 628"""


@app.route('/')
def index():
    return render_template('index.html',
                           assembler_available=ASSEMBLER_AVAILABLE,
                           interpreter_available=INTERPRETER_AVAILABLE)


@app.route('/api/assemble', methods=['POST'])
def api_assemble():
    session_id = request.json.get('session_id', 'default')
    session = get_session(session_id)

    program_text = request.json.get('program', '').strip()
    dump_range = request.json.get('dump_range', '0-127')

    session.program_text = program_text
    session.dump_range = dump_range

    if not ASSEMBLER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Assembler module not found. Make sure uvm_asm.py is available.'
        })

    if not INTERPRETER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Interpreter module not found. Make sure uvm_interp.py is available.'
        })

    try:
        # Ассемблирование
        bytecode, IR = asm_assemble_text(program_text)
        session.bytecode = bytecode
        session.IR = IR

        # Преобразование байткода в красивый hex
        bytes_per_row = 16
        hex_lines = []
        for i in range(0, len(bytecode), bytes_per_row):
            chunk = bytecode[i:i + bytes_per_row]
            row = ", ".join(f"0x{b:02X}" for b in chunk)
            hex_lines.append(row)
        pretty_hex = "\n".join(hex_lines)

        # Запуск интерпретатора
        memory = interp_execute(bytecode, mem_size=4096)
        session.memory = memory

        # Парсинг диапазона дампа
        try:
            s, e = map(int, dump_range.split("-", 1))
        except Exception:
            s, e = 0, 127

        # Подготовка дампа памяти
        memory_dump = []
        for addr in range(s, min(e + 1, len(memory))):
            val = memory[addr] if addr < len(memory) else 0
            memory_dump.append({
                'addr': addr,
                'value': val
            })

        # Подготовка IR (первые 200 строк)
        ir_preview = "\n".join(str(x) for x in IR[:200])

        return jsonify({
            'success': True,
            'bytecode_hex': pretty_hex,
            'ir_preview': ir_preview,
            'memory_dump': memory_dump,
            'stats': {
                'instructions': len(IR),
                'memory_size': len(memory),
                'bytecode_size': len(bytecode)
            }
        })

    except Exception as ex:
        error_trace = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(ex),
            'traceback': error_trace
        })


@app.route('/api/save_binary', methods=['POST'])
def api_save_binary():
    session_id = request.json.get('session_id', 'default')
    session = get_session(session_id)

    if session.bytecode is None:
        return jsonify({
            'success': False,
            'error': 'No bytecode available. Assemble a program first.'
        })

    # Создаем файл в памяти
    mem_file = io.BytesIO(session.bytecode)
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name='uvm_program.bin'
    )


@app.route('/api/save_dump', methods=['POST'])
def api_save_dump():
    session_id = request.json.get('session_id', 'default')
    session = get_session(session_id)

    if session.memory is None:
        return jsonify({
            'success': False,
            'error': 'No memory dump available. Assemble and run a program first.'
        })

    # Парсинг диапазона
    try:
        s, e = map(int, session.dump_range.split("-", 1))
    except Exception:
        s, e = 0, min(127, len(session.memory) - 1)

    # Создаем CSV в памяти
    output = io.StringIO()
    output.write("addr,value\n")
    for addr in range(s, min(e + 1, len(session.memory))):
        val = session.memory[addr] if addr < len(session.memory) else 0
        output.write(f"{addr},{val}\n")

    mem_file = io.BytesIO()
    mem_file.write(output.getvalue().encode('utf-8'))
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype='text/csv',
        as_attachment=True,
        download_name='uvm_memory_dump.csv'
    )


@app.route('/api/load_demo', methods=['GET'])
def api_load_demo():
    session_id = request.args.get('session_id', 'default')
    session = get_session(session_id)

    demo_program = default_demo_program()
    session.program_text = demo_program

    return jsonify({
        'success': True,
        'program': demo_program
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)