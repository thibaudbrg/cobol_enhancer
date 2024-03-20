from flask import Flask, render_template_string
import plotly.graph_objects as go
import plotly.io as pio
from ubp_cobol.workflow import app, convert_graph_to_plotly_figure, merge_deciders_for_printing

app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    # Your Plotly figure
    fig = convert_graph_to_plotly_figure(merge_deciders_for_printing(app.get_graph()))
    fig.show()

    # Convert Plotly figure to HTML
    fig_html = pio.to_html(fig, full_html=False)

    # Basic HTML template to render Plotly figure
    html_template = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Plotly Figure</title>
        </head>
        <body>
            {{fig_html|safe}}
        </body>
    </html>
    """
    return render_template_string(html_template, fig_html=fig_html)

if __name__ == '__main__':
    app_flask.run(debug=True, port=5000)  # Set your preferred port here
