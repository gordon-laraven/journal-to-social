"""Builds pre-filled share/intent links per platform, the same trick Substack's
own 'share to X' button uses. This module never posts anything — it only ever
constructs a URL that opens a platform's own posting page with as much of the
content pre-filled as that platform allows. Nothing here submits a post; the
human always makes the final click.

Some platforms (X, Threads) support a real share-intent scheme that pre-fills
the post text itself. Others (LinkedIn) only allow the link to be pre-filled,
not the caption text, due to platform restrictions. Others still (Substack,
Alignable, YouTube, TikTok) have no share-intent scheme at all, so the link
just opens the relevant posting/upload page and the generated caption is
supplied separately to paste in by hand.
"""
from urllib.parse import quote


def build_share_links(article_url: str, article_title: str, captions: dict,
                       linkedin_profile_url: str = "",
                       alignable_profile_url: str = "",
                       youtube_studio_url: str = "https://studio.youtube.com/",
                       tiktok_upload_url: str = "https://www.tiktok.com/upload") -> dict:
    """captions: dict of platform name -> generated caption text, e.g.
    {"X": "...", "Threads": "...", "LinkedIn": "...", "Alignable": "...",
     "YouTube description": "...", "TikTok": "..."}

    Returns a dict of platform -> {"link": url_to_open, "caption_to_paste": text}.
    """
    links = {}

    # X — real web intent, pre-fills text + link
    x_text = f"{captions.get('X', '')}\n\n{article_url}"
    links["X"] = {
        "link": f"https://twitter.com/intent/tweet?text={quote(x_text)}",
        "caption_to_paste": None,  # already included in the link itself
    }

    # Threads — supported web intent, pre-fills text + link
    threads_text = f"{captions.get('Threads', '')}\n\n{article_url}"
    links["Threads"] = {
        "link": f"https://www.threads.net/intent/post?text={quote(threads_text)}",
        "caption_to_paste": None,
    }

    # LinkedIn — the 'share-offsite' intent pre-fills the link only; LinkedIn
    # does not allow pre-filling the post body via URL, so the caption is
    # supplied separately to paste in once the composer opens
    links["LinkedIn"] = {
        "link": linkedin_profile_url
        or f"https://www.linkedin.com/sharing/share-offsite/?url={quote(article_url)}",
        "caption_to_paste": captions.get("LinkedIn", ""),
    }

    # Alignable — no share-intent scheme; link opens the posting page directly
    links["Alignable"] = {
        "link": alignable_profile_url or "https://www.alignable.com/",
        "caption_to_paste": captions.get("Alignable", ""),
    }

    # YouTube — no text/description pre-fill via URL; link opens Studio
    links["YouTube"] = {
        "link": youtube_studio_url,
        "caption_to_paste": captions.get("YouTube description", ""),
    }

    # TikTok — no caption pre-fill via URL; link opens the upload page
    links["TikTok"] = {
        "link": tiktok_upload_url,
        "caption_to_paste": captions.get("TikTok", ""),
    }

    # Universal fallback — opens the default mail client with a pre-filled
    # draft, useful for any platform not explicitly covered above
    mailto_subject = quote(f"New post: {article_title}")
    mailto_body = quote(f"{captions.get('X', '')}\n\n{article_url}")
    links["Email_share"] = {
        "link": f"mailto:?subject={mailto_subject}&body={mailto_body}",
        "caption_to_paste": None,
    }

    return links
