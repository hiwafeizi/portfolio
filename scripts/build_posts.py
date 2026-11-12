"""Build the static parts of the site from resume.json and blogs.json.

Run after adding or editing a post, or after changing resume.json:

    python scripts/build_posts.py

It writes:
  blog/<slug>.html          one page per Markdown post in blogs/posts/
  blog/post.html            old ?slug= links: redirects to the static page
  functions/blog/post.js    the same redirect as a server side 301 (Cloudflare Pages Function)
  index.html, blog/index.html   static content between <!-- static:NAME --> markers
  sitemap.xml, robots.txt, llms.txt
"""

import html
import json
import re
from datetime import date
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://hiwafeizi.com"
AUTHOR = "Hiwa Feizi"

def esc(text):
    """Escape for text and double-quoted attributes; apostrophes stay readable for plain parsers."""
    return html.escape(str(text), quote=False).replace('"', "&quot;")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def post_file(post):
    return post.get("href") or f"{post['slug']}.html"


def post_url(post):
    """Clean URL: Cloudflare Pages serves blog/x.html at /blog/x."""
    return f"{SITE}/blog/{post_file(post).removesuffix('.html')}"


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


def fill(text, name, content):
    pattern = re.compile(rf"(<!-- static:{name} -->).*?(<!-- /static:{name} -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"marker static:{name} not found")
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


# ---------- Markdown posts ----------

MD = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")

# "# Title", then an optional "**Month YYYY**" line and "---": the page header shows both.
POST_HEADER = re.compile(r"\A\s*# [^\n]*\n+(?:\*\*[A-Z][a-z]+ \d{4}\*\*[ \t]*\n+)?(?:---[ \t]*\n+)?")


def render_markdown(text):
    tokens = MD.parse(POST_HEADER.sub("", text, count=1))
    for token in tokens:
        for child in token.children or []:
            src = child.attrGet("src") if child.type == "image" else None
            if src and not re.match(r"^(https?:|/|\.\./|data:)", src):
                child.attrSet("src", f"../blogs/images/{src}")
    return MD.renderer.render(tokens, MD.options, {})


POST_CSS = """
  :root{
    --bg:#0b1020; --card:#141d38; --card2:#18234a;
    --ink:#e8edff; --muted:#9aa7cc; --line:#26315c;
    --accent:#5b9dff; --accent2:#7c7cff; --good:#3ddc97; --bad:#ff6b7d; --warn:#ffcf6b;
    --mono:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:linear-gradient(180deg,#0b1020,#0a0e1c 60%);color:var(--ink);
       font-family:var(--sans);line-height:1.6;font-size:17px}
  @media(max-width:700px){body{font-size:15.5px}}
  code{font-family:var(--mono);font-size:.9em;background:var(--card);border:1px solid var(--line);
       border-radius:5px;padding:1px 5px;color:#a9c4ff}
  a{color:var(--accent)}

  .shell{max-width:1080px;margin:0 auto}
  .backlink{display:inline-block;font-size:13px;color:var(--muted);text-decoration:none;margin-bottom:20px}
  .backlink:hover{color:var(--accent)}
  main{padding:42px 44px 90px;min-width:0}
  @media(max-width:900px){main{padding:28px 20px 70px}}

  h1{font-size:clamp(23px,5.5vw,32px);margin:10px 0 6px;letter-spacing:-.4px;max-width:820px}
  .meta{color:var(--muted);font-size:14px;margin:0 0 12px}
  .meta a{color:var(--muted)}
  .tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 28px}
  .tags a{font-size:12px;color:var(--muted);text-decoration:none;border:1px solid var(--line);
          border-radius:999px;padding:2px 10px}
  .tags a:hover{color:var(--accent);border-color:var(--accent)}
  .cover{display:block;width:100%;max-width:900px;max-height:420px;object-fit:cover;
         border-radius:12px;border:1px solid var(--line);margin:0 0 32px}

  article h2{font-size:23px;margin:44px 0 14px;padding-top:14px;border-top:1px solid var(--line);letter-spacing:-.2px}
  article h2:first-child,article hr + h2{border-top:none;margin-top:0;padding-top:0}
  article h3{font-size:16.5px;margin:26px 0 10px}
  article p{margin:0 0 14px;max-width:760px}
  article ul,article ol{margin:0 0 14px;padding-left:22px;max-width:760px}
  article li{margin-bottom:6px}
  article strong{color:#fff}
  article hr{border:none;border-top:1px solid var(--line);margin:32px 0;max-width:760px}
  article blockquote{margin:16px 0;padding:12px 18px;max-width:760px;background:var(--card);
        border:1px solid var(--line);border-left:3px solid var(--warn);border-radius:10px;color:var(--muted)}
  article blockquote p:last-child{margin-bottom:0}
  article pre{background:#07131a;border:1px solid var(--line);border-radius:10px;padding:14px 18px;
        overflow-x:auto;margin:0 0 20px;max-width:900px;font-size:14px;line-height:1.6}
  article pre code{background:none;border:none;padding:0;color:#e2e8f0}
  article img{max-width:100%;border-radius:10px;border:1px solid var(--line);margin:8px 0 20px}
  article table{width:100%;border-collapse:collapse;font-size:14.5px;margin:0 0 20px;max-width:900px}
  article th,article td{text-align:left;padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
  article th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px;font-weight:700}
  article tr:last-child td{border-bottom:none}
  article iframe{max-width:100%;border:0;border-radius:10px;margin:0 0 20px}
  .linkedin-embeds{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:16px;margin:0 0 20px}
  .linkedin-embeds iframe{width:100%;height:auto;aspect-ratio:504/700;margin:0}

  .foot{margin-top:60px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
  .foot a{color:var(--muted)}
  @media(max-width:700px){article h2{font-size:19px}article table{display:block;overflow-x:auto}}
"""


def post_page(post, body):
    url = post_url(post)
    title = post["title"]
    summary = post["summary"]
    cover = f"{SITE}/blogs/images/{post['cover']}" if post.get("cover") else None
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": summary,
        "datePublished": post["date"],
        "author": {"@type": "Person", "name": AUTHOR, "url": f"{SITE}/"},
        "keywords": post.get("tags", []),
        "url": url,
        "mainEntityOfPage": url,
    }
    if cover:
        ld["image"] = cover
    tags = "".join(
        f'<a href="index.html?tag={esc(t)}">{esc(t)}</a>' for t in post.get("tags", [])
    )
    cover_tag = (
        f'\n    <img class="cover" src="../blogs/images/{esc(post["cover"])}" alt="{esc(title)}">'
        if post.get("cover") else ""
    )
    og_image = f'\n<meta property="og:image" content="{esc(cover)}">' if cover else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{esc(title)} | {AUTHOR}</title>
