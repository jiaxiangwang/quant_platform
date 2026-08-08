from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from quant_kb.loaders import load_documents


class LoaderTests(unittest.TestCase):
    def test_loads_markdown_and_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "term.md").write_text(
                "---\nid: term-t\ntitle: T\ncategory: fixed_income\n"
                "keywords: [国债期货]\n---\nT 是国债期货。\n",
                encoding="utf-8",
            )
            (root / "ma.yaml").write_text(
                "id: indicator-ma\ntitle: MA\ncategory: indicator\n"
                "description: 移动平均线\n",
                encoding="utf-8",
            )
            documents = load_documents(root)
        self.assertEqual(
            {document.id for document in documents},
            {"term-t", "indicator-ma"},
        )

    def test_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = "---\nid: same\ntitle: A\ncategory: test\n---\nA\n"
            (root / "a.md").write_text(content, encoding="utf-8")
            (root / "b.md").write_text(
                content.replace("title: A", "title: B"), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "id 重复"):
                load_documents(root)


if __name__ == "__main__":
    unittest.main()

