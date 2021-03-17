import dash
import dash_labs as dl
import numpy as np
import dash_core_components as dcc
import plotly.express as px

app = dash.Dash(__name__, plugins=[dl.Plugin()])
tpl = dl.templates.FlatDiv()


@app.callback(
    args=dict(
        fun=tpl.dropdown_input(["sin", "cos", "exp"], label="Function", kind=dl.State),
        figure_title=tpl.textbox_input(
            "Initial Title", label="Figure Title", kind=dl.State
        ),
        phase=tpl.slider_input(1, 10, label="Phase", kind=dl.State),
        amplitude=tpl.slider_input(1, 10, value=3, label="Amplitude", kind=dl.State),
        n_clicks=tpl.button_input("Update", label=None),
    ),
    template=tpl,
)
def greet(fun, figure_title, phase, amplitude, n_clicks):
    print(fun, figure_title, phase, amplitude)
    xs = np.linspace(-10, 10, 100)
    return dcc.Graph(
        figure=px.line(x=xs, y=getattr(np, fun)(xs + phase) * amplitude).update_layout(
            title_text=figure_title
        )
    )


app.layout = tpl.layout(app)

if __name__ == "__main__":
    app.run_server(debug=True)
