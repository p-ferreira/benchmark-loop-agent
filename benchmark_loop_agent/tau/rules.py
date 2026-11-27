"""Retail rules in code (``--rules``): code builds the offer, checks a change before it runs, and refuses one early transfer.

Off by default. The rules are fitted to the retail policy, the tools and the kinds of failure seen in recorded
conversations of a cheap model; none reads the task, an expected action or a score. They are pure functions
over the conversation as the agent keeps it (``items``: role, text, calls; tool results by call id), so that
they can be run on recorded conversations.

``offers``        the model no longer reads a product's variants itself. ``get_product_details`` is shown as a
                  summary without the variants, and a tool of the agent's own, ``find_replacement_items``, searches
                  them in code: availability, the options the customer requires, prices and price differences,
                  cheapest first. A change or exchange to an item that no search returned, or of an item for itself,
                  is held.
``order-lock``    an item change of a pending order is held once when the customer spoke of a delivery address and
                  that order's address was not changed: the item change locks the order.
``payment``       an item change or exchange is held once when the customer has several payment methods on file and
                  has named none: the model is told to ask which one takes the price difference.
``address``       address fields of a write call are put in the database's forms ("USA", two-letter state); a reply that
                  asks the customer for the state or country is held with the state looked up from the ZIP code.
``handover-once`` the first transfer made before the customer asked for a person is refused, once in a conversation:
                  the model must say what it cannot do and ask whether there is anything else.
"""

import json
import re
from typing import Any

RULES = ("offers", "order-lock", "payment", "address", "handover-once")
HEADER = "Check by the system. This is not a message from the customer, and the customer does not see it."
Items = list[dict[str, Any]]
Calls = list[dict[str, Any]]


def results_of(items: Items, tool: str) -> list[tuple[dict[str, Any], str]]:
    """Each call to ``tool`` so far with the text of its result, in order."""
    calls = {call["id"]: call for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] == tool}
    return [(calls[item["id"]], item["text"]) for item in items if item["role"] == "tool" and item["id"] in calls]


def _json(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return None


def _held(call: dict[str, Any]) -> str:
    return json.dumps({"name": call["name"], "arguments": call["arguments"]}, ensure_ascii=False)


# --- offers -----------------------------------------------------------------------------------

PRODUCT_TOOL = "get_product_details"
ORDER_TOOL = "get_order_details"
SEARCH_TOOL = "find_replacement_items"
ITEM_CHANGES = {"modify_pending_order_items", "exchange_delivered_order_items"}
SEARCH_SCHEMA = {"type": "function", "function": {
    "name": SEARCH_TOOL,
    "description": (
        "Search the variants of one product for the items the customer can get, exactly: only items in stock, only items "
        "with every option the customer requires, with each price and the price difference against the customer's current "
        "item, cheapest first. Always use it to choose or price the new item of an item change or an exchange, and to answer "
        "which options or which cheapest item exist; do not work these out yourself. Call get_product_details for the "
        "product first. A change or exchange to an item this search did not return is refused."),
    "parameters": {"type": "object", "required": ["product_id"], "properties": {
        "product_id": {"type": "string", "description": "The product id (not an item id), as in the order's item."},
        "required_options": {"type": "object", "additionalProperties": {"type": "string"},
                             "description": "Only the options the customer requires, by option name, such as {\"color\": \"red\"}. "
                                            "Leave an option out when the customer did not ask for a value of it."},
        "current_item_id": {"type": "string", "description": "The item the customer has now and wants replaced, when there is one: each "
                                                             "returned item then says its price difference against it and in which "
                                                             "options it differs from it."},
        "only_among_item_ids": {"type": "array", "items": {"type": "string"},
                                "description": "When the customer restricts the choice to particular items (for example \"the cheapest "
                                               "among the other ones in my order\", or \"the same as the one I already have\"), their "
                                               "item ids; the search then looks only at these. The result lists the customer's other "
                                               "bought items of the product."}}}}}
SEARCH_REMINDERS = (
    "Present these to the customer as they are; when several items match, say how they differ and let the customer choose, "
    "and do not narrow the choice by options the customer did not state. Before the change: all items of one order that the customer wants changed "
    "go in ONE call; an item change locks a pending order, so change its address or payment method first if the customer "
    "asked for that; ask the customer which payment method takes the price difference unless they already said.")
SUMMARY_NOTE = (f"The variants are not listed here. To choose, compare or price items of this product, call {SEARCH_TOOL}: "
                "it searches the variants exactly.")
UNSEARCHED_NOTE = (
    HEADER + " You were about to make this call: {held}\n"
    "The new item {missing} was not returned by " + SEARCH_TOOL + " in this conversation, so the call is refused. Call "
    + SEARCH_TOOL + " with what the customer requires, tell the customer what it returns, and make the change with an item "
    "it returned once the customer confirms.")
UNSEARCHED_HOLDS = 2


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def products_read(items: Items) -> dict[str, dict[str, Any]]:
    """Each product whose details a tool result returned, by product id (the latest result wins)."""
    products: dict[str, dict[str, Any]] = {}
    for _, text in results_of(items, PRODUCT_TOOL):
        product = _json(text)
        if isinstance(product, dict) and isinstance(product.get("variants"), dict) and "product_id" in product:
            products[str(product["product_id"])] = product
    return products


def product_summary(text: str) -> str:
    """A product result as the model is shown it: no variants, the values each option takes, and where to search."""
    product = _json(text)
    try:
        variants = list(product["variants"].values())
        values: dict[str, list[str]] = {}
        for variant in variants:
            for name, value in variant["options"].items():
                if value not in values.setdefault(name, []):
                    values[name].append(value)
        shown = {"name": product["name"], "product_id": product["product_id"], "note": SUMMARY_NOTE, "option_values": values,
                 "variants_in_stock": sum(1 for v in variants if v["available"]), "variants_in_all": len(variants)}
    except (KeyError, TypeError, AttributeError):
        return text
    return json.dumps(shown)


def shown_items(items: Items) -> Items:
    """``items`` as the model is sent them: product results as the summary."""
    product_calls = {call["id"] for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] == PRODUCT_TOOL}
    return [{**item, "text": product_summary(item["text"])} if item["role"] == "tool" and item["id"] in product_calls else item
            for item in items]


