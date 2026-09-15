# Journal → Substack → Social (J2S)

Turns a raw journal entry into a polished Substack article, a matching header
image, and platform-tuned social captions for X, Threads, LinkedIn, Alignable,
YouTube, and TikTok — with a human-in-the-loop review step by email, and
pre-filled share links so publishing is a click-and-paste, not a retype.

## Why this exists

Most "content repurposing" tools either auto-post everywhere and remove the
author's judgment from the loop, or are paid SaaS with no source available.
This project does neither: it drafts, the user chooses, and it hands back
ready-to-paste text plus pre-filled links. **It never posts on anyone's
behalf on any platform** — every publish action is a deliberate click or
paste by a human. This is an auto-*fill* tool, not an auto-*post* tool, by
design.

**Why not n8n or a full autonomous agent:** this pipeline uses direct,
single-purpose API calls at each defined step rather than an agent or
workflow orchestrator that reasons continuously, polls, and re-checks its own
state. Fewer, well-scoped calls mean lower cost and lower compute draw than a
standing agent loop — a deliberate tradeoff of a little manual triggering
(clicking "generate," clicking "finalize") for meaningfully less energy and
API spend per article.

## Pipeline

```
Journal entry (Streamlit textarea)
        │
        ▼
1. Draft — LLM generates 3 article variations (different angle/tone each)
        │
        ▼
2. Review — all 3 are emailed for review (and shown in-app)
        │
        ▼
3. A winner is chosen in the Streamlit app
        │
        ▼
4. Finalize:
     - generates several image prompt options → one is picked → image is generated
     - generates platform-tuned social captions (X, Threads, LinkedIn, Alignable,
       YouTube description, TikTok caption)
     - builds a pre-filled share/intent link for every platform, where the
       platform's own posting page supports it
        │
        ▼
5. Delivery — final email with:
     - the finished Substack article, ready to paste into the Substack editor
     - the header image (attached)
     - each platform's caption, ready to copy
     - a pre-filled link per platform that opens that platform's own posting
       page — logged-in sessions on the local machine mean it's usually just
       one paste and one click away from live
```

## Why every platform here is "auto-fill," not "auto-post"

Being upfront about this, because it shapes the whole design. Posting
permissions vary a lot by platform, and several don't expose a public posting
API at all:

| Platform  | What's possible via API today |
|-----------|-------------------------------|
| X         | Has a real posting API, but this project only uses its public share-intent URL to pre-fill a draft — no credentials required, nothing is submitted automatically |
| Threads   | Same approach: a share-intent URL pre-fills a draft on Meta's own composer |
| LinkedIn  | Posting APIs require an approved partner app, which isn't available to individual developers; a share-offsite link pre-fills the article URL, and the caption is supplied separately to paste in |
| Substack  | No public API; the article is generated and delivered for pasting into the Substack editor |
| Alignable | No public API; the link opens the posting page and the caption is supplied to paste in |
| YouTube   | The Data API supports uploads, but this project treats it the same as the others — a link to Studio plus a caption to paste, since most journal-to-article content isn't video |
| TikTok    | The Content Posting API is video-first and requires app review; out of scope here — a link to the upload page plus a caption to paste |

Treating every platform the same way (generate content, provide a link,
require a human click to actually publish) keeps the tool's behavior
predictable and auditable, and avoids taking on API review processes or
credential scope creep for platforms that don't need them.

## Stack

- **Streamlit** — the interface (journal input, draft review, final delivery view)
- **Python** — orchestration
- **LLM API** — Anthropic Claude or OpenAI, configurable, for article and caption drafting
- **Image API** — OpenAI Images, Stability, or Gemini image-gen, configurable
- **SMTP** — for the review and delivery emails; any SMTP provider works (Hostinger email, Gmail app password, etc.)

## Setup

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in the relevant keys (see below)
4. `streamlit run app/main.py`

## Environment variables (`.env`)

```
LLM_PROVIDER=anthropic            # or openai
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

IMAGE_PROVIDER=openai             # or stability, gemini
STABILITY_API_KEY=
GEMINI_API_KEY=

SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_USER=your_email@example.com
SMTP_PASS=
NOTIFY_EMAIL=your_email@example.com   # where drafts and finals get sent

SUBSTACK_URL=https://example.substack.com
LINKEDIN_PROFILE_URL=
ALIGNABLE_PROFILE_URL=
YOUTUBE_STUDIO_URL=https://studio.youtube.com/
TIKTOK_UPLOAD_URL=https://www.tiktok.com/upload
```

No platform-posting credentials are required for any platform — every link
generated is a public share-intent or posting-page URL, not an authenticated
API call.

## Repo layout

```
app/
  main.py              # Streamlit entrypoint; journal input, draft review,
                        # and finalize/delivery all live here as session-state steps
core/
  llm.py                # provider-agnostic article/caption generation
  image_gen.py           # provider-agnostic image generation
  email_client.py         # SMTP send for the review and delivery emails
  share_links.py           # builds pre-filled share/posting links per platform
.streamlit/
  config.toml
.env.example
requirements.txt
```

## Hosting

This is a small, always-on Python process — it needs somewhere that keeps a
process running, not typical shared/static hosting. Common options:

- A small VPS: `pip install -r requirements.txt && streamlit run app/main.py --server.port 8501`, then reverse-proxy the port through the host's existing web server config
- Run it locally on demand, only spinning it up while journaling
- Streamlit Community Cloud (free tier) for a public-facing demo version, using placeholder/demo keys rather than real credentials

## Contributing

Issues and PRs are welcome. Useful directions to extend this:

- Splitting `app/main.py` into a proper Streamlit multi-page layout as the flow grows
- Adding reply-by-email selection (parsing a reply like "2" to pick a draft) as an alternative to choosing in-app
- Additional LLM or image-generation providers
- Platform-specific caption tuning improvements

## Roadmap / open items

- [ ] Reply-to-email draft selection, as an alternative to in-app selection
- [ ] Multi-page Streamlit layout as the flow grows
- [ ] Optional local caching of generated drafts/images between sessions
