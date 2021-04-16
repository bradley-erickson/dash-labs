from ._callback import _callback as dx_callback
from functools import partial
from dash import Dash
from types import MethodType


class FlexibleCallbacks:
    """
    Dash app plugin to enable advanced callback behaviors including:
      - Property grouping
      - Keyword argument support
      - Support for providing full components in place of ids when using the
        dl.Output/dl.Input/sl.State dependency objects.

    Usage:

    >>> import dash
    >>> import dash_labs as dl
    >>> app = dash.Dash(__name__, plugins=[dl.FlexibleCallbacks()])
    """

    def __init__(self):
        pass

    def plug(self, app):
        _wrapped_callback = Dash.callback
        app._wrapped_callback = _wrapped_callback
        app.callback = MethodType(
            partial(dx_callback, _wrapped_callback=_wrapped_callback), app
        )


class HiddenComponents:
    def plug(self, app):
        app._layout_value = MethodType(_layout_value, app)


def _layout_value(self):
    layout = self._layout() if self._layout_is_function else self._layout

    # Add hidden components
    if hasattr(self, "_extra_hidden_components"):
        for c in self._extra_hidden_components:
            if c not in layout.children:
                layout.children.append(c)

    return layout
