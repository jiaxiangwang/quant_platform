from __future__ import annotations

import unittest
from pathlib import Path

from quant_kb.config import Settings
from quant_kb.service import KnowledgeSearchService


ROOT = Path(__file__).resolve().parents[1]


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = KnowledgeSearchService(
            Settings(knowledge_dir=ROOT / "knowledge")
        )

    def test_finds_t_and_tl(self) -> None:
        results = self.service.search("T 和 TL 有什么区别", top_k=3)
        self.assertEqual(results[0].document.id, "fixed-income-t-tl")

    def test_finds_sdk_identifier(self) -> None:
        results = self.service.search("client.query 怎么用", top_k=3)
        self.assertEqual(results[0].document.id, "sdk-pilot-query")

    def test_filters_category(self) -> None:
        results = self.service.search(
            "移动平均线", categories=["indicator"], top_k=5
        )
        self.assertTrue(results)
        self.assertTrue(
            all(result.document.category == "indicator" for result in results)
        )

    def test_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            self.service.search("   ")


if __name__ == "__main__":
    unittest.main()