<meta name="description" content="{esc(summary)}">
<meta name="author" content="{AUTHOR}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(summary)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">{og_image}
<link rel="icon" type="image/png" href="../favicon.png">
<script type="application/ld+json">
{json_ld(ld)}
</script>
<!-- Generated by scripts/build_posts.py from blogs/posts/{post['slug']}.md. Edit the Markdown, not this file. -->
<style>{POST_CSS}</style>
</head>
<body>
<div class="shell">
  <main>
    <a class="backlink" href="index.html">&#8592; All blogs</a>
    <h1>{esc(title)}</h1>
    <p class="meta">{fmt_date(post['date'])} &middot; {esc(post.get('readTime', ''))} read &middot; by <a href="../index.html">{AUTHOR}</a></p>
    <div class="tags">{tags}</div>{cover_tag}
    <article>
{body}    </article>
    <div class="foot">
      Written by {AUTHOR}. <a href="index.html">All blogs</a> &middot; <a href="../index.html">Portfolio</a> &middot; <a href="/resume.json">CV as JSON</a>
    </div>
  </main>
</div>
</body>
</html>
"""


def build_posts(posts):
    built = []
    for post in posts:
        md_path = ROOT / "blogs" / "posts" / f"{post['slug']}.md"
        if not md_path.exists():
            continue
        post.setdefault("href", f"{post['slug']}.html")
        body = render_markdown(md_path.read_text(encoding="utf-8"))
        write(ROOT / "blog" / post["href"], post_page(post, body))
        built.append(post["slug"])
    return built


# ---------- old ?slug= links ----------

def build_redirects(posts):
    targets = {p["slug"]: post_file(p).removesuffix(".html") for p in posts}
    known = json.dumps(sorted(targets))
    links = "\n".join(
        f'    <li><a href="{esc(post_file(p))}">{esc(p["title"])}</a></li>' for p in posts
    )
    write(ROOT / "blog" / "post.html", f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script>(function(){{var known={known};var s=new URLSearchParams(location.search).get("slug");location.replace(known.indexOf(s)>-1?s+".html":"index.html");}})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<link rel="canonical" href="{SITE}/blog/">
<title>Moved | {AUTHOR}</title>
<!-- Generated by scripts/build_posts.py. Old links (post.html?slug=x) land here; functions/blog/post.js does the same as a 301. -->
</head>
<body>
  <p>Every post now has its own page:</p>
  <ul>
{links}
  </ul>
</body>
</html>
""")
    write(ROOT / "functions" / "blog" / "post.js", f"""// Generated by scripts/build_posts.py. Do not edit by hand.
// Old links: /blog/post?slug=x -> 301 to /blog/x, so readers without JavaScript land on the post.
const TARGETS = {json.dumps(targets, indent=2)};

export function onRequest({{ request }}) {{
  const url = new URL(request.url);
  const target = TARGETS[url.searchParams.get("slug")];
  return Response.redirect(`${{url.origin}}/blog/${{target || ""}}`, 301);
}}
""")


