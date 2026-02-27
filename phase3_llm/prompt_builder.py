"""
Prompt builder: filtered restaurant list is the single source of truth for the LLM.

The LLM receives only the filtered dataset (no other restaurant source).
It is forbidden to add or invent restaurants; only names from the list may appear.
"""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are a summarization assistant for restaurant search results. You will receive the complete filtered dataset—the only restaurants that matched the user's search. Your task is to write a short (2-4 sentence) friendly summary that highlights 2-3 restaurants from this list.

Rules (strict):
- The list below is the SINGLE SOURCE OF TRUTH. You may only mention restaurants that appear in that list, using their exact names.
- It is FORBIDDEN to add, invent, or reference any restaurant not in the list.
- Do not recommend or describe any place that is not in the list.
- When the user has selected a cuisine filter, your summary must reflect ONLY that cuisine. Do not mention or emphasize other cuisines, unrelated dish types (e.g. sweets/desserts if they did not select that), or dishes that do not belong to the user's selected cuisine. Describe each restaurant only in terms that match the user's selected filters.
- Use a warm, conversational tone. You may acknowledge the user's search in one sentence (e.g. "Based on your search...") but every restaurant name and every cuisine/dish you mention must align with the user's selected filters and the data in the list."""


def _format_restaurant(r: dict[str, Any], index: int) -> str:
    """Format one restaurant for the prompt."""
    name = r.get("name") or "Unknown"
    location = r.get("location") or ""
    rate = r.get("rate")
    cost = r.get("cost_for_two")
    cuisines = r.get("cuisines") or ""
    dish_liked = r.get("dish_liked") or ""
    rest_type = r.get("rest_type") or ""
    parts = [f"{index}. {name}"]
    if location:
        parts.append(f"   Location: {location}")
    if rate is not None:
        parts.append(f"   Rating: {rate}/5")
    if cost is not None:
        parts.append(f"   Cost for two: ₹{cost}")
    if cuisines:
        parts.append(f"   Cuisines: {cuisines}")
    if rest_type:
        parts.append(f"   Type: {rest_type}")
    if dish_liked:
        parts.append(f"   Popular dishes: {dish_liked}")
    return "\n".join(parts)


def _format_preferences(preferences: dict[str, Any]) -> str:
    """Format user preferences for the prompt."""
    parts = []
    if preferences.get("location"):
        parts.append(f"Location: {preferences['location']}")
    if preferences.get("min_rating") is not None:
        parts.append(f"Minimum rating: {preferences['min_rating']}/5")
    if preferences.get("min_cost") is not None:
        parts.append(f"Minimum cost for two: ₹{preferences['min_cost']}")
    if preferences.get("max_cost") is not None:
        parts.append(f"Maximum cost for two: ₹{preferences['max_cost']}")
    if preferences.get("cuisines"):
        cuisines = preferences["cuisines"]
        if isinstance(cuisines, list):
            parts.append(f"Cuisines: {', '.join(cuisines)}")
        else:
            parts.append(f"Cuisines: {cuisines}")
    if preferences.get("rest_type"):
        parts.append(f"Restaurant type: {preferences['rest_type']}")
    if not parts:
        return "No specific preferences (showing matching restaurants)."
    return " | ".join(parts)


def build_messages(
    restaurants: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Build messages for Groq. Only the filtered restaurant list is the source of truth.
    Preferences are used only for a one-line context; the LLM must not add or invent restaurants.
    """
    if not restaurants:
        user_content = "The user has no matching restaurants. Reply with a single short sentence suggesting they try relaxing their filters (e.g. location or budget)."
    else:
        context_line = _format_preferences(preferences)
        restaurant_lines = [_format_restaurant(r, i + 1) for i, r in enumerate(restaurants)]
        cuisine_instruction = ""
        if preferences.get("cuisines"):
            cuisines = preferences["cuisines"]
            cuisines_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
            cuisine_instruction = f"\nThe user selected cuisine(s): {cuisines_str}. In your summary, mention only dishes and offerings that match this selection. Do not highlight other cuisines (e.g. do not mention Chinese or Indonesian dishes if the user selected Thai), and do not add unrelated categories like sweets or desserts unless they match the filter.\n"
        user_content = f"""Context (user's selected filters): {context_line}.{cuisine_instruction}

The following is the complete filtered result set. These are the ONLY restaurants you may mention. Summarize and recommend only from this list—do not add or invent any name.

{chr(10).join(restaurant_lines)}

Write a short summary (2-4 sentences) highlighting 2-3 restaurants from the list above. Use only the exact names and details shown. Do not mention any other restaurant. Every cuisine or dish you mention must match the user's selected filters (e.g. if they chose Thai, describe only Thai-relevant offerings)."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
