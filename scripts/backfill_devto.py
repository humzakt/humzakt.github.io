#!/usr/bin/env python3
"""
One-time backfill: publish every blog post not already on Dev.to.
Safe to re-run — skips anything already present in scripts/.crosspost-state.json.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devto_common import (  # noqa: E402
    REPO_ROOT, all_blog_slugs, extract_post, create_article, load_state, save_state,
)


def main():
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("DEVTO_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    state = load_state()
    slugs = all_blog_slugs()
    todo = [s for s in slugs if s not in state]

    print(f"{len(slugs)} total posts, {len(state)} already on Dev.to, {len(todo)} to publish now.")

    posted, failed = 0, 0
    for slug in todo:
        path = os.path.join(REPO_ROOT, "blog", f"{slug}.html")
        try:
            post = extract_post(path)
            if not post["body_markdown"]:
                print(f"skip {slug}: empty body")
                continue
            result = create_article(post, api_key, published=True)
            state[slug] = {
                "id": result.get("id"),
                "url": result.get("url"),
                "postedAt": result.get("published_at") or result.get("created_at"),
            }
            save_state(state)
            posted += 1
            print(f"[{posted}/{len(todo)}] posted {slug} -> {result.get('url')}")
        except Exception as e:
            failed += 1
            print(f"FAILED {slug}: {e}", file=sys.stderr)
        time.sleep(3)

    print(f"\nDone. Posted: {posted}, Failed: {failed}, Already had: {len(state) - posted}")


if __name__ == "__main__":
    main()
