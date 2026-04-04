# Blog Writing Guide

## Structure

Every blog post follows this structure:

1. **TL;DR** Context and result in 2 to 3 sentences. For people who skim.
2. **The Problem** What was the situation, what were the constraints, what made it hard. Set the stakes.
3. **The Approach** Step by step, with detail. Sub sections per step. Explain why each decision was made, not just what was done. Include code snippets where relevant.
4. **The Result** Numbers, before/after, what it enabled. Keep it concrete.
5. **What I Learned** Specific lessons, not generic advice. Things that surprised, things that would be done differently, mental models that changed.
6. **Tags** Skill tags at the bottom, matching the tag names used in resume.json and blogs.json.

## Style rules

- No dashes (em dashes, en dashes). Use commas, periods, or restructure the sentence.
- Write in first person. This is Hiwa's voice, not a corporate blog.
- Keep the author's natural language. Polish for clarity but don't make it sound like someone else wrote it.
- Be direct. Lead with the point, not the buildup.
- No filler. If a sentence doesn't add information, cut it.
- Use bold for emphasis sparingly. Not every other sentence.
- Use bullet points as standalone bold statements followed by explanation, not as dash prefixed lists.
- Code snippets are welcome when they make the explanation concrete.
- The "What I Learned" section should have real depth. Not one paragraph. Multiple sub sections with specific, non obvious takeaways.

## Tone

- Technical but conversational. Like explaining to a smart colleague over coffee.
- Honest about what worked and what didn't.
- No buzzwords. If you write "leverage" or "synergy" you've gone wrong.
- Confidence without arrogance. Show the thinking, show the doubt, show the result.

## File conventions

- Blog posts go in `blogs/posts/` as markdown files.
- File name is the slug: `my-blog-post-title.md`
- Every post must have a corresponding entry in `blogs/blogs.json` with: slug, title, date, summary, tags, readTime, cover.
- Tags must match skill names from `resume.json` exactly. This is how blog posts link to portfolio skills.

## Images

- All images go in `blogs/images/`.
- In markdown, reference images by filename only: `![description](my-image.png)`. The blog renderer automatically resolves the path.
- Cover images are optional. Set `"cover": "filename.png"` in blogs.json, or `null` for no cover.
- Supported formats: PNG, JPG, WebP, SVG.

## HTML pages

- `blog/index.html` is the blog listing page. Supports `?tag=SkillName` to filter posts by tag.
- `blog/post.html` is the single post template. Loads markdown and renders it. Supports `?slug=post-slug`.
- Clicking a tag on a post navigates to the listing filtered by that tag.
- On the portfolio, skill tags can link to `/blog/?tag=SkillName` to show related blog posts.

## Example blogs.json entry

```json
{
  "slug": "ai-column-matching-pipeline",
  "title": "How I Automated SAS-to-Snowflake Column Matching with AI",
  "date": "2026-04-04",
  "summary": "Short description of the post for the blog listing page.",
  "tags": ["LLM API chaining", "SAS", "Snowflake"],
  "readTime": "8 min",
  "cover": "column-matching-cover.png"
}
```
