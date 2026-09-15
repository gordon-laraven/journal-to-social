import os
import sys
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.llm import generate_article_variations, generate_caption, generate_image_prompt_options
from core.image_gen import generate_image
from core.share_links import build_share_links
from core.email_client import send_review_email, send_final_email

st.set_page_config(page_title="Journal → Social", layout="wide")
st.title("Journal → Substack → Social")

if "step" not in st.session_state:
    st.session_state.step = "draft"

# ---------- Step 1: Draft ----------
if st.session_state.step == "draft":
    st.header("1. Drop your journal entry")
    entry = st.text_area("Raw journal entry", height=300)
    if st.button("Generate 3 article drafts", type="primary", disabled=not entry.strip()):
        with st.spinner("Drafting..."):
            variations = generate_article_variations(entry)
            st.session_state.variations = variations
            send_review_email(variations)
        st.session_state.step = "review"
        st.rerun()

# ---------- Step 2: Review & choose ----------
elif st.session_state.step == "review":
    st.header("2. Pick your favorite")
    st.caption("Also sent to your email if you'd rather review there.")
    variations = st.session_state.variations
    cols = st.columns(len(variations))
    for i, (col, v) in enumerate(zip(cols, variations)):
        with col:
            st.subheader(v["title"])
            st.caption(v["angle"])
            st.markdown(v["body_markdown"][:600] + "...")
            if st.button(f"Choose option {i + 1}", key=f"choose_{i}"):
                st.session_state.chosen = v
                st.session_state.step = "finalize"
                st.rerun()

# ---------- Step 3: Image + captions + share links ----------
elif st.session_state.step == "finalize":
    chosen = st.session_state.chosen
    st.header("3. Image, captions, and share links")
    st.subheader(chosen["title"])

    if "image_prompts" not in st.session_state:
        summary = chosen["body_markdown"][:400]
        st.session_state.image_prompts = generate_image_prompt_options(chosen["title"], summary)

    st.write("Pick an image concept:")
    prompt_choice = st.radio("Image prompt options", st.session_state.image_prompts)

    article_url = st.text_input(
        "Article URL (paste once you've published on Substack, or leave the base URL for now)",
        value=os.getenv("SUBSTACK_URL", ""),
    )

    if st.button("Generate image + captions + finalize", type="primary"):
        with st.spinner("Generating image and captions..."):
            image_bytes = generate_image(prompt_choice)
            summary = chosen["body_markdown"][:400]
            captions = {
                "X": generate_caption("X", chosen["title"], summary),
                "Threads": generate_caption("Threads", chosen["title"], summary),
                "LinkedIn": generate_caption("LinkedIn", chosen["title"], summary),
                "Alignable": generate_caption("Alignable", chosen["title"], summary),
                "YouTube description": generate_caption("YouTube", chosen["title"], summary),
                "TikTok": generate_caption("TikTok", chosen["title"], summary),
            }
            links = build_share_links(
                article_url=article_url,
                article_title=chosen["title"],
                captions=captions,
                linkedin_profile_url=os.getenv("LINKEDIN_PROFILE_URL", ""),
                alignable_profile_url=os.getenv("ALIGNABLE_PROFILE_URL", ""),
                youtube_studio_url=os.getenv("YOUTUBE_STUDIO_URL", "https://studio.youtube.com/"),
                tiktok_upload_url=os.getenv("TIKTOK_UPLOAD_URL", "https://www.tiktok.com/upload"),
            )
            send_final_email(chosen["title"], chosen["body_markdown"], image_bytes,
                              captions, links, article_url)
            st.session_state.image_bytes = image_bytes
            st.session_state.captions = captions
            st.session_state.links = links
        st.success("Sent to your email — check your inbox for the full package.")
        st.image(image_bytes, caption="Header image")
        for platform, text in captions.items():
            st.text_area(platform, text)
        for platform, info in links.items():
            st.markdown(f"[{platform} — open pre-filled]({info['link']})")
            if info.get("caption_to_paste"):
                st.caption(f"Paste this caption once it opens: {info['caption_to_paste']}")

    if st.button("Start a new entry"):
        for key in ["step", "variations", "chosen", "image_prompts", "image_bytes", "captions", "links"]:
            st.session_state.pop(key, None)
        st.session_state.step = "draft"
        st.rerun()
