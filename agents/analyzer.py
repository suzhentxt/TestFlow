"""Static source analyzer for target Python files."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .base import BaseAgent


class AnalyzerAgent(BaseAgent):
    """Extract import, class, function, and visible exception details."""

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        target_file = state.get("target_file") or state.get("path")
        if not target_file:
            raise ValueError("AnalyzerAgent requires state['target_file'] or state['path'].")

        path = Path(target_file)
        source = path.read_text(encoding=state.get("encoding", "utf-8"))
        tree = ast.parse(source, filename=str(path))

        return {
            "path": str(path),
            "module": path.stem,
            "imports": self._imports(tree),
            "functions": [self._function_info(node) for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))],
            "classes": [self._class_info(node) for node in tree.body if isinstance(node, ast.ClassDef)],
            "exceptions": sorted(self._exceptions(tree)),
            "source": source,
        }

    def _imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        imports: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"type": "import", "module": alias.name, "asname": alias.asname})
            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    {
                        "type": "from",
                        "module": node.module or "",
                        "names": [{"name": alias.name, "asname": alias.asname} for alias in node.names],
                        "level": node.level,
                    }
                )
        return imports

    def _function_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
        return {
            "name": node.name,
            "signature": self._signature(node),
            "args": self._arg_names(node.args),
            "returns": ast.unparse(node.returns) if node.returns else None,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
            "raises": sorted(self._exceptions(node)),
            "lineno": node.lineno,
        }

    def _class_info(self, node: ast.ClassDef) -> dict[str, Any]:
        return {
            "name": node.name,
            "bases": [ast.unparse(base) for base in node.bases],
            "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
            "methods": [
                self._function_info(child)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
            "raises": sorted(self._exceptions(node)),
            "lineno": node.lineno,
        }

    def _signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        args = node.args
        parts: list[str] = []
        positional = list(args.posonlyargs) + list(args.args)
        defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
        for arg, default in zip(positional, defaults):
            parts.append(self._format_arg(arg, default))
        if args.vararg:
            parts.append("*" + self._format_arg(args.vararg, None))
        elif args.kwonlyargs:
            parts.append("*")
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            parts.append(self._format_arg(arg, default))
        if args.kwarg:
            parts.append("**" + self._format_arg(args.kwarg, None))
        return f"{node.name}({', '.join(parts)})"

    def _format_arg(self, arg: ast.arg, default: ast.expr | None) -> str:
        value = arg.arg
        if arg.annotation:
            value += f": {ast.unparse(arg.annotation)}"
        if default is not None:
            value += f" = {ast.unparse(default)}"
        return value

    def _arg_names(self, args: ast.arguments) -> list[str]:
        names = [arg.arg for arg in args.posonlyargs + args.args]
        if args.vararg:
            names.append(args.vararg.arg)
        names.extend(arg.arg for arg in args.kwonlyargs)
        if args.kwarg:
            names.append(args.kwarg.arg)
        return names

    def _exceptions(self, node: ast.AST) -> set[str]:
        exceptions: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc is not None:
                exceptions.add(self._exception_name(child.exc))
            elif isinstance(child, ast.ExceptHandler):
                if child.type is None:
                    exceptions.add("Exception")
                else:
                    exceptions.add(self._exception_name(child.type))
        return exceptions

    def _exception_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Call):
            return self._exception_name(node.func)
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node)
        if isinstance(node, ast.Tuple):
            return ", ".join(self._exception_name(element) for element in node.elts)
        return ast.unparse(node)
