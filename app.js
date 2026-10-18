"use strict";

const FUNCTIONS = {
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  asin: Math.asin, acos: Math.acos, atan: Math.atan,
  sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh,
  asinh: Math.asinh, acosh: Math.acosh, atanh: Math.atanh,
  sqrt: Math.sqrt, cbrt: Math.cbrt, abs: Math.abs,
  ln: Math.log, log: Math.log10, log10: Math.log10, log2: Math.log2,
  exp: Math.exp, floor: Math.floor, ceil: Math.ceil,
  factorial: (n) => {
    if (!Number.isInteger(n) || n < 0 || n > 170) throw new Error("Factorial needs a whole number from 0 to 170");
    let result = 1;
    for (let i = 2; i <= n; i += 1) result *= i;
    return result;
  },
  degrees: (n) => n * (180 / Math.PI),
  radians: (n) => n * (Math.PI / 180),
  gamma: (n) => gamma(n),
  lgamma: (n) => Math.log(Math.abs(gamma(n))),
};

const GAMMA_COEFFICIENTS = [
  676.5203681218851, -1259.1392167224028, 771.3234287776531,
  -176.6150291621406, 12.507343278686905, -0.13857109526572012,
  9.984369578019572e-6, 1.5056327351493116e-7,
];

function gamma(z) {
  if (z <= 0 && Number.isInteger(z)) throw new Error("Gamma is undefined for non-positive integers");
  if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
  let x = 0.9999999999998099;
  z -= 1;
  GAMMA_COEFFICIENTS.forEach((coefficient, index) => { x += coefficient / (z + index + 1); });
  const t = z + GAMMA_COEFFICIENTS.length - 0.5;
  return Math.sqrt(2 * Math.PI) * (t ** (z + 0.5)) * Math.exp(-t) * x;
}

class ExpressionParser {
  constructor(source, angleMode, ans) {
    this.angleMode = angleMode;
    this.ans = ans;
    this.tokens = this._tokenize(source);
    this.position = 0;
  }