def _purchase_price(items: Items, item_id: str) -> float | None:
    """What the customer paid for ``item_id``, from an order result; ``None`` when no order read holds it."""
    for _, text in reversed(results_of(items, ORDER_TOOL)):
        order = _json(text)
        for line in (order.get("items") or []) if isinstance(order, dict) else []:
            if isinstance(line, dict) and line.get("item_id") == item_id and isinstance(line.get("price"), (int, float)):
                return float(line["price"])
    return None


def _other_purchases(items: Items, product_id: str, current_id: str | None, product: dict[str, Any]) -> list[dict[str, Any]]:
    """The customer's other bought items of this product, from the orders read: for \"the same as my other one\" and \"among my other ones\"."""
    bought: dict[str, dict[str, Any]] = {}
    for _, text in results_of(items, ORDER_TOOL):
        order = _json(text)
        for line in (order.get("items") or []) if isinstance(order, dict) else []:
            if isinstance(line, dict) and str(line.get("product_id")) == product_id and line.get("item_id") != current_id:
                variant = product["variants"].get(str(line.get("item_id")))
                bought[str(line.get("item_id"))] = {"item_id": line.get("item_id"), "in_order": order.get("order_id"), "options": line.get("options"),
                                                  "in_stock_now": bool(variant and variant.get("available")),
                                                  "price_now": variant.get("price") if variant else None}
    return list(bought.values())


def _difference(new: float, old: float | None) -> str | None:
    if old is None:
        return None
    cents = round(new * 100) - round(old * 100)
    if cents == 0:
        return "0.00 (same price)"
    return f"{abs(cents) / 100:.2f} ({'the customer pays this much more' if cents > 0 else 'refunded to the customer'})"


