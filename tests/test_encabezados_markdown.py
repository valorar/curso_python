"""Regresión de formato: python3 -m unittest discover -s tests -v."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SECTION = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(Nota|Notas|Ejemplos)"
    r"(?:\*\*)?\s*:?(?:\*\*)?\s*$"
)


def heading_errors(source):
    """Detecta rótulos de sección, sin confundir prosa ni bloques de código."""
    errors = []
    fence = None
    lines = source.splitlines()
    for index, line in enumerate(lines):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        match = SECTION.fullmatch(line)
        if match:
            if line != "#### " + match.group(1):
                errors.append((index + 1, "encabezado", line))
            if index + 1 >= len(lines) or lines[index + 1] != "":
                errors.append((index + 1, "falta línea vacía", line))
    return errors


class HeadingFormatTests(unittest.TestCase):
    def test_published_notebooks(self):
        notebooks = sorted(ROOT.glob("soluciones/*.ipynb")) + sorted(
            ROOT.glob("ejercicios/nivel*/*.ipynb")
        )
        self.assertTrue(notebooks)
        for path in notebooks:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] == "markdown":
                    with self.subTest(path=str(path.relative_to(ROOT)), cell=index):
                        self.assertEqual(heading_errors("".join(cell["source"])), [])

    def test_accepts_level_four_and_blank_line(self):
        for label in ("Nota", "Notas", "Ejemplos"):
            self.assertEqual(heading_errors(f"#### {label}\n\nTexto"), [])

    def test_rejects_wrong_level_bold_colon_or_missing_blank(self):
        for label in ("Nota", "Notas", "Ejemplos"):
            for heading in (f"### {label}", f"**{label}**", f"#### {label}:",
                            f"#### **{label}**", f"**{label}:**"):
                with self.subTest(heading=heading):
                    self.assertTrue(heading_errors(heading + "\n\nTexto"))
            self.assertTrue(heading_errors(f"#### {label}\nTexto"))
            self.assertTrue(heading_errors(f"#### {label}"))

    def test_preserves_prose_and_code_examples(self):
        self.assertEqual(heading_errors(
            "La Nota garantiza texto no vacío.\n\n```python\n### Notas\n```\n"
        ), [])


if __name__ == "__main__":
    unittest.main()
