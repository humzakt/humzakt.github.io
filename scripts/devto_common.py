"""Shared helpers for Dev.to cross-posting scripts."""
import html
import json
import os
import re
import glob as globmod
import subprocess
import tempfile

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


def all_blog_slugs():
    """Every post slug currently on disk, excluding non-post pages."""
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in globmod.glob(os.path.join(REPO_ROOT, "blog", "*.html"))
    )


def sanitize_tag(tag):
    t = re.sub(r"[^a-z0-9]", "", tag.lower())
    return t[:30] if t else None


def inline_to_md(node):
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    name = node.name
    inner = "".join(inline_to_md(c) for c in node.children)
    if name in ("strong", "b"):
        return f"**{inner}**"
    if name in ("em", "i"):
        return f"*{inner}*"
    if name == "code":
        return f"`{inner}`"
    if name == "a":
        href = node.get("href", "")
        return f"[{inner}]({href})"
    if name == "br":
        return "\n"
    return inner


def block_to_md(node):
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
        lang = ""
        for c in code.get("class", []):
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
        return ""

    return "".join(block_to_md(c) for c in node.children)


def extract_post(html_path):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    canonical = soup.find("link", rel="canonical")
    canonical_url = canonical["href"] if canonical else None

    title_el = soup.find("h1", class_="blog-title")
    title = title_el.get_text().strip() if title_el else soup.title.get_text().split(" — ")[0]

    desc_meta = soup.find("meta", attrs={"name": "description"})
    description = desc_meta["content"].strip() if desc_meta else ""

    date_meta = soup.find("meta", attrs={"property": "article:published_time"})
    published_time = date_meta["content"].strip() if date_meta else None

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
        "blog_date": published_time,
    }


def _request(url, payload, api_key, method="POST", max_retries=4):
    # Shell out to curl rather than urllib: avoids local Python SSL trust-store
    # issues (common on macOS) and matches what the GitHub Actions runner needs
    # no extra setup for either.
    import time as _time

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        body_path = f.name
    try:
        for attempt in range(max_retries + 1):
            result = subprocess.run(
                [
                    "curl", "-s", "-w", "\n%{http_code}",
                    "-X", method, url,
                    "-H", f"api-key: {api_key}",
                    "-H", "Content-Type: application/json",
                    "--data", f"@{body_path}",
                ],
                capture_output=True, text=True, check=True,
            )
            body, status_code = result.stdout.rsplit("\n", 1)
            status_code = int(status_code)

            if status_code == 429 and attempt < max_retries:
                print(f"  rate limited, waiting 30s (attempt {attempt + 1}/{max_retries})...")
                _time.sleep(30)
                continue
            if status_code >= 400:
                raise RuntimeError(f"Dev.to API error {status_code} on {method} {url}: {body}")
            return json.loads(body)
    finally:
        os.unlink(body_path)


def create_article(post, api_key, published):
    payload = {
        "article": {
            "title": post["title"][:128],
            "body_markdown": post["body_markdown"],
            "published": published,
            "description": post["description"][:280] if post["description"] else None,
            "tags": post["tags"],
            "canonical_url": post["canonical_url"],
        }
    }
    return _request(DEVTO_API_URL, payload, api_key, method="POST")


def publish_article(article_id, api_key):
    payload = {"article": {"published": True}}
    return _request(f"{DEVTO_API_URL}/{article_id}", payload, api_key, method="PUT")
