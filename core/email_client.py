"""SMTP sending for the review email (3 draft variations) and the final
delivery email (chosen article + image + captions + share links)."""
import os
import smtplib
from email.message import EmailMessage


def _smtp_send(subject: str, html_body: str, attachments: list[tuple[str, bytes]] = None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["NOTIFY_EMAIL"]
    msg.set_content("This email requires an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    for filename, data in (attachments or []):
        msg.add_attachment(data, maintype="image", subtype="png", filename=filename)

    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 465))) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def send_review_email(variations: list[dict]):
    """variations: list of {"angle", "title", "body_markdown"} — sends all 3 for review."""
    sections = ""
    for i, v in enumerate(variations, 1):
        sections += (
            f"<h2>Option {i}: {v['title']}</h2>"
            f"<p><em>Angle: {v['angle']}</em></p>"
            f"<div>{v['body_markdown'].replace(chr(10), '<br>')}</div><hr>"
        )
    html = f"<h1>Three drafts ready for review</h1>{sections}" \
           "<p>Pick your favorite in the Streamlit app to continue to image + captions.</p>"
    _smtp_send("Your 3 article drafts are ready", html)


def send_final_email(article_title: str, article_body_markdown: str, image_bytes: bytes,
                      captions: dict, share_links: dict, article_url: str):
    caption_html = "".join(
        f"<h3>{platform}</h3><p>{text}</p>" for platform, text in captions.items()
    )
    # share_links: platform -> {"link": url, "caption_to_paste": text_or_None}
    link_html = ""
    for platform, info in share_links.items():
        link_html += f'<p><a href="{info["link"]}">{platform} — open pre-filled</a>'
        if info.get("caption_to_paste"):
            link_html += f'<br><em>Paste this caption once it opens:</em><br>{info["caption_to_paste"]}'
        link_html += "</p>"
    html = (
        f"<h1>{article_title}</h1>"
        f"<p>Substack article body below — paste into the Substack editor.</p>"
        f"<div>{article_body_markdown.replace(chr(10), '<br>')}</div>"
        f"<h2>Image</h2><p>Attached — upload as your Substack header image.</p>"
        f"<h2>Social captions</h2>{caption_html}"
        f"<h2>Pre-filled share links</h2>{link_html}"
        f"<p>Article URL used for links: {article_url}</p>"
    )
    _smtp_send(f"Ready to publish: {article_title}", html,
               attachments=[("header_image.png", image_bytes)])