  _tokenize(source) {
    const raw = source.replaceAll("×", "*").replaceAll("÷", "/").replaceAll("−", "-")
      .replaceAll("π", "pi").replaceAll("√", "sqrt").replaceAll("^", "^")
      .match(/(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|\*\*|[^\s]/g) || [];
    const constants = new Set(["pi", "e", "tau", "ans"]);
    const isNumber = (token) => /^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(token);
    const tokens = [];
    let previous = null;
    for (const token of raw) {
      const previousCanEnd = previous === ")" || constants.has(previous) || (previous !== null && isNumber(previous));
      const tokenCanStart = token === "(" || constants.has(token) || isNumber(token) || token in FUNCTIONS;
      const knownFunctionCall = previous in FUNCTIONS && token === "(";
      if (previousCanEnd && tokenCanStart && !knownFunctionCall) tokens.push("*");
      tokens.push(token);
      previous = token;
    }
    return tokens;
  }

  peek() { return this.tokens[this.position]; }
  take() { return this.tokens[this.position++]; }

  parse() {
    const value = this._addition();
    if (this.position !== this.tokens.length) throw new Error(`Unexpected token: ${this.peek()}`);
    if (typeof value !== "number" || !Number.isFinite(value)) throw new Error("Result is outside the calculator's range");
    return value;
  }

  _addition() {
    let value = this._multiplication();
    while (this.peek() === "+" || this.peek() === "-") {
      const operator = this.take();
      const right = this._multiplication();
      value = operator === "+" ? value + right : value - right;
    }
    return value;
  }

  _multiplication() {
    let value = this._unary();
    while (["*", "/", "%"].includes(this.peek())) {
      const operator = this.take();
      const right = this._unary();
      if ((operator === "/" || operator === "%") && right === 0) throw new Error("Cannot divide by zero");
      if (operator === "*") value *= right;
      else if (operator === "/") value /= right;
      else value %= right;
    }
    return value;
  }

  _unary() {
    if (this.peek() === "+") { this.take(); return this._unary(); }
    if (this.peek() === "-") { this.take(); return -this._unary(); }
    return this._power();
  }

  _power() {
    const value = this._primary();
    if (this.peek() === "^" || this.peek() === "**") {
      this.take();
      const exponent = this._unary();
      if (Math.abs(exponent) > 10000) throw new Error("Exponent is too large");
      return value ** exponent;
    }
    return value;
  }

  _primary() {
    const token = this.take();
    if (token === undefined) throw new Error("Expression is incomplete");
    if (/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(token)) return Number(token);
    if (token === "(") {
      const value = this._addition();
      if (this.take() !== ")") throw new Error("Missing closing parenthesis");
      return value;
    }
    if (token in FUNCTIONS) {
      if (this.take() !== "(") throw new Error(`Add parentheses after ${token}`);
      const argument = this._addition();
      if (this.take() !== ")") throw new Error("Missing closing parenthesis");
      return this._call(token, argument);
    }
    const constants = { pi: Math.PI, e: Math.E, tau: 2 * Math.PI, ans: this.ans };
    if (Object.hasOwn(constants, token)) return constants[token];
    throw new Error(`Unknown name: ${token}`);
  }

  _call(name, value) {
    if (["sin", "cos", "tan"].includes(name) && this.angleMode === "DEG") value *= Math.PI / 180;
    const result = FUNCTIONS[name](value);
    if (["asin", "acos", "atan"].includes(name) && this.angleMode === "DEG") return result * 180 / Math.PI;
    return result;
  }
}

const expressionInput = document.querySelector("#expression");
const resultLine = document.querySelector("#result-line");
const statusLabel = document.querySelector("#status");
const historyList = document.querySelector("#history-list");
const angleSelect = document.querySelector("#angle-mode");
const memoryIndicator = document.querySelector("#memory-indicator");
let answer = 0;
let memory = 0;
let justCalculated = false;
let history = [];

function formatNumber(value) {
  if (Object.is(value, -0) || value === 0) return "0";
  return Number(value.toPrecision(12)).toString();
}

function calculate() {
  const source = expressionInput.value.trim();
  if (!source) return;
  try {
    const result = new ExpressionParser(source, angleSelect.value, answer).parse();
    answer = result;
    const rendered = formatNumber(result);
    resultLine.textContent = `= ${rendered}`;
    resultLine.classList.remove("error");
    statusLabel.textContent = `Result · ${angleSelect.value} · ans = ${rendered}`;
    addHistory(source, rendered);
    expressionInput.value = rendered;
    expressionInput.setSelectionRange(rendered.length, rendered.length);
    justCalculated = true;
  } catch (error) {
    resultLine.textContent = error.message || "Check the expression";
    resultLine.classList.add("error");
    statusLabel.textContent = "Could not calculate";
    justCalculated = false;
  }
}

function addHistory(source, result) {
  history.unshift({ source, result });
  history = history.slice(0, 50);
  historyList.replaceChildren(...history.map((item, index) => {
    const button = document.createElement("button");
    button.className = "history-item";
    button.type = "button";
    button.dataset.historyIndex = String(index);
    const expression = document.createElement("span");
    expression.className = "history-expression";
    expression.textContent = item.source;
    const value = document.createElement("span");
    value.className = "history-result";
    value.textContent = `= ${item.result}`;
    button.append(expression, value);
    return button;
  }));
}

function insertText(text) {
  const start = expressionInput.selectionStart ?? expressionInput.value.length;
  const end = expressionInput.selectionEnd ?? start;
  if (justCalculated && !["+", "−", "-", "×", "÷", "/", "%", "^"].includes(text)) {
    expressionInput.value = "";
    expressionInput.setSelectionRange(0, 0);
  }
  justCalculated = false;
  const currentStart = expressionInput.selectionStart ?? expressionInput.value.length;
  const currentEnd = expressionInput.selectionEnd ?? currentStart;
  expressionInput.setRangeText(text, currentStart, currentEnd, "end");
  expressionInput.focus();
  resultLine.textContent = "";
  resultLine.classList.remove("error");
  statusLabel.textContent = "Enter an expression";
}

function clearAll() {
  expressionInput.value = "";
  resultLine.textContent = "";
  resultLine.classList.remove("error");
  statusLabel.textContent = "Enter an expression";
  justCalculated = false;
  expressionInput.focus();
}

function updateMemoryIndicator() { memoryIndicator.hidden = memory === 0; }

document.querySelector("#keypad").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const { action, insert } = button.dataset;
  if (action === "equals") calculate();
  else if (action === "clear") clearAll();
  else if (action === "clear-entry") {
    expressionInput.value = "";
    resultLine.textContent = "";
    statusLabel.textContent = "Entry cleared";
  } else if (action === "backspace") {
    const start = expressionInput.selectionStart ?? expressionInput.value.length;
    const end = expressionInput.selectionEnd ?? start;
    if (start === end && start > 0) expressionInput.setRangeText("", start - 1, end, "end");
    else expressionInput.setRangeText("", start, end, "end");
    expressionInput.focus();
  } else if (action === "sign") {
    const value = expressionInput.value;
    if (value) expressionInput.value = `-(${value})`;
    expressionInput.focus();
  } else if (insert !== undefined) insertText(insert);
});