# ---------- homepage ----------

def blog_href(blog):
    return f"blog/{blog if blog.endswith('.html') else blog + '.html'}"


def render_list(items, indent):
    lines = [f"{indent}<ul>"]
    for item in items:
        text = item if isinstance(item, str) else item.get("text")
        if not text:
            continue
        link = ""
        if isinstance(item, dict) and item.get("blog"):
            link = f' <a class="bullet-blog-link" href="{esc(blog_href(item["blog"]))}">Read in depth &#8594;</a>'
        lines.append(f"{indent}    <li>{esc(text)}{link}</li>")
    lines.append(f"{indent}</ul>")
    return "\n".join(lines)


def render_experience(entry, i):
    company = entry["company"] + (f", {entry['location']}" if entry.get("location") else "")
    out = [
        f'{i}<div class="timeline-item">',
        f'{i}    <div class="timeline-header"><h3>{esc(company)}</h3><span>{esc(entry.get("timeframe", ""))}</span></div>',
    ]
    if entry.get("notes"):
        out.append(f"{i}    <p>{esc(entry['notes'])}</p>")
    for role in entry.get("roles", []):
        out.append(f"{i}    <h4>{esc(role['title'])} ({esc(role['timeframe'])})</h4>")
        if role.get("groups"):
            for group in role["groups"]:
                out.append(f"{i}    <h5>{esc(group['heading'])}</h5>")
                out.append(render_list(group.get("bullets", []), i + "    "))
        else:
            out.append(render_list(role.get("bullets", []), i + "    "))
    out.append(f"{i}</div>")
    return "\n".join(out)


def render_project(project, i):
    out = [
        f'{i}<div class="timeline-item">',
        f'{i}    <div class="timeline-header"><h3>{esc(project["name"])}</h3><span>{esc(project.get("timeframe", ""))}</span></div>',
        render_list(project.get("bullets", []), i + "    "),
    ]
    if project.get("link"):
        out.append(f'{i}    <a class="project-link" href="{esc(project["link"])}" target="_blank" rel="noreferrer">View Code</a>')
    out.append(f"{i}</div>")
    return "\n".join(out)


def render_skills(domains, i):
    legend = "".join(
        f'<span class="skill-legend-item" data-domain="{esc(d["id"])}">{esc(d["label"])}</span>' for d in domains
    )
    chips = "".join(
        f'<button type="button" class="skill-chip" data-domain="{esc(d["id"])}">{esc(s)}</button>'
        for d in domains for s in d.get("skills", [])
    )
    return f'\n{i}<div class="skill-legend">{legend}</div>\n{i}<div class="skill-cloud">{chips}</div>\n{i[:-4]}'


