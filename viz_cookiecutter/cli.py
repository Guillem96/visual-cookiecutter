from importlib import resources as pkg_resources
from pathlib import Path
from typing import ContextManager

import typer
from streamlit.web import bootstrap as st_bootstrap

import viz_cookiecutter

app = typer.Typer(
    name="viz-cookiecutter",
    help="Command to execute Visual Cookiecutter.",
    no_args_is_help=True,
)


@app.command()
def run(template_path: str) -> None:
    with _get_streamlit_main() as st_main:
        st_bootstrap.run(str(st_main),
                         command_line=None,
                         args=[template_path],
                         flag_options={})


def _get_streamlit_main() -> ContextManager[Path]:
    return pkg_resources.path(viz_cookiecutter, "gui.py")
