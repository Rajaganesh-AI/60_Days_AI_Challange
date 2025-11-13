import streamlit as st
import ast
import operator as op
import re
from typing import Tuple, List

# --- Safe evaluation helpers (adapted from original script) ---
_ALLOWED_BINOPS = {
    ast.Add: (op.add, "+"),
    ast.Sub: (op.sub, "-"),
    ast.Mult: (op.mul, "×"),
    ast.Div: (op.truediv, "÷"),
    ast.Pow: (op.pow, "**"),
    ast.Mod: (op.mod, "%"),
    ast.FloorDiv: (op.floordiv, "//"),
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: (lambda x: x, "+"),
    ast.USub: (lambda x: -x, "-")
}


class SafeEvalError(Exception):
    pass


def sanitize_text(s: str) -> str:
    s = s.strip()
    s = s.replace("×", "*").replace("✕", "*").replace("·", "*")
    s = s.replace("÷", "/").replace("−", "-").replace("—", "-")
    s = re.sub(r"^(what is|what's|whats|calculate|evaluate|compute)\s+", "", s, flags=re.IGNORECASE)
    s = s.strip()
    s = s.rstrip("?.")
    return s


def handle_percent_of(s: str) -> str:
    def repl_of(match):
        pct = match.group("pct")
        target = match.group("target")
        return f"(({pct})/100)*({target})"

    pattern_of = re.compile(
        r"(?P<pct>\d+(\.\d+)?)\s*%\s*(?:of)\s*(?P<target>\(?[0-9\.\-\+\*\/\s\(\)]+?\)?)",
        flags=re.IGNORECASE,
    )
    s = pattern_of.sub(repl_of, s)
    s = re.sub(r"(?P<p>\d+(\.\d+)?)\s*%", r"((\g<p>)/100)", s)
    return s


def sanitize_expression(user_input: str) -> str:
    s = sanitize_text(user_input)
    s = handle_percent_of(s)
    s = re.sub(r"\s+", " ", s)
    return s


def _ensure_allowed_node(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _ensure_allowed_node(node.body)

    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BINOPS:
            raise SafeEvalError(f"Operator {type(node.op).__name__} is not allowed.")
        _ensure_allowed_node(node.left)
        _ensure_allowed_node(node.right)
        return

    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in _ALLOWED_UNARYOPS:
            raise SafeEvalError(f"Unary operator {type(node.op).__name__} is not allowed.")
        _ensure_allowed_node(node.operand)
        return

    if isinstance(node, ast.Num):
        return

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return
        raise SafeEvalError("Only numeric constants are allowed.")

    if isinstance(node, ast.Call):
        raise SafeEvalError("Function calls are not allowed.")

    if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript, ast.Lambda, ast.List, ast.Dict, ast.Tuple)):
        raise SafeEvalError("Names, attributes, or data structures are not allowed.")

    for child in ast.iter_child_nodes(node):
        _ensure_allowed_node(child)


def safe_eval(expr: str) -> float:
    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise SafeEvalError("Syntax error in expression.") from e

    _ensure_allowed_node(parsed)

    def _eval(node: ast.AST):
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            func = _ALLOWED_BINOPS.get(op_type)
            if func is None:
                raise SafeEvalError(f"Operator {op_type.__name__} not supported.")
            try:
                return func[0](left, right)
            except ZeroDivisionError as e:
                raise ZeroDivisionError("Division by zero.") from e

        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            func = _ALLOWED_UNARYOPS.get(type(node.op))
            if func is None:
                raise SafeEvalError("Unary operator not supported.")
            return func[0](operand)

        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.Constant):
            return node.value

        raise SafeEvalError(f"Unsupported expression: {ast.dump(node)}")

    result = _eval(parsed)
    if isinstance(result, bool):
        raise SafeEvalError("Boolean values are not allowed.")
    return result


