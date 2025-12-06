import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import traceback
import sys
import os
import uvm_asm
import inspect


try:
    from uvm_asm import assemble_text as asm_assemble_text
except Exception:
    asm_assemble_text = None

try:
    from uvm_interp import execute as interp_execute
except Exception:
    interp_execute = None


class UVMGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UVM — Assembler & Interpreter (GUI)")
        self.geometry("1000x700")
        self.create_widgets()

        # last assembled results
        self.bytecode = None
        self.IR = None
        self.memory = None
        self.binary_path = None

    def create_widgets(self):
        # top frame: editor + controls
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # left: assembler editor
        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl_prog = ttk.Label(left, text="Assembler program (algebraic syntax):")
        lbl_prog.pack(anchor="w")

        self.text_prog = tk.Text(left, wrap="none", height=25)
        self.text_prog.pack(fill=tk.BOTH, expand=True)

        # horizontal and vertical scrollbars for editor
        hscroll = ttk.Scrollbar(left, orient="horizontal", command=self.text_prog.xview)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        vscroll = ttk.Scrollbar(left, orient="vertical", command=self.text_prog.yview)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_prog.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)

        # fill with a demo program template
        self.text_prog.insert("1.0", self.default_demo_program())

        # right: controls + output
        right = ttk.Frame(top, width=380)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        # controls
        controls = ttk.LabelFrame(right, text="Controls")
        controls.pack(fill=tk.X, padx=4, pady=4)

        self.btn_assemble = ttk.Button(controls, text="Assemble & Run", command=self.on_assemble_run)
        self.btn_assemble.pack(fill=tk.X, padx=4, pady=4)

        self.btn_save_bin = ttk.Button(controls, text="Save last binary...", command=self.on_save_binary)
        self.btn_save_bin.pack(fill=tk.X, padx=4, pady=2)

        self.btn_save_dump = ttk.Button(controls, text="Save memory dump CSV...", command=self.on_save_dump)
        self.btn_save_dump.pack(fill=tk.X, padx=4, pady=2)

        # dump range entry
        frm_range = ttk.Frame(controls)
        frm_range.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(frm_range, text="Dump range (start-end):").pack(side=tk.LEFT)
        self.ent_range = ttk.Entry(frm_range, width=12)
        self.ent_range.pack(side=tk.LEFT, padx=4)
        self.ent_range.insert(0, "0-127")

        # memory table
        mem_frame = ttk.LabelFrame(right, text="Memory dump (addr,value)")
        mem_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=6)

        columns = ("addr", "value")
        self.tree = ttk.Treeview(mem_frame, columns=columns, show="headings", selectmode="none", height=30)
        self.tree.heading("addr", text="addr")
        self.tree.heading("value", text="value")
        self.tree.column("addr", width=80, anchor="center")
        self.tree.column("value", width=120, anchor="e")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # scrollbar for tree
        tree_scroll = ttk.Scrollbar(mem_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # bottom: bytecode hex and IR
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=6)

        lbl_bytecode = ttk.Label(bottom, text="Bytecode (hex):")
        lbl_bytecode.pack(anchor="w")
        self.txt_bytecode = tk.Text(bottom, height=4, wrap="none")
        self.txt_bytecode.pack(fill=tk.X, expand=True)

        lbl_ir = ttk.Label(bottom, text="IR (first lines):")
        lbl_ir.pack(anchor="w")
        self.txt_ir = tk.Text(bottom, height=6, wrap="none")
        self.txt_ir.pack(fill=tk.X, expand=True)

        # status bar
        self.status = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # menu
        self.create_menu()

    def default_demo_program(self):
        return (
            "# Example: small test program\n"
            "load_const 81 368\n"
            "read_value 13 48\n"
            "write_value 6 127 15\n"
            "min 92 23 628\n"
        )

    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", command=self.on_open_file)
        filemenu.add_command(label="Save program as...", command=self.on_save_program)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.on_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)

    def on_about(self):
        messagebox.showinfo("About", "UVM GUI\nAssembler + Interpreter frontend\nVariant 24\nAuthor: Generated")

    def on_open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files","*.txt;*.asm;*.s;*.uasm"),("All files","*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
        self.text_prog.delete("1.0", tk.END)
        self.text_prog.insert("1.0", txt)
        self.status.config(text=f"Loaded {os.path.basename(path)}")

    def on_save_program(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text_prog.get("1.0", tk.END))
        self.status.config(text=f"Saved {os.path.basename(path)}")

    def on_assemble_run(self):
        # Disable button while running
        self.btn_assemble.config(state=tk.DISABLED)
        try:
            prog_text = self.text_prog.get("1.0", tk.END)
            if asm_assemble_text is None:
                raise ImportError("Assembler function `assemble_text` not found. Make sure uvm24_asm.py is in the same folder.")
            if interp_execute is None:
                raise ImportError("Interpreter function `execute` not found. Make sure uvm24_interp.py is in the same folder.")

            # assemble
            bytecode, IR = asm_assemble_text(prog_text)
            self.bytecode = bytecode
            self.IR = IR

            # show bytecode hex
            # === Красивый вывод байткода в формате 0xNN, как в PDF ===
            self.txt_bytecode.delete("1.0", tk.END)

            # Построчно по 16 байт
            bytes_per_row = 16
            lines = []
            for i in range(0, len(bytecode), bytes_per_row):
                chunk = bytecode[i:i + bytes_per_row]
                row = ", ".join(f"0x{b:02X}" for b in chunk)
                lines.append(row)

            pretty_hex = "\n".join(lines)
            self.txt_bytecode.insert("1.0", pretty_hex)

            # show IR (first 50 lines)
            self.txt_ir.delete("1.0", tk.END)
            ir_text = "\n".join(str(x) for x in IR[:200])
            self.txt_ir.insert("1.0", ir_text)

            # run interpreter
            memory = interp_execute(bytecode, mem_size=4096)
            self.memory = memory

            # parse dump range
            rng = self.ent_range.get().strip()
            try:
                s,e = (int(x) for x in rng.split("-", 1))
            except Exception:
                s,e = 0, 127

            # populate treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            for addr in range(s, e+1):
                val = memory[addr] if addr < len(memory) else 0
                self.tree.insert("", "end", values=(addr, val))

            self.status.config(text=f"Assembled {len(IR)} instructions; memory size {len(memory)}")
            self.binary_path = None  # assembled but not saved
        except Exception as ex:
            tb = traceback.format_exc()
            messagebox.showerror("Error", f"Exception:\n{ex}\n\nTraceback:\n{tb}")
            self.status.config(text="Error")
        finally:
            self.btn_assemble.config(state=tk.NORMAL)

    def on_save_binary(self):
        if self.bytecode is None:
            messagebox.showinfo("No binary", "Nothing assembled yet. Press 'Assemble & Run' first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("Binary","*.bin"),("All files","*.*")])
        if not path:
            return
        with open(path, "wb") as f:
            f.write(self.bytecode)
        self.binary_path = path
        self.status.config(text=f"Saved binary: {os.path.basename(path)}")

    def on_save_dump(self):
        if self.memory is None:
            messagebox.showinfo("No dump", "No memory dump available. Press 'Assemble & Run' first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv"),("All files","*.*")])
        if not path:
            return
        # determine range to save
        rng = self.ent_range.get().strip()
        try:
            s,e = (int(x) for x in rng.split("-", 1))
        except Exception:
            s,e = 0, min(127, len(self.memory)-1)

        with open(path, "w", encoding="utf-8") as f:
            f.write("addr,value\n")
            for addr in range(s, e+1):
                val = self.memory[addr] if addr < len(self.memory) else 0
                f.write(f"{addr},{val}\n")
        self.status.config(text=f"Saved dump: {os.path.basename(path)}")


if __name__ == "__main__":
    app = UVMGuiApp()
    app.mainloop()
