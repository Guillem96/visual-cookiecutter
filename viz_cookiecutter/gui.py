import copy
import sys
from pathlib import Path
from typing import Any, Mapping
import re
import streamlit as st
from cookiecutter.main import cookiecutter, get_user_config, determine_repo_dir
from jinja2 import Environment, BaseLoader

from viz_cookiecutter.core import VisualCookiecutter

jinja_env = Environment(loader=BaseLoader())


def _render_string(text: str) -> str:
    return jinja_env.from_string(text).render(
        {"cookiecutter": st.session_state.to_dict()})


def main() -> None:
    template = sys.argv[1]

    viz_cookie, title = _initialize_context(template)
    default_values = _initialize_default_values(viz_cookie)

    # Set default values to the session_state, if the parameter
    # is required set an empty value as default
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = "" if viz_cookie.is_required(
                key) else value

    _render_site(viz_cookie, template, title)


def _render_site(viz_cookie: VisualCookiecutter, template: str,
                 title: str) -> None:
    st.markdown(f"# 🍪 Visual Cookicutter - `{title}`")

    col1, col2 = st.columns([2, 1])

    with col1:
        _cookiecutter_params_form(viz_cookie)

    with col2:
        st.subheader("Cookiecutter context")
        st.write({
            k: st.session_state[k]
            for k in sorted(st.session_state.to_dict())
        })

    with st.container():
        if st.button("Bake 🍪"):
            with st.spinner("Baking project template..."):
                _bake_cookiecutter_template(viz_cookie, template)


def _cookiecutter_params_form(viz_cookie: VisualCookiecutter) -> None:
    st.subheader("Parameters")
    params_to_ask = {
        p: v
        for p, v in viz_cookie.cookiecutter_params.items()
        if _should_ask_for(viz_cookie, p)
    }

    for param_name, param_def_value in params_to_ask.items():
        label = _snake_case_to_title(param_name)
        if (desc := viz_cookie.context.descriptions.get(param_name)):
            label = f"{label} - {desc}"

        prev = st.session_state[param_name]
        if isinstance(param_def_value, str):
            st.session_state[param_name] = _render_text_input(
                viz_cookie, label, param_name, param_def_value)
        else:
            st.session_state[param_name] = st.radio(
                label, param_def_value,
                param_def_value.index(st.session_state[param_name]))

        if prev != st.session_state[param_name]:
            st.experimental_rerun()


def _render_text_input(viz_cookie: VisualCookiecutter, label: str,
                       param_name: str, param_def_value: str) -> str:
    placeholder = "Required" if viz_cookie.is_required(param_name) else ""

    # If the default value is a Jinja expression, render it and do not allow
    # the user to override it
    if re.match(r"^.*\{\{\s+.*\s+\}\}.*$", param_def_value):
        value = _render_string(param_def_value)
        disabled = True
        label = f"{label} - 🚫 Generated with Jinja: `{param_def_value}`"
    else:
        disabled = False
        value = st.session_state[param_name]

    return st.text_input(label,
                         value,
                         placeholder=placeholder,
                         disabled=disabled)


def _bake_cookiecutter_template(viz_cookie: VisualCookiecutter,
                                template: str) -> None:
    valid_form = True
    for param_name in viz_cookie.context.is_required:
        if st.session_state[param_name] == "":
            st.error(f'Parameter "{param_name}" is missing', icon="🚨")
            valid_form = False

    if not valid_form:
        return

    try:
        cookiecutter(template=template,
                     no_input=True,
                     extra_context=st.session_state.to_dict())
        st.success("Project successfully baked!", icon="✅")
    except Exception as e:
        st.error(f"Error baking project: {e}")


def _should_ask_for(viz_cookie: VisualCookiecutter, pn: str) -> bool:
    if pn not in viz_cookie.cookiecutter_params:
        raise ValueError(f'invalid parameter "{pn}"'
                         "it is not present in cookiecutter context.")

    if pn in viz_cookie.context.is_required:
        return True

    for param, cond in viz_cookie.context.if_.items():
        if pn in cond.ask_for:
            return st.session_state[param] == cond.is_

    return True


@st.cache_resource(show_spinner="Preparing Cookiecutter template...")
def _initialize_context(template: str) -> tuple[VisualCookiecutter, str]:
    config_dict = get_user_config()
    template_path, _ = determine_repo_dir(
        template=template,
        checkout=None,
        abbreviations=config_dict["abbreviations"],
        clone_to_dir=config_dict["cookiecutters_dir"],
        no_input=True,
    )
    template_path = Path(template_path)
    with (template_path / "cookiecutter.json").open() as f:
        viz_cookie = VisualCookiecutter.from_cookiecutter(f)

    return viz_cookie, template_path.name


@st.cache_data(show_spinner="Reading cookiecutter.json...")
def _initialize_default_values(
        _viz_cookie: VisualCookiecutter) -> Mapping[str, str]:
    input_values = {}
    for param_name, param_def_value in _viz_cookie.cookiecutter_params.items():
        if isinstance(param_def_value, str):
            input_values[param_name] = param_def_value
        else:
            input_values[param_name] = param_def_value[0]

    return copy.deepcopy(input_values)


def _snake_case_to_title(text: str) -> str:
    return " ".join(t.title() for t in text.split("_"))


if __name__ == "__main__":
    main()
