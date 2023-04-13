from importlib import resources as pkg_resources
from pathlib import Path
from typing import ContextManager, Optional

import typer
from streamlit.web import bootstrap as st_bootstrap

import viz_cookiecutter

app = typer.Typer(
    name="viz-cookiecutter",
    help="Command to execute Visual Cookiecutter.",
    no_args_is_help=True,
)


@app.command()
def run(
    template_path: str,
    directory: Optional[str] = typer.Option(
        None,
        help=
        "Directory within repo that holds cookiecutter.json file for advanced "
        "repositories with multi templates in it"),
    ouptut_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Where to output the generated project dir into"),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help="branch, tag or commit to checkout after git clone"),
    overwrite_if_exists: bool = typer.Option(
        False,
        "-f",
        "--overwrite-if-exists",
        help=
        "Overwrite the contents of the output directory if it already exists"),
    config_file: Optional[Path] = typer.Option(None,
                                               dir_okay=False,
                                               exists=True,
                                               help="User configuration file"),
) -> None:
    args = [template_path]
    if overwrite_if_exists is not None:
        args.append("--overwrite-if-exists")

    if directory:
        args.extend(["--directory", directory])

    if checkout is not None:
        args.extend(["--checkout", checkout])

    if config_file is not None:
        args.extend(["--config-file", config_file])

    with _get_streamlit_main() as st_main:
        st_bootstrap.run(str(st_main),
                         command_line=None,
                         args=args,
                         flag_options={})


def _get_streamlit_main() -> ContextManager[Path]:
    return pkg_resources.path(viz_cookiecutter, "gui.py")