def search(items: Items, arguments: dict[str, Any]) -> str:
    """The result of ``find_replacement_items``: computed from the product result already in the conversation."""
    product_id = str(arguments.get("product_id") or "")
    product = products_read(items).get(product_id)
    if product is None:
        return json.dumps({"error": f"The details of product {product_id or '(none given)'} were not read in this conversation. "
                                    f"Call {PRODUCT_TOOL} with the product id first (a product id, not an item id), then search again."})
    variants = [v for v in product["variants"].values() if isinstance(v, dict) and isinstance(v.get("options"), dict)]
    names = {_norm(name): name for v in variants for name in v["options"]}
    required = arguments.get("required_options") or {}
    if not isinstance(required, dict):
        return json.dumps({"error": "required_options must be an object of option name to value."})
    unknown = [name for name in required if _norm(name) not in names]
    if unknown:
        return json.dumps({"error": f"This product has no option named {', '.join(map(str, unknown))}.", "option_names": sorted(names.values())})
    wanted = {names[_norm(name)]: _norm(value) for name, value in required.items()}
    current_id = arguments.get("current_item_id")
    current = product["variants"].get(str(current_id)) if current_id else None
    if current_id and current is None:
        return json.dumps({"error": f"Item {current_id} is not a variant of product {product_id}. Check the item id and the product id "
                                    "in the order."})
    among = arguments.get("only_among_item_ids")
    among = {str(i) for i in among} if isinstance(among, list) and among else None
    pool = variants if among is None else [v for v in variants if v.get("item_id") in among]
    old = None
    if current is not None:
        paid = _purchase_price(items, str(current_id))
        old = paid if paid is not None else float(current["price"])

    def row(variant: dict[str, Any]) -> dict[str, Any]:
        shown = {"item_id": variant["item_id"], "options": variant["options"], "price": variant["price"]}
        difference = _difference(float(variant["price"]), old)
        if difference is not None:
            shown["price_difference_against_current_item"] = difference
        if current is not None:  # so that "the same but in red" can be told from an item that changes more than was asked
            shown["differs_from_current_item_in"] = {name: value for name, value in variant["options"].items()
                                                     if _norm(current["options"].get(name)) != _norm(value)}
        return shown

    def misses(variant: dict[str, Any]) -> dict[str, Any]:
        return {name: variant["options"].get(name) for name, value in wanted.items() if _norm(variant["options"].get(name)) != value}

    in_stock = [v for v in pool if v.get("available") and (current is None or v.get("item_id") != current.get("item_id"))]
    matches = sorted((v for v in in_stock if not misses(v)), key=lambda v: (v["price"], v["item_id"]))
    result: dict[str, Any] = {"product": product.get("name"), "product_id": product_id, "searched_for": wanted or "any item in stock"}
    if current is not None:
        result["current_item"] = {"item_id": current["item_id"], "options": current["options"], "price_paid": old,
                                  "note": "Not among the items below: an item cannot be changed or exchanged for itself. A replacement "
                                          "must be a different item of the product."}
    if among is not None:
        result["only_among_item_ids"] = sorted(among)
        result["of_those_not_variants_of_this_product"] = sorted(among - {v.get("item_id") for v in variants})
    result["items_in_stock_that_match_cheapest_first"] = [row(v) for v in matches]
    if matches:
        cheapest = [v["item_id"] for v in matches if v["price"] == matches[0]["price"]]
        result["cheapest_match"] = cheapest[0] if len(cheapest) == 1 else {"tie_at_the_same_price": cheapest}
        if old is not None:  # for "the cheapest one": the item the customer has may already be it
            result["keeping_the_current_item_is_cheaper_than_every_match"] = round(old * 100) < round(float(matches[0]["price"]) * 100)
    else:
        result["no_item_in_stock_matches"] = True
        result["matching_items_out_of_stock"] = [v["item_id"] for v in pool if not v.get("available") and not misses(v)]
        nearest = sorted(in_stock, key=lambda v: (len(misses(v)), v["price"], v["item_id"]))[:5]
        result["closest_items_in_stock"] = [{**row(v), "differs_from_what_was_asked_in": misses(v)} for v in nearest]
        result["values_in_stock_for_each_option"] = {name: sorted({v["options"][name] for v in in_stock if name in v["options"]})
                                                     for name in sorted(names.values())}
    owned = _other_purchases(items, product_id, str(current_id) if current_id else None, product)
    if owned:
        result["other_items_of_this_product_the_customer_bought"] = owned
    result["reminders"] = SEARCH_REMINDERS
    return json.dumps(result)


def offered_item_ids(items: Items) -> set[str]:
    """Every item a search of this conversation returned as a match."""
    offered: set[str] = set()
    for _, text in results_of(items, SEARCH_TOOL):
        result = _json(text)
        for row in (result.get("items_in_stock_that_match_cheapest_first") or []) if isinstance(result, dict) else []:
            offered.add(str(row.get("item_id")))
    return offered


def unsearched_change(items: Items, calls: Calls) -> str | None:
    """The note, when this reply changes or exchanges to an item that no search of the conversation returned."""
    offered = offered_item_ids(items)
    for call in calls:
        new = call["arguments"].get("new_item_ids")
        if call["name"] not in ITEM_CHANGES or not isinstance(new, list):
            continue
        missing = [str(item) for item in new if str(item) not in offered]
        if missing:
            return UNSEARCHED_NOTE.format(held=_held(call), missing=", ".join(missing))
    return None


