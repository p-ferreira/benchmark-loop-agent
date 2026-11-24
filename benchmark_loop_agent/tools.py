"""Turn a BFCL function schema into what a model is given, the way BFCL does.

This follows BFCL's native function-calling handlers at the pinned gorilla
commit; nothing here is a new design:

* ``bfcl_eval/utils.py``: ``_func_doc_language_specific_pre_processing`` adds a
  language note to every function description and, for Java and JavaScript,
  rewrites each parameter as a string that holds the value in that language's
  syntax (``load_dataset_entry`` applies it to every category, Python too).
* ``bfcl_eval/model_handler/utils.py``: ``convert_to_tool`` and
  ``_cast_to_openai_type`` map BFCL type names to JSON Schema types with
  ``GORILLA_TO_OPENAPI`` (vendored ``type_mappings.py``), and replace "." in a
  function name with "_" because both providers reject dots in tool names.
  The scorer is told the same (see ``vendor/.../model_config.py``), as BFCL
  does for these models (``underscore_to_dot=True``).

Only the models' two styles are ported (OpenAI Responses and Anthropic).
"""

import copy
import json
import re
from typing import Any

from .categories import is_java, is_js
from .scoring import GORILLA_TO_OPENAPI


def language_note(category: str) -> str:
    """BFCL's ``_get_language_specific_hint``."""
    if is_java(category):
        return " Note that the provided function is in Java 8 SDK syntax."
    if is_js(category):
        return " Note that the provided function is in JavaScript syntax."
    return " Note that the provided function is in Python 3 syntax."


def with_language_handling(functions: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    """BFCL's ``_func_doc_language_specific_pre_processing``, on a copy."""
    functions = copy.deepcopy(functions)
    for item in functions:
        item["description"] = item["description"] + language_note(category)
        properties = item["parameters"]["properties"]
        if is_java(category):
            for value in properties.values():
                if value["type"] == "any":
                    value["description"] += " This parameter can be of any type of Java object in string representation."
                else:
                    value["description"] += f" This is Java {value['type']} type parameter in string representation."
                if value["type"] == "ArrayList" or value["type"] == "Array":
                    value["description"] += (
                        f" The list elements are of type {value['items']['type']}; they are not in string representation."
                    )
                    del value["items"]
                value["type"] = "string"
        elif is_js(category):
            for value in properties.values():
                if value["type"] == "any":
                    value["description"] += " This parameter can be of any type of JavaScript object in string representation."
                else:
                    value["description"] += f" This is JavaScript {value['type']} type parameter in string representation."
                if value["type"] == "array":
                    value["description"] += (
                        f" The list elements are of type {value['items']['type']}; they are not in string representation."
                    )
                    del value["items"]
                if value["type"] == "dict":
                    if "properties" in value:  # not every dict has properties
                        value["description"] += (
                            " The dictionary entries have the following schema; they are not in string representation. "
                            f"{json.dumps(value['properties'])}"
                        )
                        del value["properties"]
                value["type"] = "string"
    return functions


def _cast_to_openai_type(properties: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """BFCL's ``_cast_to_openai_type``, line for line."""
    for key, value in properties.items():
        if "type" not in value:
            properties[key]["type"] = "string"
        else:
            var_type = value["type"]
            if mapping == GORILLA_TO_OPENAPI and var_type == "float":
                properties[key]["format"] = "float"
                properties[key]["description"] += " This is a float type value."
            if var_type in mapping:
                properties[key]["type"] = mapping[var_type]
            else:
                properties[key]["type"] = "string"

        if properties[key]["type"] == "array" or properties[key]["type"] == "object":
            if "properties" in properties[key]:
                properties[key]["properties"] = _cast_to_openai_type(properties[key]["properties"], mapping)
            elif "items" in properties[key]:
                properties[key]["items"]["type"] = mapping[properties[key]["items"]["type"]]
                if properties[key]["items"]["type"] == "array" and "items" in properties[key]["items"]:
                    properties[key]["items"]["items"]["type"] = mapping[properties[key]["items"]["items"]["type"]]
                elif properties[key]["items"]["type"] == "object" and "properties" in properties[key]["items"]:
                    properties[key]["items"]["properties"] = _cast_to_openai_type(
                        properties[key]["items"]["properties"], mapping
                    )
    return properties


def convert_to_tool(functions: list[dict[str, Any]], style: str) -> list[dict[str, Any]]:
    """BFCL's ``convert_to_tool`` for ``style`` "openai-responses" or "claude"."""
    oai_tool = []
    for item in copy.deepcopy(functions):
        if "." in item["name"]:
            item["name"] = re.sub(r"\.", "_", item["name"])
        item["parameters"]["type"] = "object"
        item["parameters"]["properties"] = _cast_to_openai_type(item["parameters"]["properties"], GORILLA_TO_OPENAPI)
        if style == "claude":
            item["input_schema"] = item["parameters"]
            del item["parameters"]
            if "response" in item:
                item["description"] += f" The response field has the following schema: {json.dumps(item['response'])}"
                del item["response"]
        else:
            item["type"] = "function"
        oai_tool.append(item)
    return oai_tool