def block(items, i):
    return "\n" + "\n".join(items) + "\n" + i[:-4]


def build_homepage(resume):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    i = " " * 16
    text = fill(text, "name", esc(resume["name"]))
    text = fill(text, "location", esc(resume.get("location", "")))
    text = fill(text, "email", esc(resume.get("email", "")))
    text = fill(text, "summary", resume.get("summary", ""))  # trusted HTML, same as app.js
    text = fill(text, "skills", render_skills(resume.get("domains", []), i))
    text = fill(text, "experience", block([render_experience(e, i) for e in resume.get("experience", [])], i))
    text = fill(text, "founder", block([render_experience(e, i) for e in resume.get("founder_projects", [])], i))
    text = fill(text, "projects", block([render_project(p, i) for p in resume.get("projects", [])], i))
    text = fill(text, "education", block([
        f'{i}<div class="education-card"><h3>{esc(e["degree"])}</h3><p>{esc(e["institution"])}</p><span>{esc(e["timeframe"])}</span></div>'
        for e in resume.get("education", [])
    ], i))
    write(path, text)
    return text


# ---------- blog index ----------

def build_blog_index(posts):
    path = ROOT / "blog" / "index.html"
    i = " " * 16
    cards = []
    for post in sorted(posts, key=lambda p: p["date"], reverse=True):
        cover = (
            f'<img class="blog-card-cover" src="../blogs/images/{esc(post["cover"])}" alt="{esc(post["title"])}">'
            if post.get("cover") else ""
        )
        tags = "".join(f'<span class="blog-card-tag">{esc(t)}</span>' for t in post.get("tags", []))
        cards.append(
            f'{i}<a class="blog-card" href="{esc(post_file(post))}">{cover}<div class="blog-card-body">'
            f'<div class="blog-card-meta"><span>{fmt_date(post["date"])}</span><span>{esc(post.get("readTime", ""))}</span></div>'
            f'<div class="blog-card-title">{esc(post["title"])}</div>'
            f'<p class="blog-card-summary">{esc(post["summary"])}</p>'
            f'<div class="blog-card-tags">{tags}</div></div></a>'
        )
    write(path, fill(path.read_text(encoding="utf-8"), "posts", block(cards, i)))


# ---------- sitemap, robots, llms.txt ----------

def build_crawl_files(posts, resume, homepage):
    newest = max(p["date"] for p in posts)
    entries = [(f"{SITE}/", newest), (f"{SITE}/blog/", newest)]
    entries += [(post_url(p), p["date"]) for p in sorted(posts, key=lambda p: p["date"], reverse=True)]
    urls = "\n".join(f"  <url><loc>{esc(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in entries)
    write(ROOT / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')

    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    description = re.search(r'<meta name="description" content="([^"]*)"', homepage).group(1)
    lines = [
        f"# {resume['name']}",
        "",
        f"> {html.unescape(description)}",
        "",
        f"{resume.get('title', '')}, {resume.get('location', '')}.",
        "",
        f"- Machine-readable CV: {SITE}/resume.json",
        f"- Portfolio: {SITE}/",
        f"- LinkedIn: {resume['links']['linkedin']}",
        f"- GitHub: {resume['links']['github']}",
        "",
        "## Posts",
        "",
    ]
    lines += [
        f"- [{p['title']}]({post_url(p)}): {p['summary']}"
        for p in sorted(posts, key=lambda p: p["date"], reverse=True)
    ]
    write(ROOT / "llms.txt", "\n".join(lines) + "\n")


def main():
    blogs_path = ROOT / "blogs" / "blogs.json"
    posts = read_json(blogs_path)
    resume = read_json(ROOT / "resume.json")

    built = build_posts(posts)
    write(blogs_path, json.dumps(posts, ensure_ascii=False, indent=2) + "\n")
    build_redirects(posts)
    homepage = build_homepage(resume)
    build_blog_index(posts)
    build_crawl_files(posts, resume, homepage)
    print(f"Built {len(built)} posts: {', '.join(built)}")


if __name__ == "__main__":
    main()