SAME_ITEM_NOTE = (
    HEADER + " You were about to make this call: {held}\n"
    "It replaces item {same} with itself. The policy allows a change or an exchange only to a different item of the same "
    "product, so this call is refused. Tell the customer that the item cannot be replaced by the same item, and ask "
    "whether they want a different option of it or something else.")
SAME_ITEM_HOLDS = 2


def same_item_change(calls: Calls) -> str | None:
    """The note, when this reply changes or exchanges an item for itself."""
    for call in calls:
        old, new = call["arguments"].get("item_ids"), call["arguments"].get("new_item_ids")
        if call["name"] in ITEM_CHANGES and isinstance(old, list) and isinstance(new, list):
            same = [str(a) for a, b in zip(old, new) if str(a) == str(b)]
            if same:
                return SAME_ITEM_NOTE.format(held=_held(call), same=", ".join(same))
    return None


# --- order-lock -------------------------------------------------------------------------------

PENDING_CHANGE = "modify_pending_order_items"
ORDER_ADDRESS = "modify_pending_order_address"
SPEAKS_OF_DELIVERY = re.compile(r"\b(address|ship(ped|ping|ment|s)?|deliver(ed|y|ing)?|redirect|send (it|them|this|that|the)|sent to)\b", re.IGNORECASE)
LOCK_NOTE = (
    HEADER + " You were about to make this call: {held}\n"
    "It locks the order: afterwards its shipping address and payment method cannot be changed, its items cannot be changed "
    "again and it cannot be cancelled. The customer has spoken of a delivery address in this conversation, and the address "
    "of this order has not been changed. If the customer still wants this order sent to another address, make that change "
    "first, with their confirmation. If they do not, or said to leave the address as it is, make the same call again.")


def locks_before_address(items: Items, calls: Calls) -> str | None:
    """The note, when an item change of a pending order comes while the customer spoke of delivery and its address is unchanged."""
    change = next((call for call in calls if call["name"] == PENDING_CHANGE), None)
    if change is None or not any(item["role"] == "user" and SPEAKS_OF_DELIVERY.search(item["text"]) for item in items):
        return None
    order = change["arguments"].get("order_id")
    changed = any(call["arguments"].get("order_id") == order and not text.startswith("Error") for call, text in results_of(items, ORDER_ADDRESS))
    same_reply = any(call["name"] == ORDER_ADDRESS and call["arguments"].get("order_id") == order for call in calls)
    return None if changed or same_reply else LOCK_NOTE.format(held=_held(change))


# --- payment ----------------------------------------------------------------------------------

USER_TOOL = "get_user_details"
NAMES_A_PAYMENT = re.compile(r"paypal|credit card|gift card|\bcard\b|original (payment|method)|same (payment|method|card)|payment method",
                             re.IGNORECASE)
PAYMENT_NOTE = (
    HEADER + " You were about to make this call: {held}\n"
    "The policy says the customer must provide the payment method that pays or receives the price difference. This "
    "customer has more than one payment method on file and has not named one in this conversation. Do not make the "
    "call yet: ask the customer which payment method to use for the price difference, naming the ones on file, and "
    "make the call with their answer.")


def payment_methods_on_file(items: Items) -> int:
    """How many payment methods the customer's details showed, from the last ``get_user_details`` result; 0 when none was read."""
    for _, text in reversed(results_of(items, USER_TOOL)):
        user = _json(text)
        methods = user.get("payment_methods") if isinstance(user, dict) else None
        return len(methods) if isinstance(methods, dict) else 0
    return 0


def payment_not_chosen(items: Items, calls: Calls) -> str | None:
    """The note, when this reply changes or exchanges items and the customer, with several methods on file, named none."""
    change = next((call for call in calls if call["name"] in ITEM_CHANGES), None)
    if change is None or payment_methods_on_file(items) < 2:
        return None
    if any(item["role"] == "user" and NAMES_A_PAYMENT.search(item["text"]) for item in items):
        return None
    return PAYMENT_NOTE.format(held=_held(change))


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


