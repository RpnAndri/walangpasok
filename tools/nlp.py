import os
from typing import Literal

from google import genai
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()


# =========================================
# Models
# =========================================

class Suspension(BaseModel):
    location: str

    scope: Literal[
        "municipality",
        "city",
        "province",
        "region",
        "nationwide",
    ]

    province: str | None = None

    status: Literal[
        "suspended",
        "not_suspended",
        "unknown",
    ]

    evidence: str


class SuspensionExtraction(BaseModel):
    suspensions: list[Suspension]


# =========================================
# Gemini client
# =========================================

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# =========================================
# NLP extraction
# =========================================

async def extract_suspensions(
    article_text: str,
) -> SuspensionExtraction:
    """
    Extract explicit geographic class suspension
    announcements from a Philippine news article.

    The model MUST NOT infer locations.

    Each extraction must include evidence from
    the article supporting the result.
    """

    prompt = f"""
You are extracting class suspension information
from a Philippine news article.

Your task is to identify geographic areas that are
EXPLICITLY stated in the article as having classes suspended.

IMPORTANT RULES:

1. Do NOT infer municipalities.
2. Do NOT assume that an entire province is suspended
   unless the article explicitly says so.
3. If a municipality or city is mentioned, identify its
   province ONLY if the article explicitly provides enough
   context to determine it.
4. If the article has a province heading followed by
   municipalities, use that province for those municipalities.
5. This is extremely important because Philippine
   municipalities/cities can have identical names.

Examples:

Zambales
- Santa Cruz
- San Antonio

means:

Santa Cruz -> province = Zambales
San Antonio -> province = Zambales

6. If the municipality's province cannot be determined
   from the article, set province = null.
7. NEVER guess the province from the municipality name alone.
8. Do NOT use a similarly named municipality from another province.
9. If the article says "all of Bulacan", return:
   location = "Bulacan"
   scope = "province"
10. If the article says "Metro Manila", return:
    location = "Metro Manila"
    scope = "region"
11. If it names a city, return scope = "city".
12. Ignore schools and universities unless the geographic
    area itself is explicitly suspended.
13. Ignore locations merely mentioned as context.
14. Only return actual class suspensions.
15. Do not return locations where classes are merely being
    considered, threatened, or requested.

ARTICLE:

{article_text}
"""

    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": (
                SuspensionExtraction.model_json_schema()
            ),
        },
    )

    return SuspensionExtraction.model_validate_json(
        response.text
    )