document.querySelector(".utility-row").addEventListener("click", (event) => {
  const key = event.target.closest("button")?.dataset.key;
  if (!key) return;
  if (key === "MC") memory = 0;
  else if (key === "MR") insertText(formatNumber(memory));
  else {
    try {
      const value = new ExpressionParser(expressionInput.value, angleSelect.value, answer).parse();
      if (key === "MS") memory = value;
      if (key === "M+") memory += value;
      if (key === "M-") memory -= value;
      statusLabel.textContent = `Memory: ${formatNumber(memory)}`;
    } catch {
      statusLabel.textContent = "Enter a valid expression first";
    }
  }
  updateMemoryIndicator();
});

historyList.addEventListener("click", (event) => {
  const item = event.target.closest("[data-history-index]");
  if (!item) return;
  expressionInput.value = history[Number(item.dataset.historyIndex)].source;
  expressionInput.focus();
  expressionInput.setSelectionRange(expressionInput.value.length, expressionInput.value.length);
  justCalculated = false;
});

document.querySelector("#clear-history").addEventListener("click", () => {
  history = [];
  const empty = document.createElement("div");
  empty.className = "empty-history";
  const symbol = document.createElement("span");
  symbol.className = "history-symbol";
  symbol.textContent = "↳";
  const copy = document.createElement("p");
  copy.append("Your calculations", document.createElement("br"), "will show up here.");
  empty.append(symbol, copy);
  historyList.replaceChildren(empty);
});

expressionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") { event.preventDefault(); calculate(); }
  if (event.key === "Escape") { event.preventDefault(); clearAll(); }
  if (event.key === "ArrowUp" && history.length) {
    event.preventDefault();
    expressionInput.value = history[0].source;
    expressionInput.setSelectionRange(expressionInput.value.length, expressionInput.value.length);
  }
});

document.querySelector("#theme-toggle").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("nova-theme", next);
  document.querySelector("#theme-label").textContent = next === "light" ? "Dark" : "Light";
  document.querySelector(".theme-icon").textContent = next === "light" ? "☾" : "☼";
  document.querySelector('meta[name="theme-color"]').content = next === "light" ? "#f5f5f5" : "#090909";
});

const savedTheme = localStorage.getItem("nova-theme");
if (savedTheme === "light") {
  document.documentElement.dataset.theme = "light";
  document.querySelector("#theme-label").textContent = "Dark";
  document.querySelector(".theme-icon").textContent = "☾";
  document.querySelector('meta[name="theme-color"]').content = "#f5f5f5";
}
