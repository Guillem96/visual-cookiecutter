from viz_cookiecutter.core import VisualCookiecutterContext, VisualCookiecutter

ctx = VisualCookiecutterContext.parse_obj({})
VisualCookiecutter(cookiecutter_params=[
    1,
], context=ctx)