# The first three digits of a ZIP code give the state. 201 is left out: the store's addresses use it for Washington, DC.
ZIP_STATES = (
    (5, 5, "NY"), (10, 27, "MA"), (28, 29, "RI"), (30, 38, "NH"), (39, 49, "ME"), (50, 59, "VT"), (60, 69, "CT"), (70, 89, "NJ"),
    (100, 149, "NY"), (150, 196, "PA"), (197, 199, "DE"), (200, 200, "DC"), (202, 205, "DC"), (206, 219, "MD"), (220, 246, "VA"),
    (247, 268, "WV"), (270, 289, "NC"), (290, 299, "SC"), (300, 319, "GA"), (320, 349, "FL"), (350, 369, "AL"), (370, 385, "TN"),
    (386, 397, "MS"), (398, 399, "GA"), (400, 427, "KY"), (430, 459, "OH"), (460, 479, "IN"), (480, 499, "MI"), (500, 528, "IA"),
    (530, 549, "WI"), (550, 567, "MN"), (570, 577, "SD"), (580, 588, "ND"), (590, 599, "MT"), (600, 629, "IL"), (630, 658, "MO"),
    (660, 679, "KS"), (680, 693, "NE"), (700, 714, "LA"), (716, 729, "AR"), (730, 749, "OK"), (750, 799, "TX"), (800, 816, "CO"),
    (820, 831, "WY"), (832, 838, "ID"), (840, 847, "UT"), (850, 865, "AZ"), (870, 884, "NM"), (885, 885, "TX"), (889, 898, "NV"),
    (900, 961, "CA"), (967, 968, "HI"), (970, 979, "OR"), (980, 994, "WA"), (995, 999, "AK"))
ZIP = re.compile(r"(?<![\d#])\d{5}(?!\d)")
ASKS_STATE_OR_COUNTRY = re.compile(r"\b(state|country)\b", re.IGNORECASE)
STATE_NOTE = (
    HEADER + " You were about to send this reply: {held}\n"
    "The system has looked up what you were about to ask for. {facts} The country of every address in this store is USA. "
    "These are looked-up facts, not guesses: use them, do not ask the customer for the state or the country, and go on "
    "with the address the customer gave (summarise it in full and ask for their confirmation as the policy requires).")


STATE_HOLDS = 3  # the model asked again after one note in a smoke run of the second round


def state_for_zip(code: str) -> str | None:
    """The two-letter state of a five-digit ZIP code; ``None`` when the prefix is not in the table."""
    if not (isinstance(code, str) and len(code.strip()) == 5 and code.strip().isdigit()):
        return None
    prefix = int(code.strip()[:3])
    return next((state for low, high, state in ZIP_STATES if low <= prefix <= high), None)


def asks_state_or_country(items: Items, text: str, calls: Calls) -> str | None:
    """The note, when a reply about an address asks for the state or country and a ZIP code the customer gave settles the state."""
    if calls or not text or not ASKS_STATE_OR_COUNTRY.search(text) or "address" not in text.lower() or re.search(r"\bUSA\b", text):
        return None
    codes = [code for item in items if item["role"] == "user" for code in ZIP.findall(item["text"])]
    states = {code: state_for_zip(code) for code in dict.fromkeys(codes)}
    facts = [f"ZIP code {code} is in the state {state}." for code, state in states.items() if state]
    return STATE_NOTE.format(held=json.dumps(text, ensure_ascii=False), facts=" ".join(facts)) if facts else None


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
        elif not state.strip() and state_for_zip(arguments.get("zip")):
            arguments["state"] = state_for_zip(arguments.get("zip"))
    return call if arguments == call["arguments"] else {**call, "arguments": arguments}


# --- handover-once ----------------------------------------------------------------------------

HANDOVER_TOOL = "transfer_to_human_agents"
HANDOVER_ONCE_NOTE = (
    HEADER + " You were about to transfer the customer to a human agent. A transfer ends the conversation, and the "
    "customer may have other requests you can handle. Do not transfer in this reply. Tell the customer plainly what "
    "you cannot do and why, answer anything they asked that the tool results above answer, and ask whether there is "
    "anything else you can help with. If the customer then still needs something outside your tools, you can transfer.")


HANDOVER_REFUSALS = 1  # a second refusal can keep a customer from help the policy requires (Codex, on the full run)


def first_early_transfer(items: Items, calls: Calls, asked_for_a_person: bool) -> bool:
    """This reply transfers, no transfer was made before, and the customer has not asked for a person."""
    if asked_for_a_person or not any(call["name"] == HANDOVER_TOOL for call in calls):
        return False
    return not any(call["name"] == HANDOVER_TOOL for item in items if item["role"] == "assistant" for call in item["calls"])


# --- one turn of the agent under the rules ------------------------------------------------------

MAX_ROUNDS = 8  # searches and holds in one turn before the turn is given up as unscored


