"""A standalone scientific calculator built with Python's standard library."""

from __future__ import annotations

import ast
import math
import operator
import tkinter as tk
from tkinter import ttk


class MathError(Exception):
    """An expression is invalid or outside the calculator's supported domain."""


class Calculator:
    """Evaluate a deliberately small, safe subset of Python math syntax."""

    FUNCTIONS = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
        "sqrt": math.sqrt, "cbrt": math.cbrt, "abs": abs,
        "ln": math.log, "log": math.log10, "log10": math.log10,
        "log2": math.log2, "exp": math.exp, "floor": math.floor,
        "ceil": math.ceil, "factorial": math.factorial,
        "degrees": math.degrees, "radians": math.radians,
        "gamma": math.gamma, "lgamma": math.lgamma,
    }
    BINARY = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def __init__(self):
        self.angle_mode = "DEG"
        self.ans = 0

    def evaluate(self, expression: str):
        expression = expression.strip().replace("×", "*").replace("÷", "/").replace("−", "-")
        if not expression:
            raise MathError("Enter an expression")
        expression = expression.replace("π", "pi").replace("√", "sqrt")
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._node(tree.body)
            if isinstance(result, complex):
                return result
            if not math.isfinite(result):
                raise MathError("Result is outside the calculator's range")
            self.ans = result
            return result
        except MathError:
            raise
        except ZeroDivisionError as exc:
            raise MathError("Cannot divide by zero") from exc
        except OverflowError as exc:
            raise MathError("Result is too large") from exc
        except (ValueError, TypeError) as exc:
            raise MathError(str(exc) or "Invalid expression") from exc
        except SyntaxError as exc:
            raise MathError("Check the expression syntax") from exc

    def _node(self, node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            constants = {"pi": math.pi, "e": math.e, "tau": math.tau,
                         "ans": self.ans, "inf": math.inf}
            if node.id in constants:
                return constants[node.id]
            raise MathError(f"Unknown name: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in self.BINARY:
            left, right = self._node(node.left), self._node(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10000:
                raise MathError("Exponent is too large")
            return self.BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.UNARY:
            return self.UNARY[type(node.op)](self._node(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in self.FUNCTIONS or node.keywords:
                raise MathError(f"Unsupported function: {name}")
            args = [self._node(arg) for arg in node.args]
            if name in {"sin", "cos", "tan"} and self.angle_mode == "DEG":
                args[0] = math.radians(args[0])
            elif name in {"asin", "acos", "atan"} and self.angle_mode == "DEG":
                result = self.FUNCTIONS[name](*args)
                return math.degrees(result)
            if name == "factorial" and (len(args) != 1 or args[0] < 0 or int(args[0]) != args[0]):
                raise MathError("Factorial requires a non-negative integer")
            return self.FUNCTIONS[name](*args)
        raise MathError("Unsupported expression")


class ScientificCalculatorApp:
    THEMES = {
        "Dark": {
            "BG": "#080808", "PANEL": "#171717", "KEY": "#242424",
            "KEY_HOVER": "#3a3a3a", "TEXT": "#ffffff", "MUTED": "#bdbdbd",
            "ACCENT": "#ffffff", "GREEN": "#ffffff", "RED": "#d5d5d5",
            "BORDER": "#383838", "SELECT": "#505050", "FUNCTION": "#202020",
            "OPERATOR": "#303030", "DANGER": "#424242",
        },
        "Light": {
            "BG": "#ffffff", "PANEL": "#f2f2f2", "KEY": "#e5e5e5",
            "KEY_HOVER": "#d0d0d0", "TEXT": "#111111", "MUTED": "#555555",
            "ACCENT": "#111111", "GREEN": "#111111", "RED": "#333333",
            "BORDER": "#d0d0d0", "SELECT": "#c8c8c8", "FUNCTION": "#ebebeb",
            "OPERATOR": "#d9d9d9", "DANGER": "#dedede",
        },
    }

    def __init__(self, root):
        self.root = root
        self.calc = Calculator()
        self.memory = 0
        self.history = []
        self.just_evaluated = False
        self.expression = tk.StringVar()
        self.theme_name = tk.StringVar(value="Dark")
        self._apply_palette()
        root.title("Nova · Scientific Calculator")
        root.geometry("960x680")
        root.minsize(740, 570)
        root.configure(bg=self.BG)
        self._style()
        self._build()
        self._bind_keys()
        self.entry.focus_set()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=self.PANEL, background=self.KEY,
                        foreground=self.TEXT, arrowcolor=self.TEXT, borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", self.KEY)],
                  foreground=[("readonly", self.TEXT)],
                  selectbackground=[("readonly", self.KEY)],
                  selectforeground=[("readonly", self.TEXT)])

    def _apply_palette(self):
        for name, color in self.THEMES[self.theme_name.get()].items():
            setattr(self, name, color)

    def _build(self):
        shell = tk.Frame(self.root, bg=self.BG, padx=24, pady=18)
        shell.pack(fill="both", expand=True)
        header = tk.Frame(shell, bg=self.BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text="NOVA", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 19, "bold")).pack(side="left")
        tk.Label(header, text="SCIENTIFIC CALCULATOR", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=12, pady=(6, 0))
        self.theme_picker = ttk.Combobox(
            header, textvariable=self.theme_name, values=("Dark", "Light"),
            state="readonly", width=8, font=("Segoe UI", 10, "bold"),
        )
        self.theme_picker.pack(side="right", padx=(8, 0))
        self.theme_picker.bind("<<ComboboxSelected>>", self._change_theme)
        self.mode = tk.StringVar(value="DEG")
        mode = ttk.Combobox(header, textvariable=self.mode, values=("DEG", "RAD"),
                            state="readonly", width=7, font=("Segoe UI", 10, "bold"))
        mode.pack(side="right", padx=(8, 0))
        mode.bind("<<ComboboxSelected>>", lambda _e: setattr(self.calc, "angle_mode", self.mode.get()))
        self.angle_label = tk.Label(header, text="ANGLE", bg=self.BG, fg=self.MUTED,
                                    font=("Segoe UI", 8, "bold"))
        self.angle_label.pack(side="right")

        self.display = tk.Frame(shell, bg=self.PANEL, padx=20, pady=14,
                                highlightthickness=1, highlightbackground=self.BORDER)
        display = self.display
        display.pack(fill="x", pady=(0, 14))
        self.status = tk.Label(display, text="Ready  ·  π  ·  e  ·  ans", bg=self.PANEL,
                               fg=self.MUTED, anchor="e", font=("Segoe UI", 9))
        self.status.pack(fill="x")
        self.entry = tk.Entry(display, textvariable=self.expression, bg=self.PANEL,
                              fg=self.TEXT, insertbackground=self.ACCENT, relief="flat",
                              justify="right", font=("Segoe UI", 28), borderwidth=0)
        self.entry.pack(fill="x", ipady=7)
        self.entry.bind("<Return>", lambda _e: self.calculate())
        self.entry.bind("<KP_Enter>", lambda _e: self.calculate())

        body = tk.Frame(shell, bg=self.BG)
        body.pack(fill="both", expand=True)
        keys = tk.Frame(body, bg=self.BG)
        keys.pack(side="left", fill="both", expand=True, padx=(0, 16))
        self._make_buttons(keys)
        self.side_panel = tk.Frame(body, bg=self.PANEL, width=210, padx=14, pady=14)
        side = self.side_panel
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="HISTORY", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        self.history_box = tk.Listbox(side, bg=self.PANEL, fg=self.TEXT, selectbackground=self.SELECT,
                                      relief="flat", borderwidth=0, font=("Segoe UI", 10),
                                      activestyle="none", highlightthickness=0,
                                      selectforeground=self.TEXT)
        self.history_box.pack(fill="both", expand=True)
        self.history_box.bind("<Double-Button-1>", self._recall)
        self.history_box.bind("<Return>", self._recall)
        self._button(side, "Clear history", self.clear_history, kind="utility").pack(fill="x", pady=(10, 0))

    def _make_buttons(self, parent):
        layout = [
            [("sin", "fn"), ("cos", "fn"), ("tan", "fn"), ("asin", "fn"), ("acos", "fn"), ("atan", "fn")],
            [("sinh", "fn"), ("cosh", "fn"), ("tanh", "fn"), ("ln", "fn"), ("log", "fn"), ("log₂", "fn")],
            [("√", "fn"), ("∛", "fn"), ("x²", "fn"), ("xʸ", "fn"), ("1/x", "fn"), ("n!", "fn")],
            [("π", "fn"), ("e", "fn"), ("(", "fn"), (")", "fn"), ("⌫", "utility"), ("AC", "danger")],
            [("7", "num"), ("8", "num"), ("9", "num"), ("÷", "op"), ("%", "op"), ("MR", "utility")],
            [("4", "num"), ("5", "num"), ("6", "num"), ("×", "op"), ("−", "op"), ("M+", "utility")],
            [("1", "num"), ("2", "num"), ("3", "num"), ("+", "op"), ("Ans", "utility"), ("M−", "utility")],
            [("±", "utility"), ("0", "num"), (".", "num"), ("=", "equals"), ("exp", "fn"), ("MR", "utility")],
        ]
        for r, row in enumerate(layout):
            parent.grid_rowconfigure(r, weight=1, uniform="row")
            for c, (label, kind) in enumerate(row):
                parent.grid_columnconfigure(c, weight=1, uniform="col")
                self._button(parent, label, lambda value=label: self.press(value), kind).grid(
                    row=r, column=c, sticky="nsew", padx=4, pady=4)

    def _button(self, parent, label, command, kind="num"):
        colors = {"num": (self.KEY, self.TEXT), "fn": (self.FUNCTION, self.TEXT),
                  "op": (self.OPERATOR, self.TEXT), "utility": (self.FUNCTION, self.MUTED),
                  "danger": (self.DANGER, self.TEXT), "equals": (self.ACCENT, self.BG)}
        bg, fg = colors[kind]
        button = tk.Button(parent, text=label, command=command, bg=bg, fg=fg,
                           activebackground=self.KEY_HOVER, activeforeground=self.TEXT,
                           relief="flat", bd=0, cursor="hand2",
                           font=("Segoe UI", 10, "bold" if kind in ("op", "equals", "danger") else "normal"))
        button._calculator_kind = kind
        button._calculator_bg = bg
        button.bind("<Enter>", lambda _e: button.configure(bg=self.KEY_HOVER) if kind != "equals" else None)
        button.bind("<Leave>", lambda _e: button.configure(bg=button._calculator_bg))
        return button

    def _change_theme(self, _event=None):
        self._apply_palette()
        self.root.configure(bg=self.BG)
        self._style()
        self._recolor_widget_tree(self.root)

    def _recolor_widget_tree(self, widget):
        """Update every existing widget so theme changes apply immediately."""
        if isinstance(widget, tk.Entry):
            widget.configure(bg=self.PANEL, fg=self.TEXT, insertbackground=self.ACCENT)
        elif isinstance(widget, tk.Listbox):
            widget.configure(bg=self.PANEL, fg=self.TEXT, selectbackground=self.SELECT,
                             selectforeground=self.TEXT)
        elif isinstance(widget, tk.Button):
            kind = getattr(widget, "_calculator_kind", "num")
            colors = {"num": (self.KEY, self.TEXT), "fn": (self.FUNCTION, self.TEXT),
                      "op": (self.OPERATOR, self.TEXT), "utility": (self.FUNCTION, self.MUTED),
                      "danger": (self.DANGER, self.TEXT), "equals": (self.ACCENT, self.BG)}
            bg, fg = colors[kind]
            widget.configure(bg=bg, fg=fg, activebackground=self.KEY_HOVER,
                             activeforeground=self.TEXT)
            widget._calculator_bg = bg
        elif isinstance(widget, (tk.Frame, tk.Label)):
            if widget is self.root:
                widget.configure(bg=self.BG)
            elif widget is getattr(self, "display", None) or widget is getattr(self, "side_panel", None):
                widget.configure(bg=self.PANEL)
            else:
                widget.configure(bg=self.BG)
            if widget is getattr(self, "display", None):
                widget.configure(highlightbackground=self.BORDER)
            if isinstance(widget, tk.Label):
                widget.configure(fg=self.MUTED if widget in (self.status, self.angle_label) or
                                 widget.cget("text") == "HISTORY" or
                                 widget.cget("text") == "SCIENTIFIC CALCULATOR" else self.TEXT)
        for child in widget.winfo_children():
            self._recolor_widget_tree(child)

    def _bind_keys(self):
        self.root.bind("<Escape>", lambda _e: self.press("AC"))
        self.root.bind("<Control-BackSpace>", lambda _e: self.press("AC"))

    def press(self, key):
        if key == "AC":
            self.expression.set("")
            self.status.configure(text="Ready  ·  π  ·  e  ·  ans", fg=self.MUTED)
            self.just_evaluated = False
            return
        if key == "⌫":
            self.expression.set(self.expression.get()[:-1])
            return
        if key in ("M+", "M−", "MR"):
            if key == "MR":
                self._insert(str(self.memory))
            else:
                try:
                    value = self.calc.evaluate(self.expression.get())
                    self.memory += value if key == "M+" else -value
                    self.status.configure(text=f"Memory: {self._format(self.memory)}", fg=self.GREEN)
                except (MathError, TypeError):
                    self.status.configure(text="Enter a valid expression before using memory", fg=self.RED)
            return
        if key == "±":
            text = self.expression.get().strip()
            if text:
                self.expression.set(f"-({text})")
            return
        if key == "=":
            self.calculate()
            return
        insert = {"×": "×", "÷": "÷", "−": "−", "√": "sqrt(", "∛": "cbrt(",
                  "x²": "^2", "xʸ": "^", "1/x": "1/(", "n!": "factorial(",
                  "log₂": "log2(", "π": "π", "Ans": "ans", "exp": "exp("}.get(key, key)
        if key in Calculator.FUNCTIONS and key not in ("exp",):
            insert = key + "("
        self._insert(insert)

    def _insert(self, value):
        if self.just_evaluated and value not in ("×", "÷", "+", "−", "^", "%"):
            self.expression.set("")
        self.just_evaluated = False
        self.entry.insert(tk.INSERT, value)
        self.entry.focus_set()

    def calculate(self):
        source = self.expression.get().strip()
        if not source:
            return
        normalized = source.replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**")
        try:
            result = self.calc.evaluate(normalized)
            rendered = self._format(result)
            self.history.insert(0, (source, rendered))
            self.history_box.insert(0, f"{source}\n= {rendered}")
            if len(self.history) > 100:
                self.history.pop()
                self.history_box.delete(100)
            self.expression.set(rendered)
            self.status.configure(text=f"Result  ·  {self.calc.angle_mode}  ·  ans = {rendered}", fg=self.GREEN)
            self.just_evaluated = True
        except (MathError, TypeError, IndexError) as exc:
            self.status.configure(text=str(exc), fg=self.RED)
            self.root.bell()

    @staticmethod
    def _format(value):
        if isinstance(value, complex):
            return f"{value.real:.12g}{value.imag:+.12g}i"
        if isinstance(value, float):
            if value == 0:
                return "0"
            return f"{value:.12g}"
        return str(value)

    def _recall(self, _event=None):
        selection = self.history_box.curselection()
        if selection:
            source = self.history[selection[0]][0]
            self.expression.set(source)
            self.entry.icursor(tk.END)

    def clear_history(self):
        self.history.clear()
        self.history_box.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    ScientificCalculatorApp(root)
    root.mainloop()
