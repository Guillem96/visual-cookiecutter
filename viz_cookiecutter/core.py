import json
from typing import Any, Mapping, Sequence, TextIO

import pydantic


class ConditionalParameter(pydantic.BaseModel):
    is_: Any = pydantic.Field(
        ...,
        alias="is",
        description=("If the parameter is equal to the value provided then "
                     "the condition will evaluate to true and 'invoke' the "
                     "follow up actions."))

    ask_for: set[str] = pydantic.Field(
        ...,
        description=("If the condition is met (evaluates to true), "
                     "visual cookicutter will prompt an input for all the "
                     "parameters listed here. Otherwise, the parameters will "
                     "stay hidden for the user filling up the form."))

    @pydantic.validator("is_", allow_reuse=True)
    def _is_primitive(cls, value: Any) -> int | str | float | bool:
        if not isinstance(value, (int, str, float, bool)):
            raise ValueError(
                "invalid type for 'is' of 'if' clause in '_viz_context'")
        return value

    class Config:
        frozen: bool = True


class VisualCookiecutterContext(pydantic.BaseModel):
    is_required: set[str] = pydantic.Field(
        set(),
        description=(
            "Sequence of required cookiecutter context fields. "
            "The parameters listed here will ignore the default "
            "value and the user will have to introduce them manually."))

    if_: Mapping[str, ConditionalParameter] = pydantic.Field(
        {}, alias="if", description="Mapping of parameter name to condition.")

    descriptions: Mapping[str, str] = pydantic.Field(
        {},
        description=("Mapping from parameter names to description. Useful "
                     "when providing extra information about the parameter. "
                     "The description supports markdown."))

    class Config:
        frozen: bool = True


_CookiecutterLastLevel = Mapping[str, str | Sequence[str]]
_CookiecutterNestedDict = Mapping[str, str | Sequence[str]
                                  | _CookiecutterLastLevel]
CookiecutterContext = Mapping[str,
                              str | Sequence[str] | _CookiecutterNestedDict]


class VisualCookiecutter(pydantic.BaseModel):
    cookiecutter_params: CookiecutterContext
    context: VisualCookiecutterContext

    def is_required(self, param_name: str) -> bool:
        return param_name in self.context.is_required

    @classmethod
    def from_cookiecutter(cls, fp: TextIO) -> "VisualCookiecutter":
        cookicutter_info = json.load(fp)

        try:
            ctx = VisualCookiecutterContext.parse_obj(
                cookicutter_info.pop("_viz_context"))
        except KeyError:
            ctx = VisualCookiecutterContext.parse_obj({})

        return cls(cookiecutter_params=cookicutter_info, context=ctx)

    @pydantic.root_validator(allow_reuse=True)
    def _validate_consistency(cls, values) -> None:
        cookiecutter_params = values["cookiecutter_params"]
        _validate_cookiecutter_params(cookiecutter_params)

        cookiecutter_param_names = set(cookiecutter_params)
        ctx: VisualCookiecutterContext = values["context"]

        for req_param_name in ctx.is_required:
            if req_param_name not in cookiecutter_param_names:
                raise ValueError(
                    f'invalid rquired parameter "{req_param_name}". '
                    "it is not present in cookiecutter context.")

            if isinstance(cookiecutter_params[req_param_name], list):
                raise ValueError(
                    f'choice parameter "{req_param_name}" cannot be in "is_required".'
                )

        # Check if description keys are avaialble in the cookiecutter json file
        for desc_param in ctx.descriptions:
            if desc_param not in cookiecutter_param_names:
                raise ValueError(
                    f'invalid parameter "{req_param_name}" in "descriptions". '
                    "it is not present in cookiecutter context.")

        # Check if condition keys and ask for keys are presend in the
        # cookiecutter json file
        for cond_param, cond in ctx.if_.items():
            if cond_param not in cookiecutter_param_names:
                raise ValueError(f'invalid "if" clause: "{cond_param}".'
                                 "it is not present in cooliecutter context")

            for ask_for_param_name in cond.ask_for:
                if ask_for_param_name not in cookiecutter_param_names:
                    raise ValueError(
                        f'invalid "ask_for" parameter name "{ask_for_param_name}". '
                        "it is not present in cookiecutter context.")

        return values

    def __hash__(self) -> int:
        return hash(self.context) ^ hash(tuple(self.cookiecutter_params))

    class Config:
        allow_mutation: bool = False


def _validate_cookiecutter_params(params: CookiecutterContext) -> None:
    for param_key, param_def_value in params.items():
        if isinstance(param_def_value, dict):
            err = (
                f'Mapping "{param_key}" can only have a single item defining '
                'the schema is supported.')
            assert len(param_def_value) == 1, err

            err = f'Mappings "{param_key}" can only have 1 or 2 depth levels'
            assert _dict_depth(param_def_value) in {1, 2}, err


def _dict_depth(d: Mapping[Any, Any], level: int = 0) -> int:
    if not isinstance(d, dict) or not d:
        return level
    return max(_dict_depth(d[key], level + 1) for key in d)