class RuleError(Exception):
    """The turn did not settle under the rules: the conversation is unscored."""


class RuleState:
    """What the rules keep over one conversation."""

    def __init__(self) -> None:
        self.holds: list[str] = []  # each reply held and asked again, by rule
        self.local: list[tuple[int, Items]] = []  # searches the agent ran itself: (how many kept items came before, the call and its result)
        self.searches: list[dict[str, Any]] = []  # each search: its arguments and its result, for the record
        self.address_corrections = 0

    def record(self) -> dict[str, Any]:
        return {"holds": list(self.holds), "address_corrections": self.address_corrections, "searches": list(self.searches)}


def with_local(base: Items, state: RuleState) -> Items:
    """The kept conversation with the agent's own searches put back where they happened."""
    merged: Items = []
    for position in range(len(base) + 1):
        for anchor, entry in state.local:
            if anchor == position:
                merged.extend(entry)
        if position < len(base):
            merged.append(base[position])
    return merged


def _hold(rules: tuple[str, ...], items: Items, calls: Calls, state: RuleState, asked_for_a_person: bool) -> tuple[str, str] | None:
    """Which rule holds this reply, and its note: one at a time, each kind a limited number of times in a conversation."""
    if ("handover-once" in rules and state.holds.count("handover-once") < HANDOVER_REFUSALS
            and first_early_transfer(items, calls, asked_for_a_person)):
        return "handover-once", HANDOVER_ONCE_NOTE
    if "offers" in rules and state.holds.count("same-item") < SAME_ITEM_HOLDS:
        note = same_item_change(calls)
        if note:
            return "same-item", note
    if "offers" in rules and state.holds.count("unsearched") < UNSEARCHED_HOLDS:
        note = unsearched_change(items, calls)
        if note:
            return "unsearched", note
    if "order-lock" in rules and "order-lock" not in state.holds:
        note = locks_before_address(items, calls)
        if note:
            return "order-lock", note
    if "payment" in rules and "payment" not in state.holds:
        note = payment_not_chosen(items, calls)
        if note:
            return "payment", note
    return None


def _text_hold(rules: tuple[str, ...], items: Items, text: str, calls: Calls, state: RuleState) -> tuple[str, str] | None:
    """A hold that reads the reply's words: the question about the state or country, a few times in a conversation."""
    if "address" in rules and state.holds.count("state") < STATE_HOLDS:
        note = asks_state_or_country(items, text, calls)
        if note:
            return "state", note
    return None


def turn(rules: tuple[str, ...], base: Items, tools: list[dict[str, Any]], ask: Any, state: RuleState,
         asked_for_a_person: bool) -> tuple[str, Calls]:
    """The agent's reply to the conversation ``base`` under the rules. ``ask(items, tools)`` is one model call."""
    offers = "offers" in rules
    if offers:
        tools = [*tools, SEARCH_SCHEMA]
    items = with_local(base, state)

    def shown() -> Items:
        return shown_items(items) if offers else items

    text, calls = ask(shown(), tools)
    for _ in range(MAX_ROUNDS):
        local = [call for call in calls if call["name"] == SEARCH_TOOL]
        if local:  # the agent's own tool: run here, kept with the conversation, never sent on
            entry: Items = [{"role": "assistant", "text": text, "calls": local}]
            for call in local:
                result = search(items, call["arguments"])
                state.searches.append({"arguments": call["arguments"], "result": _json(result)})
                entry.append({"role": "tool", "id": call["id"], "text": result})
            state.local.append((len(base), entry))
            items = items + entry
            text, calls = ask(shown(), tools)
            continue
        held = _hold(rules, items, calls, state, asked_for_a_person) or _text_hold(rules, items, text, calls, state)
        if held is None:
            break
        state.holds.append(held[0])
        offered = [t for t in tools if t["function"]["name"] != HANDOVER_TOOL] if held[0] == "handover-once" else tools
        text, calls = ask([*shown(), {"role": "user", "text": held[1]}], offered)
        if held[0] == "handover-once" and any(call["name"] == HANDOVER_TOOL for call in calls):
            raise RuleError("the model called the transfer tool, which was not among the tools it was sent")
    else:
        raise RuleError(f"the turn did not settle in {MAX_ROUNDS} rounds of searches and checks")
    if "address" in rules:
        fixed = [fix_address(call) for call in calls]
        state.address_corrections += sum(1 for before, after in zip(calls, fixed) if after is not before)
        calls = fixed
    return text, calls
