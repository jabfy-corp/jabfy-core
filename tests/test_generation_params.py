import pytest
from pydantic import ValidationError

from app.schemas.actions import ActionRequest
from app.schemas.generation import GenerationParams


def test_unset_params_are_omitted() -> None:
    assert GenerationParams().to_payload() == {}


def test_exposes_every_documented_parameter() -> None:
    params = GenerationParams(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        min_p=0.05,
        max_tokens=256,
        seed=1234,
        stop=["</s>"],
    )

    assert params.to_payload() == {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "min_p": 0.05,
        "max_tokens": 256,
        "seed": 1234,
        "stop": ["</s>"],
    }


def test_accepts_n_predict_as_alias_for_max_tokens() -> None:
    assert GenerationParams(n_predict=128).to_payload() == {"max_tokens": 128}


def test_rejects_out_of_range_temperature() -> None:
    with pytest.raises(ValidationError):
        GenerationParams(temperature=5.0)


def test_rejects_unknown_parameter() -> None:
    with pytest.raises(ValidationError):
        GenerationParams(repeat_penalty=1.1)


def test_action_request_defaults_to_empty_params() -> None:
    request = ActionRequest(model="qwen3", prompt="User enters the house")

    assert request.params.to_payload() == {}
