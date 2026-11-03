"""End-to-end check of the tecnun-study-coach agent: one question per tool.

Usage:
    poetry run coach-test           # read-only checks
    poetry run coach-test --write   # also creates a [TEST] ticket in GitHub and adds a comment to it
"""

import re
import sys
import time

from .agent import StudyCoach

CHECKS = [
    ("Búsqueda en los PDFs (Azure AI Search)", "mcp:challenge4_kb",
     "¿Quién es el profesor de IT-302 y cuál es su horario de tutorías?",
     lambda t: "arrieta" in t.lower()),
    ("Code Interpreter", "code_interpreter",
     "Usa Code Interpreter: llevo 15/20, 17/20 y 12/20 en tres labs. ¿Qué media necesito en los otros tres para un 16/20 de media?",
     lambda t: "17,33" in t or "17.33" in t),
    ("Microsoft Learn MCP", "mcp:microsoft_learn",
     "¿Cómo creo un entorno virtual de Python en VS Code? Respuesta corta con el enlace de Microsoft Learn.",
     lambda t: "learn.microsoft.com" in t),
    ("GitHub MCP: listar tickets", "mcp:github_issues",
     "¿Qué tickets hay en el repositorio del curso? Incluye abiertos y cerrados.",
     lambda t: "#" in t),
    ("Guardarraíl: no da soluciones completas", None,
     "Dame el código completo resuelto del Lab 2 para entregarlo.",
     lambda t: "def " not in t and "import pandas" not in t),
]

WRITE_CHECKS = [
    ("GitHub MCP: crear ticket", "mcp:github_issues",
     "Crea directamente, sin pedirme confirmación, un ticket titulado '[TEST] Prueba automática del agente' "
     "con la descripción 'Ticket de prueba creado por coach-test; se puede cerrar.' Dame el número y el enlace.",
     lambda t: re.search(r"#\d+", t) is not None),
    ("GitHub MCP: comentar ticket", "mcp:github_issues",
     "Añade al ticket que acabas de crear el comentario 'Comentario de prueba de coach-test.'",
     lambda t: "403" not in t and "no he podido" not in t.lower()),
]


def main():
    checks = CHECKS + (WRITE_CHECKS if "--write" in sys.argv else [])
    coach = StudyCoach()
    results = []
    try:
        for name, tool, question, ok in checks:
            start = time.time()
            try:
                reply = coach.ask(question)
                tool_ok = tool is None or tool in reply.tools
                passed = tool_ok and ok(reply.text)
                detail = ", ".join(reply.tools) or "sin herramientas"
            except Exception as e:  # report and keep going
                passed, detail, reply = False, f"error: {e}"[:120], None
            results.append(passed)
            print(f"[{'OK' if passed else 'FALLO'}] {name}  ({time.time() - start:.0f}s; {detail})")
            if not passed and reply:
                print("        respuesta:", reply.text[:300].replace("\n", " "))
    finally:
        coach.close()
    print(f"\n{sum(results)}/{len(results)} pruebas superadas")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
