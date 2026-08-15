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
You are an information extraction system for
Philippine class suspension announcements.

Your task is to identify geographic areas that are
EXPLICITLY stated in the article as having classes
suspended.

IMPORTANT RULES:

1. Do NOT infer municipalities.

2. Do NOT assume that an entire province is suspended
   unless the article explicitly says so.

3. If the article says:
   "all of Bulacan"

   return:

   location = "Bulacan"
   scope = "province"

4. If the article says:
   "Metro Manila"

   return:

   location = "Metro Manila"
   scope = "region"

5. If the article explicitly names a municipality,
   return:

   scope = "municipality"

6. If the article explicitly names a city,
   return:

   scope = "city"

7. If the article explicitly names a province,
   return:

   scope = "province"

8. If the article explicitly says classes are
   suspended nationwide, return:

   location = "Philippines"
   scope = "nationwide"

9. Ignore schools and universities unless the
   suspension explicitly applies to the geographic
   area itself.

10. Ignore locations that are merely mentioned
    as context.

11. Ignore locations where classes are merely being
    considered, threatened, requested, recommended,
    or discussed.

12. Only return actual class suspensions.

13. Do not infer that neighboring municipalities
    are suspended.

14. Do not infer that all municipalities within a
    province are suspended unless the article
    explicitly states that the province is suspended.

15. If the article contains both a broad geographic
    suspension and specific municipalities, return
    both.

16. Preserve the location name as written in the
    article whenever possible.

17. EVERY suspension MUST include evidence.

18. The evidence MUST be copied directly from the
    article.

19. Do NOT write an explanation in the evidence field.

20. Keep the evidence short. Include only the sentence
    or relevant portion of the article that explicitly
    supports the suspension.

21. If there is no explicit evidence that a location
    is suspended, DO NOT return that location.

22. The evidence must support BOTH the location and
    the suspension status.

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