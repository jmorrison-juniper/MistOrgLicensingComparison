import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_uses_only_the_six_requested_sections(self):
        readme = (ROOT / "README.md").read_text()
        headings = re.findall(r"^## (.+)$", readme, re.MULTILINE)

        self.assertEqual(headings, ["What", "How", "Where", "When", "Why", "Who"])

    def test_local_markdown_links_resolve(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]

        for document in documents:
            with self.subTest(document=document.relative_to(ROOT)):
                contents = document.read_text()
                links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", contents)
                for link in links:
                    if link.startswith(("http://", "https://", "#")):
                        continue
                    target = (document.parent / link.split("#", 1)[0]).resolve()
                    self.assertTrue(target.exists(), f"Broken link in {document}: {link}")

    def test_readme_embeds_nonempty_png_screenshots(self):
        readme = (ROOT / "README.md").read_text()
        screenshots = re.findall(
            r"!\[[^\]]*\]\((docs/screenshots/[^)]+\.png)\)", readme
        )

        self.assertEqual(
            screenshots,
            [
                "docs/screenshots/license-comparison.png",
                "docs/screenshots/manual-organization.png",
                "docs/screenshots/remaining-licenses.png",
            ],
        )
        for screenshot in screenshots:
            image = ROOT / screenshot
            self.assertGreater(image.stat().st_size, 0, f"Empty screenshot: {screenshot}")
            self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
