"""
core/generator.py
------------------
This is your ORIGINAL app.py logic, unchanged in spirit: the same LCEL
chain (prompt | llm | StrOutputParser()) calling Gemini. It's just been
moved out of the single script and extended with the extra fields your
minor project brief asked for (title, genre, speakers, language, extra
instructions), plus it now returns plain text instead of writing
directly to the Streamlit page, so it can be reused from the Generate
Script page and saved to the database.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

MODEL_OPTIONS = ["gemini-3.5-flash-lite", "gemini-3.5-pro"]

PROMPT = ChatPromptTemplate.from_template("""
You are an expert podcast scriptwriter and show producer.

Write a complete, ready-to-record podcast script based on the details below.

Podcast Title: {title}
Topic: {topic}
Genre/Category: {category}
Target Audience: {audience}
Tone: {tone}
Target Length: {duration} minutes
Number of Speakers: {num_speakers}
Speaker Names: {speaker_names}
Language: {language}
Additional Instructions: {additional_instructions}

Structure the output in Markdown with these sections, in this order:

## {title}

## Introduction
Opening hook and welcome, introducing the speaker(s) and the topic.

## Main Discussion
The core content, broken into clearly labeled segments, written as
natural spoken dialogue matching the {tone} tone, using the speaker
names given above (e.g. "Host:", "Guest:", or the actual names) with
rough time markers that add up to about {duration} minutes total.

## Conclusion
Recap, key takeaways, call to action, and sign-off.

Write in {language}. Keep the language natural and easy to read aloud.
""")


def generate_script(api_key: str, model: str, *, title, topic, category,
                     audience, tone, duration, num_speakers, speaker_names,
                     language, additional_instructions):
    """Calls Gemini via the LCEL chain and returns the generated script text.
    Raises whatever exception the underlying call raises — the caller
    decides how to show/handle it (and, importantly, whether to deduct a
    credit: only on success)."""

    llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
    chain = PROMPT | llm | StrOutputParser()

    return chain.invoke({
        "title": title or "Untitled Episode",
        "topic": topic,
        "category": category,
        "audience": audience,
        "tone": tone,
        "duration": duration,
        "num_speakers": num_speakers,
        "speaker_names": speaker_names or "Host, Guest",
        "language": language,
        "additional_instructions": additional_instructions or "None",
    })
