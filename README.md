# Morning Brief

Top tech stories, filtered to a few topics, published every morning at 8:
**https://printfapp.github.io/morning-brief/** (RSS: `/feed.xml`). Sources: Hacker News (more to come).

## How it works

- `scripts/brief.py` reads each source (Hacker News: its front page, from the public HN Algolia API,
  no key), keeps the stories whose title matches the topics and that have at least 50 points
  ("Today's picks", each tagged with its topic and source), ranks them by points and takes the top 10.
  If fewer than 10 qualify, the highest-scoring other stories fill the rest, one "Also popular on …"
  section per source. It writes `_posts/YYYY-MM-DD-morning-brief.md`. Python 3 standard library only.
- GitHub Pages builds the site with Jekyll (theme `minima`): one page per brief, a home page listing
  them, and an RSS feed (`jekyll-feed`). No build step in this repo.
- A [cmdbook](https://printf.app/cmdbook) command runs the script, commits and pushes; a cmdbook
  automation runs that command every day at 08:00.

## Run it by hand

```sh
python3 scripts/brief.py --sources hackernews --topics "AI, LLM, Rust, Postgres, SQLite, security, open source" --count 10 --min-points 50
git add _posts && git commit -m "Morning Brief $(date +%Y-%m-%d)" && git push
```

## Add a source

Write a `fetch_<name>()` in `scripts/brief.py` that returns stories with `title`, `url`, `site`,
`points`, `comments`, `discussion` and `source`, add it to `SOURCES`, and pass `--sources hackernews,<name>`.

## Set up GitHub Pages

Settings → Pages → Build and deployment → Source: *Deploy from a branch*, branch `main`, folder `/ (root)`.
