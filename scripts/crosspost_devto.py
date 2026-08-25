#!/usr/bin/env python3
"""
Cross-post blog posts to Dev.to via their public API, with canonical_url
pointing back to the original so SEO credit stays with the blog.

Usage:
  python3 scripts/crosspost_devto.py <blog/post-slug.html> [<blog/other-slug.html> ...]

Reads DEVTO_API_KEY from the environment. Skips any file whose slug already
appears in scripts/.crosspost-state.json (idempotent — safe to re-run).
"""
import html
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

from bs4 import BeautifulSoup, NavigableString, Tag

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(REPO_ROOT, "scripts", ".crosspost-state.json")
DEVTO_API_URL = "https://dev.to/api/articles"
MAX_TAGS = 4


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def sanitize_tag(tag):
    t = re.sub(r"[^a-z0-9]", "", tag.lower())
    return t[:30] if t else None


def inline_to_md(node):
    """Convert inline content (text + <strong>/<em>/<code>/<a>) to markdown."""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    name = node.name
    inner = "".join(inline_to_md(c) for c in node.children)
    if name == "strong" or name == "b":
        return f"**{inner}**"
    if name == "em" or name == "i":
        return f"*{inner}*"
    if name == "code":
        return f"`{inner}`"
    if name == "a":
        href = node.get("href", "")
        return f"[{inner}]({href})"
    if name == "br":
        return "\n"
    return inner


def block_to_md(node, depth=0):
    """Convert a top-level block element from .blog-content to markdown."""
    if isinstance(node, NavigableString):
        text = str(node).strip()
        return text + "\n\n" if text else ""
    if not isinstance(node, Tag):
        return ""

    name = node.name

    if name in ("h2", "h3", "h4"):
        level = {"h2": "##", "h3": "###", "h4": "####"}[name]
        return f"{level} {inline_to_md(node).strip()}\n\n"

    if name == "p":
        text = inline_to_md(node).strip()
        return f"{text}\n\n" if text else ""

    if name in ("ul", "ol"):
        lines = []
        for i, li in enumerate(node.find_all("li", recursive=False)):
            marker = "-" if name == "ul" else f"{i + 1}."
            lines.append(f"{marker} {inline_to_md(li).strip()}")
        return "\n".join(lines) + "\n\n"

    if name == "blockquote":
        text = inline_to_md(node).strip()
        quoted = "\n".join(f"> {line}" for line in text.splitlines())
        return f"{quoted}\n\n"

    if name == "pre":
        code = node.find("code")
        if code is None:
            return ""
        classes = code.get("class", [])
        lang = ""
        for c in classes:
            if c.startswith("language-"):
                lang = c[len("language-"):]
        code_text = html.unescape(code.get_text())
        return f"```{lang}\n{code_text.rstrip()}\n```\n\n"

    if name == "table":
        rows = node.find_all("tr")
        if not rows:
            return ""
        out = []
        header_cells = rows[0].find_all(["th", "td"])
        out.append("| " + " | ".join(inline_to_md(c).strip() for c in header_cells) + " |")
        out.append("|" + "|".join(["---"] * len(header_cells)) + "|")
        for r in rows[1:]:
            cells = r.find_all(["th", "td"])
            out.append("| " + " | ".join(inline_to_md(c).strip() for c in cells) + " |")
        return "\n".join(out) + "\n\n"

    if name == "section":
        # e.g. Related Articles — excluded by caller, but guard just in case
        return ""

    # Fallback: recurse into children (e.g. a stray <div>)
    return "".join(block_to_md(c, depth + 1) for c in node.children)


def extract_post(html_path):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    canonical = soup.find("link", rel="canonical")
    canonical_url = canonical["href"] if canonical else None

    title_el = soup.find("h1", class_="blog-title")
    title = title_el.get_text().strip() if title_el else soup.title.get_text().split(" — ")[0]

    desc_meta = soup.find("meta", attrs={"name": "description"})
    description = desc_meta["content"].strip() if desc_meta else ""

    tags = []
    for span in soup.select(".blog-tag"):
        t = sanitize_tag(span.get_text())
        if t and t not in tags:
            tags.append(t)
        if len(tags) >= MAX_TAGS:
            break

    content_div = soup.find("div", class_="blog-content")
    if content_div is None:
        raise ValueError(f"No .blog-content found in {html_path}")

    body_md = "".join(block_to_md(c) for c in content_div.children).strip()

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "canonical_url": canonical_url,
        "body_markdown": body_md,
    }


def post_to_devto(post, api_key):
    payload = {
        "article": {
            "title": post["title"][:128],
            "body_markdown": post["body_markdown"],
            "published": True,
            "description": post["description"][:280] if post["description"] else None,
            "tags": post["tags"],
            "canonical_url": post["canonical_url"],
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEVTO_API_URL,
        data=data,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Dev.to API error {e.code}: {body}") from e


def main():
    paths = sys.argv[1:]
    if not paths:
        print("No files given — nothing to cross-post.")
        return

    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("DEVTO_API_KEY not set in environment — aborting.", file=sys.stderr)
        sys.exit(1)

    state = load_state()

    for path in paths:
        slug = os.path.splitext(os.path.basename(path))[0]
        abs_path = path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)

        if slug in state:
            print(f"skip {slug}: already cross-posted ({state[slug]['url']})")
            continue
        if not os.path.exists(abs_path):
            print(f"skip {slug}: file not found at {abs_path}")
            continue

        try:
            post = extract_post(abs_path)
            if not post["body_markdown"]:
                print(f"skip {slug}: empty body after conversion")
                continue
            result = post_to_devto(post, api_key)
            state[slug] = {
                "id": result.get("id"),
                "url": result.get("url"),
                "postedAt": result.get("published_at") or result.get("created_at"),
            }
            print(f"posted {slug} -> {result.get('url')}")
            save_state(state)  # persist after every success, not just at the end
        except Exception as e:
            print(f"FAILED {slug}: {e}", file=sys.stderr)

        time.sleep(2)  # be polite to the API between posts


if __name__ == "__main__":
    main()
