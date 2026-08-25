#!/usr/bin/env python3
"""
Cross-post newly-added blog posts to Dev.to via their public API, with
canonical_url pointing back to the original so SEO credit stays with the blog.

Usage:
  python3 scripts/crosspost_devto.py <blog/post-slug.html> [<blog/other-slug.html> ...]

Reads DEVTO_API_KEY from the environment. Skips any file whose slug already
appears in scripts/.crosspost-state.json (idempotent — safe to re-run).
Invoked automatically by .github/workflows/crosspost-devto.yml on every push
to gh-pages that adds new blog/*.html files.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devto_common import REPO_ROOT, extract_post, create_article, load_state, save_state  # noqa: E402


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
            result = create_article(post, api_key, published=True)
            state[slug] = {
                "id": result.get("id"),
                "url": result.get("url"),
                "postedAt": result.get("published_at") or result.get("created_at"),
            }
            print(f"posted {slug} -> {result.get('url')}")
            save_state(state)  # persist after every success, not just at the end
        except Exception as e:
            print(f"FAILED {slug}: {e}", file=sys.stderr)

        time.sleep(3)  # be polite to the API between posts


if __name__ == "__main__":
    main()
