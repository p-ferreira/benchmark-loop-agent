"""Retail rules in code (``--rules``): what the model is shown, what is corrected, what is held and asked again.

Off by default. Each rule is fitted to the retail policy, the tools and the kinds of failure seen in recorded
conversations of a cheap model; none reads the task, an expected action or a score. They are pure functions
over the conversation as the agent keeps it (``items``: role, text, calls), so that where each one steps in
can be counted on recorded conversations without a model call.

``address``       address fields of a write call are put in the database's forms ("USA", two-letter state), and a
                  reply that asks the customer for the country is held once.
``products``      the result of ``get_product_details`` is shown as available variants only, cheapest first.
``payment``       an item change or exchange is held once when the customer has several payment methods on file and
                  has named none: the model is told to ask which one takes the price difference.
``handover-once`` the first transfer of a conversation, made before the customer asked for a person, is refused
                  once: the model must say what it cannot do and ask whether there is anything else.
"""

import json
import re
from typing import Any

RULES = ("address", "products", "payment", "handover-once")
HEADER = "Check by the system. This is not a message from the customer, and the customer does not see it."

# --- address ----------------------------------------------------------------------------------

ADDRESS_TOOLS = {"modify_user_address", "modify_pending_order_address"}
COUNTRY_FORMS = {"", "us", "usa", "u.s.", "u.s.a.", "united states", "united states of america", "the united states", "america"}
STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
ASKS_COUNTRY = re.compile(r"\bcountry\b", re.IGNORECASE)
COUNTRY_NOTE = (
    HEADER + " You were about to send this reply: {held}\n"
    "Do not ask the customer for the country: every address in this store is in the USA, so use \"USA\". Do not ask "
    "for the state when the city and ZIP code are given: work out its two-letter form from them. Continue with what "
    "the customer gave you, and ask only for something you still cannot work out.")


def fix_address(call: dict[str, Any]) -> dict[str, Any]:
    """The call with its country and state in the database's forms; the same object when nothing changes."""
    if call["name"] not in ADDRESS_TOOLS:
        return call
    arguments = dict(call["arguments"])
    country, state = arguments.get("country"), arguments.get("state")
    if isinstance(country, str) and country != "USA" and country.strip().lower() in COUNTRY_FORMS:
        arguments["country"] = "USA"
    if isinstance(state, str):
        if state.strip().lower() in STATES:
            arguments["state"] = STATES[state.strip().lower()]
        elif len(state.strip()) == 2 and state != state.strip().upper():
            arguments["state"] = state.strip().upper()
    return call if arguments == call["arguments"] else {**call, "arguments": arguments}


def asks_for_country(text: str, calls: list[dict[str, Any]]) -> bool:
    """A reply to the customer, with no call, that asks about the country."""
    return not calls and bool(text) and bool(ASKS_COUNTRY.search(text)) and not said_country_is_set(text)


def said_country_is_set(text: str) -> bool:
    """The reply states the country (in a summary for confirmation) and does not ask for it."""
    return bool(re.search(r"\b(USA|United States)\b", text))


# --- products ---------------------------------------------------------------------------------

PRODUCT_TOOL = "get_product_details"
PRODUCT_NOTE = "Shown by the system: available variants only, cheapest first. Variants in unavailable_item_ids cannot be ordered."


def product_table(text: str) -> str:
    """The product's details with the available variants sorted by price; the text unchanged when it is not a product."""
    try:
        product = json.loads(text)
        variants = list(product["variants"].values())
        available = sorted((v for v in variants if v["available"]), key=lambda v: (v["price"], v["item_id"]))
        shown = {"name": product["name"], "product_id": product["product_id"], "note": PRODUCT_NOTE,
                 "available_variants_cheapest_first": [{"item_id": v["item_id"], "price": v["price"], "options": v["options"]}
                                                       for v in available],
                 "unavailable_item_ids": sorted(v["item_id"] for v in variants if not v["available"])}
    except (ValueError, KeyError, TypeError, AttributeError):
        return text
    return json.dumps(shown)


def shown_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """``items`` as the model is shown them: product results as the table."""
    product_calls = {call["id"] for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] == PRODUCT_TOOL}
    return [{**item, "text": product_table(item["text"])} if item["role"] == "tool" and item["id"] in product_calls else item
            for item in items]


# --- payment ----------------------------------------------------------------------------------

ITEM_CHANGES = {"modify_pending_order_items", "exchange_delivered_order_items"}
USER_TOOL = "get_user_details"
NAMES_A_PAYMENT = re.compile(r"paypal|credit card|gift card|\bcard\b|original (payment|method)|same (payment|method|card)|payment method",
                             re.IGNORECASE)
PAYMENT_NOTE = (
    HEADER + " You were about to make this call: {held}\n"
    "The policy says the customer must provide the payment method that pays or receives the price difference. This "
    "customer has more than one payment method on file and has not named one in this conversation. Do not make the "
    "call yet: ask the customer which payment method to use for the price difference, naming the ones on file, and "
    "make the call with their answer.")


def payment_methods_on_file(items: list[dict[str, Any]]) -> int:
    """How many payment methods the customer's details showed, from the last ``get_user_details`` result; 0 when none was read."""
    user_calls = {call["id"] for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] == USER_TOOL}
    for item in reversed(items):
        if item["role"] == "tool" and item["id"] in user_calls:
            try:
                return len(json.loads(item["text"])["payment_methods"])
            except (ValueError, KeyError, TypeError):
                return 0
    return 0


def payment_not_chosen(items: list[dict[str, Any]], calls: list[dict[str, Any]]) -> str | None:
    """The note, when this reply changes or exchanges items and the customer, with several methods on file, named none."""
    change = next((call for call in calls if call["name"] in ITEM_CHANGES), None)
    if change is None or payment_methods_on_file(items) < 2:
        return None
    if any(item["role"] == "user" and NAMES_A_PAYMENT.search(item["text"]) for item in items):
        return None
    return PAYMENT_NOTE.format(held=json.dumps({"name": change["name"], "arguments": change["arguments"]}, ensure_ascii=False))


# --- handover-once ----------------------------------------------------------------------------

HANDOVER_TOOL = "transfer_to_human_agents"
HANDOVER_ONCE_NOTE = (
    HEADER + " You were about to transfer the customer to a human agent. A transfer ends the conversation, and the "
    "customer may have other requests you can handle. Do not transfer in this reply. Tell the customer plainly what "
    "you cannot do and why, answer anything they asked that the tool results above answer, and ask whether there is "
    "anything else you can help with. If the customer then still needs something outside your tools, you can transfer.")


def first_early_transfer(items: list[dict[str, Any]], calls: list[dict[str, Any]], asked_for_a_person: bool) -> bool:
    """This reply makes the conversation's first transfer, and the customer has not asked for a person."""
    if asked_for_a_person or not any(call["name"] == HANDOVER_TOOL for call in calls):
        return False
    return not any(call["name"] == HANDOVER_TOOL for item in items if item["role"] == "assistant" for call in item["calls"])
