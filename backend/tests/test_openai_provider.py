"""OpenAI provider: OPENAI_EXTRA_BODY parsing + it being merged into requests.

The mentor hung on slow reasoning models; the fix streams AND lets the operator
disable the model's hidden "thinking" via OPENAI_EXTRA_BODY. A bad value must
never break the mentor, and a good value must actually reach the request body.
"""

from __future__ import annotations

from app.services.ai.openai_provider import OpenAIProvider, _parse_extra_body


def test_parse_extra_body_valid_empty_and_invalid():
    assert _parse_extra_body('{"reasoning_effort":"low"}') == {"reasoning_effort": "low"}
    assert _parse_extra_body("") == {}
    assert _parse_extra_body("   ") == {}
    # Invalid JSON and non-object JSON are ignored rather than raising.
    assert _parse_extra_body("{not json}") == {}
    assert _parse_extra_body("[1,2,3]") == {}


def test_extra_body_is_stored_on_the_provider():
    p = OpenAIProvider(
        "sk-test",
        model="m",
        base_url="https://gw.example/v1",
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    assert p._extra_body == {"chat_template_kwargs": {"enable_thinking": False}}
