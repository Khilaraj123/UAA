"""FastAPI discovery adapter using Python AST."""

import ast
from pathlib import Path
from typing import List, Optional
from adapters.discovery.base import BaseDiscoveryAdapter
from engine.specification.models import Endpoint, SourceEvidence, make_endpoint_id, normalize_path

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

class FastAPIDiscoveryAdapter(BaseDiscoveryAdapter):
    @property
    def name(self) -> str:
        return "fastapi"

    def detect(self, repo_path: Path) -> bool:
        for py_file in repo_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in content.lower() or "from fastapi import" in content:
                    return True
            except Exception:
                continue
        return False

    def discover(self, repo_path: Path) -> List[Endpoint]:
        endpoints: List[Endpoint] = []
        for py_file in repo_path.rglob("*.py"):
            # Skip virtual environments or cache
            if any(part in py_file.parts for part in (".venv", "venv", "__pycache__", ".git")):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        ep = self._parse_decorator(decorator, node, py_file, repo_path)
                        if ep:
                            endpoints.append(ep)
        return endpoints

    def _parse_decorator(
        self,
        decorator: ast.AST,
        func_node: ast.AST,
        file_path: Path,
        repo_root: Path,
    ) -> Optional[Endpoint]:
        if not isinstance(decorator, ast.Call):
            return None

        # Check call attribute, e.g., app.get or router.post
        func = decorator.func
        if not isinstance(func, ast.Attribute):
            return None

        method = func.attr.lower()
        if method not in HTTP_METHODS:
            return None

        # Extract path argument
        path = "/"
        if decorator.args:
            first_arg = decorator.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                path = first_arg.value

        rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
        norm_path = normalize_path(path)
        ep_id = make_endpoint_id("rest", method.upper(), norm_path)

        # Extract docstring if present
        docstring = ast.get_docstring(func_node)

        # Check for authentication dependency in function arguments
        has_auth = False
        parameters = []
        for arg in func_node.args.args:
            arg_name = arg.arg
            parameters.append({"name": arg_name, "in": "query", "required": False})

        for default in func_node.args.defaults:
            if isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
                if default.func.id in ("Depends", "Security"):
                    has_auth = True

        evidence = SourceEvidence(
            source_type="framework_route",
            file_path=rel_path,
            line_start=func_node.lineno,
            line_end=getattr(func_node, "end_lineno", func_node.lineno),
            symbol=func_node.name,
            confidence="high",
        )

        return Endpoint(
            endpoint_id=ep_id,
            api_type="rest",
            method=method.upper(),
            path_template=norm_path,
            discovery_status="confirmed",
            confidence="high",
            source_evidence=[evidence],
            operation_id=func_node.name,
            summary=docstring.split("\n")[0] if docstring else None,
            description=docstring,
            parameters=parameters,
            authentication={"required": has_auth},
            side_effect_risk="read" if method.upper() in ("GET", "HEAD") else "reversible_write",
            tags=["fastapi"],
        )