# --- Explanation generator (step-by-step) ---
def explain_evaluation(expr: str) -> List[str]:
    """
    Produce a human-friendly sequence of steps explaining how the expression was evaluated.

    This function parses and recursively evaluates the expression while recording each
    sub-operation in the order it is computed. It uses the same allowed operators as safe_eval.
    """
    sanitized = expr
    try:
        parsed = ast.parse(sanitized, mode="eval")
    except Exception:
        return ["Could not parse expression for explanation."]

    steps: List[str] = []

    def node_to_source(node: ast.AST) -> str:
        # Prefer ast.unparse when available for nicer source strings
        try:
            src = ast.unparse(node)
            # replace Python-style operators with display-friendly ones
            return src.replace("*", "×").replace("/", "÷").replace("**", "^")
        except Exception:
            return str(node)

    def _explain(node: ast.AST) -> Tuple[float, str]:
        # returns (numeric_value, source_string)
        if isinstance(node, ast.Expression):
            return _explain(node.body)

        if isinstance(node, ast.BinOp):
            lval, lsrc = _explain(node.left)
            rval, rsrc = _explain(node.right)
            op_type = type(node.op)
            op_entry = _ALLOWED_BINOPS.get(op_type)
            if op_entry is None:
                raise SafeEvalError(f"Operator {op_type.__name__} not supported for explanation.")
            func, symbol = op_entry
            try:
                value = func(lval, rval)
            except ZeroDivisionError:
                raise
            # create a readable left/right representation (use parentheses if the subexpr contains spaces)
            left_repr = lsrc if " " not in lsrc else f"({lsrc})"
            right_repr = rsrc if " " not in rsrc else f"({rsrc})"
            step = f"Compute {left_repr} {symbol} {right_repr} = {value}"
            steps.append(step)
            # return value and a short source string for parent steps
            return value, str(value)

        if isinstance(node, ast.UnaryOp):
            operand_val, operand_src = _explain(node.operand)
            func, symbol = _ALLOWED_UNARYOPS.get(type(node.op))
            value = func(operand_val)
            step = f"Apply unary {symbol}{operand_src} = {value}"
            steps.append(step)
            return value, str(value)

        if isinstance(node, ast.Num):
            return node.n, str(node.n)

        if isinstance(node, ast.Constant):
            return node.value, str(node.value)

        # fallback: try to get a source-like representation
        return 0, node_to_source(node)

    try:
        _explain(parsed)
    except ZeroDivisionError:
        return ["Division by zero occurred during explanation."]
    except SafeEvalError as e:
        return [f"Explanation not available: {e}"]
    except Exception:
        return ["Failed to generate explanation for this expression."]

    if not steps:
        # Expression is a single number
        try:
            # get the numeric value
            val = safe_eval(sanitized)
            return [f"Expression is a single number: {val}"]
        except Exception:
            return ["No steps generated."]

    return steps


def format_result(original_expr: str, result) -> str:
    display_expr = original_expr.replace("*", "×").replace("/", "÷")
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{display_expr} = **{result}**"


def evaluate_user_input(user_input: str) -> Tuple[str, List[str]]:
    original_sanitized = sanitize_expression(user_input)
    if original_sanitized == "":
        return ("I didn't find a valid expression. Try '12 + 8' or '25% of 400'.", [])

    try:
        value = safe_eval(original_sanitized)
    except ZeroDivisionError:
        return ("Division by zero is undefined. Please check your input.", ["Division by zero occurred."])
    except SafeEvalError as e:
        return (f"Could not evaluate the expression: {e}. Please use numbers, + - * / ** and parentheses. Examples: '12 + 8', '25% of 400', '(3 + 2) * 4'.", [])
    except Exception:
        return ("An unexpected error occurred while evaluating. Please check your input.", [])

    explanation_steps = explain_evaluation(original_sanitized)
    return (format_result(original_sanitized, value), explanation_steps)


# --- Streamlit UI ---

st.set_page_config(page_title="Simple Safe Calculator", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🧮 Simple Safe Calculator")
st.write("Enter a math expression in natural-ish form. Supports +, -, *, /, **, parentheses and % (e.g. '25% of 400').")

with st.form(key="calc_form"):
    user_input = st.text_input("Expression", value="",
                               placeholder="e.g. What is 12 + 8?  /  Calculate 25% of 400.")
    show_examples = st.checkbox("Show examples", value=False)
    include_steps = st.checkbox("Show step-by-step explanation", value=True)
    submit = st.form_submit_button("Evaluate")

    if show_examples:
        st.markdown("**Examples:**")
        st.write("- What is 12 + 8? -> 20")
        st.write("- Calculate 25% of 400. -> 100")
        st.write("- (15 + 5) * 3 -> 60")

if submit:
    if not user_input.strip():
        st.warning("Please enter a mathematical expression.")
    else:
        output, steps = evaluate_user_input(user_input)
        # store history
        st.session_state.history.insert(0, (user_input, output, steps))
        # display result
        st.markdown(output)

        # optional step-by-step explanation
        if include_steps:
            with st.expander("How this result was computed — step-by-step", expanded=True):
                if steps:
                    for i, s in enumerate(steps, start=1):
                        st.write(f"{i}. {s}")
                else:
                    st.write("No step-by-step explanation available for this expression.")

# history
with st.expander("History", expanded=False):
    if len(st.session_state.history) == 0:
        st.write("No history yet.")
    else:
        for i, (expr, out, steps) in enumerate(st.session_state.history[:50], start=1):
            st.write(f"{i}. **{expr}**  →  {out}")

# quick example buttons
st.markdown("---")
col1, col2, col3 = st.columns(3)
if col1.button("Example: 12 + 8"):
    st.session_state.clear()
    st.rerun()

if col2.button("Example: 25% of 400"):
    st.session_state.clear()
    st.rerun()

if col3.button("Example: (15 + 5) * 3"):
    st.session_state.clear()
    st.rerun()

st.markdown("---")
st.caption("Built with a safe AST-based evaluator. No function calls or names allowed — safe for embedding in chatbots.")
