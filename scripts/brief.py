#!/usr/bin/env python3
"""Write today's Morning Brief as a Jekyll post (_posts/YYYY-MM-DD-morning-brief.md).

For readers of the published brief, not for the person who set it up: headings and the intro say
what the brief is, each pick says which topic it is about.

Sources: one fetch function per site in SOURCES; only Hacker News so far (its front page, from the
public HN Algolia API, no key). Adding a site = adding a function that returns the same story dicts.
"Today's picks" = stories from all sources whose title matches a topic and that have at least
--min-points, ranked by points, each tagged with its topic and source; if fewer than --count, the
highest-scoring other stories fill the rest, one "Also popular on <source>" section per source.
Standard library only.

    python3 scripts/brief.py --sources hackernews --topics "AI, LLM, Rust, Postgres" --count 10 --min-points 50
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

API = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=100"
HN_ITEM = "https://news.ycombinator.com/item?id={}"


def fetch_hackernews():
    req = urllib.request.Request(API, headers={"User-Agent": "morning-brief"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        hits = json.load(resp)["hits"]
    stories = []
    for h in hits:
        if not h.get("title"):
            continue
        stories.append({
            "title": h["title"],
            "url": h.get("url") or HN_ITEM.format(h["objectID"]),
            "site": urllib.parse.urlparse(h["url"]).netloc.removeprefix("www.") if h.get("url") else "news.ycombinator.com",
            "points": h.get("points") or 0,
            "comments": h.get("num_comments") or 0,
            "discussion": HN_ITEM.format(h["objectID"]),
            "source": "Hacker News",
        })
    return stories


SOURCES = {"hackernews": fetch_hackernews}


def topic_pattern(topics):
    # Whole words, case-insensitive: "AI" matches "AI agents", not "said".
    words = [re.escape(t.strip()) for t in topics if t.strip()]
    return re.compile(r"(?<![\w-])(" + "|".join(words) + r")(?![\w-])", re.I) if words else None


def utc_offset(t):
    m = int(t.utcoffset().total_seconds() // 60)
    h, mm = divmod(abs(m), 60)
    return "UTC" + ("+" if m >= 0 else "-") + str(h) + (f":{mm:02d}" if mm else "")


def topic_of(pat, topics, title):
    # The topic as written in --topics ("open source", not "Open Source" from the title).
    m = pat.search(title)
    return next(t for t in topics if t.lower() == m.group(1).lower())


def line(i, s, tag=None):
    # tag: "**Rust** · Hacker News · " for a pick (topic and source); none in a per-source section.
    # Brackets would end the Markdown link; {{ and {% would be read as Liquid by Jekyll.
    title = s["title"].replace("[", "(").replace("]", ")").replace("{", "&#123;").replace("}", "&#125;")
    meta = f"{s['site']} · {s['points']} points · [{s['comments']} comments]({s['discussion']})"
    return f"{i}. [{title}]({s['url']}) — " + (f"**{tag}** · {s['source']} · " if tag else "") + meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="hackernews", help="comma-separated: " + ", ".join(SOURCES))
    ap.add_argument("--topics", default="", help="comma-separated, e.g. 'AI, Rust, Postgres'")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--min-points", type=int, default=50, help="a pick needs at least this many points")
    ap.add_argument("--out", default="_posts")
    args = ap.parse_args()

    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    names = [n.strip() for n in args.sources.split(",") if n.strip()]
    stories = sorted((s for n in names for s in SOURCES[n]()), key=lambda s: s["points"], reverse=True)
    source_names = list(dict.fromkeys(s["source"] for s in stories))
    pat = topic_pattern(topics)
    matched = [s for s in stories
               if pat and pat.search(s["title"]) and s["points"] >= args.min_points][: args.count]
    others = [s for s in stories if s not in matched][: max(0, args.count - len(matched))]

    now = dt.datetime.now().astimezone()
    today = now.date()
    lines = [
        "---",
        "layout: post",
        f'title: "Morning Brief — {today.strftime("%B")} {today.day}, {today.year}"',
        # The real time: Jekyll does not publish posts dated in the future.
        f"date: {now.strftime('%Y-%m-%d %H:%M:%S %z')}",
        "---",
        "",
        # Readers are anywhere: give the offset, not a zone name ("CST" is three different zones).
        f"Top stories from {' and '.join(source_names)} at {now.strftime('%H:%M')} {utc_offset(now)}"
        + (f", filtered to {', '.join(topics[:-1])} and {topics[-1]}." if len(topics) > 1
           else f", filtered to {topics[0]}." if topics else "."),
        "",
    ]
    if matched:
        lines += ["## Today's picks", ""] + [
            line(i, s, topic_of(pat, topics, s["title"])) for i, s in enumerate(matched, 1)] + [""]
    n = len(matched)
    for src in source_names:
        group = [s for s in others if s["source"] == src]
        if group:
            lines += [f"## Also popular on {src}", ""] + [line(i, s) for i, s in enumerate(group, n + 1)] + [""]
            n += len(group)

    out = pathlib.Path(args.out) / f"{today.isoformat()}-morning-brief.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"{len(stories)} stories from {', '.join(source_names)}; {len(matched)} picks on the topics.")
    for i, s in enumerate(matched + others, 1):
        print(f"{i:>2}. {s['points']:>4}  {s['title']}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
