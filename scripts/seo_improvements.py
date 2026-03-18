"""
SEO improvements based on Google SEO Starter Guide:
1. Add og:image to all content pages
2. Complete Twitter Card (twitter:image, twitter:title, twitter:description, summary_large_image)
3. Add LCP preload script to <head> on all content pages
4. Add fetchpriority="high" decoding="async" to #pg-bg-img
5. Add image field to Article structured data
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OG_IMAGE = "https://www.vilketveckonummer.se/images/spring.png"

LCP_PRELOAD = (
    "  <!-- Preload seasonal LCP image with high priority -->\n"
    "  <script>(function(){var m=new Date().getMonth();"
    "var s=m<=1||m===11?'vinter':m<=4?'spring':m<=7?'summer':'fall';"
    "var l=document.createElement('link');l.rel='preload';l.as='image';"
    "l.href='/images/'+s+'.png';l.setAttribute('fetchpriority','high');"
    "document.head.insertBefore(l,document.head.firstChild);})();</script>"
)

IMAGE_SCHEMA = {
    "@type": "ImageObject",
    "url": OG_IMAGE,
    "width": 1200,
    "height": 630,
}


def process_file(filepath: Path) -> list[str]:
    """Process a single index.html, return list of changes made."""
    text = filepath.read_text(encoding="utf-8")
    changes: list[str] = []

    # ------------------------------------------------------------------ #
    # 1. og:image — insert before og:url (or after og:site_name fallback)
    # ------------------------------------------------------------------ #
    if '<meta property="og:image"' not in text:
        if '<meta property="og:url"' in text:
            text = text.replace(
                '<meta property="og:url"',
                f'<meta property="og:image" content="{OG_IMAGE}" />\n  <meta property="og:url"',
            )
            changes.append("og:image added")
        elif '<meta name="twitter:card"' in text:
            text = text.replace(
                '<meta name="twitter:card"',
                f'<meta property="og:image" content="{OG_IMAGE}" />\n  <meta name="twitter:card"',
            )
            changes.append("og:image added (fallback position)")

    # ------------------------------------------------------------------ #
    # 2. Twitter Card: upgrade to summary_large_image + add missing tags
    # ------------------------------------------------------------------ #
    if '<meta name="twitter:card" content="summary" />' in text:
        og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
        og_desc = re.search(r'<meta property="og:description" content="([^"]*)"', text)

        twitter_extra = ""
        if og_title and '<meta name="twitter:title"' not in text:
            twitter_extra += f'\n  <meta name="twitter:title" content="{og_title.group(1)}" />'
        if og_desc and '<meta name="twitter:description"' not in text:
            twitter_extra += f'\n  <meta name="twitter:description" content="{og_desc.group(1)}" />'
        if '<meta name="twitter:image"' not in text:
            twitter_extra += f'\n  <meta name="twitter:image" content="{OG_IMAGE}" />'

        # Upgrade card type to summary_large_image for bigger previews
        replacement = f'<meta name="twitter:card" content="summary_large_image" />{twitter_extra}'
        text = text.replace('<meta name="twitter:card" content="summary" />', replacement)
        changes.append("Twitter Card completed (summary_large_image + title/desc/image)")

    # ------------------------------------------------------------------ #
    # 3. LCP preload script in <head>
    # ------------------------------------------------------------------ #
    if "l.rel='preload'" not in text and "<title>" in text:
        text = text.replace("  <title>", f"{LCP_PRELOAD}\n  <title>")
        changes.append("LCP preload script added")

    # ------------------------------------------------------------------ #
    # 4. fetchpriority + decoding on #pg-bg-img
    # ------------------------------------------------------------------ #
    if 'id="pg-bg-img" alt=""' in text and "fetchpriority" not in text:
        text = text.replace(
            '<img id="pg-bg-img" alt="" />',
            '<img id="pg-bg-img" alt="" fetchpriority="high" decoding="async" />',
        )
        changes.append("fetchpriority/decoding added to pg-bg-img")

    # ------------------------------------------------------------------ #
    # 5. Add image to Article JSON-LD
    # ------------------------------------------------------------------ #
    # Find all <script type="application/ld+json"> blocks and patch Article types
    def patch_jsonld(match: re.Match) -> str:
        raw = match.group(0)
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return raw

        patched = False

        def patch_node(node: dict) -> None:
            nonlocal patched
            if node.get("@type") == "Article" and "image" not in node:
                node["image"] = IMAGE_SCHEMA
                patched = True

        if isinstance(data, dict):
            if data.get("@type") == "Article":
                patch_node(data)
            elif "@graph" in data and isinstance(data["@graph"], list):
                for node in data["@graph"]:
                    if isinstance(node, dict):
                        patch_node(node)

        if patched:
            new_json = json.dumps(data, ensure_ascii=False, indent=2)
            return f'<script type="application/ld+json">\n  {new_json}\n  </script>'
        return raw

    new_text, n_subs = re.subn(
        r'<script type="application/ld\+json">\s*([\s\S]*?)\s*</script>',
        patch_jsonld,
        text,
    )
    if n_subs and new_text != text:
        text = new_text
        changes.append("Article JSON-LD: image field added")

    if changes:
        filepath.write_text(text, encoding="utf-8")
    return changes


def main() -> None:
    processed = 0
    skipped = 0
    all_changes: dict[str, list[str]] = {}

    for html_file in sorted(ROOT.rglob("index.html")):
        # Skip root homepage and scripts/ subfolder
        if html_file.parent == ROOT:
            continue
        if "scripts" in html_file.parts:
            continue

        rel = html_file.relative_to(ROOT).as_posix()
        changes = process_file(html_file)
        if changes:
            processed += 1
            all_changes[rel] = changes
        else:
            skipped += 1

    print(f"\nSEO improvements complete: {processed} files updated, {skipped} unchanged.\n")
    for path, changes in all_changes.items():
        print(f"  {path}")
        for c in changes:
            print(f"    • {c}")


if __name__ == "__main__":
    main()
