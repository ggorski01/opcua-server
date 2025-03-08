from flask import Flask, jsonify, request
from flask_basicauth import BasicAuth
from flasgger import Swagger
from opcua import Server
import logging, os, time, threading
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import datetime

# Initialize Flask app
app = Flask(__name__)

# Basic Authentication Configuration
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'adminpassword'
basic_auth = BasicAuth(app)

# Swagger Configuration
app.config['SWAGGER'] = {'title': 'OPC UA Server API', 'uiversion': 3}
swagger = Swagger(app)

# Logging Configuration
LOG_FILENAME = "opcua_server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILENAME),  # Log to file
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger("opcua.server")

# Create OPC UA Server
server = Server()
server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
server.set_server_name("OPC UA Server with Authentication")

uri = "http://example.org"
idx = server.register_namespace(uri)
objects = server.get_objects_node()
temperature_object = objects.add_object(idx, "Temperature")
temperature_tag = temperature_object.add_variable(idx, "Temperature", 22.5)
temperature_tag.set_writable()

# User authentication database
users = {"admin": "adminpassword", "user1": "userpassword"}

# Global variables for Dash
temperature_data = []  # Store last 10 temperature values
time_data = []  # Store last 10 timestamps

# Function to simulate temperature changes
def temperature_simulation():
    while True:
        try:
            new_temp = round(temperature_tag.get_value() + 0.1, 2)
            temperature_tag.set_value(new_temp)
            logger.info(f"Temperature updated: {new_temp}°C")

            # Append new data
            time_data.append(datetime.datetime.now().strftime('%H:%M:%S'))
            temperature_data.append(new_temp)

            # Keep only last 10 data points
            if len(temperature_data) > 10:
                temperature_data.pop(0)
                time_data.pop(0)

            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in temperature simulation: {e}")
            break

# Start OPC UA server
def start_opcua_server():
    try:
        server.start()
        logger.info(f"Server started at {server.endpoint}")
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to start OPC UA server: {e}")
    finally:
        server.stop()
        logger.info("OPC UA Server stopped.")

# Flask API - Get Temperature
@app.route('/temperature', methods=['GET'])
@basic_auth.required
def get_temperature():
    """
    Retrieves the current temperature value from the OPC UA server.
    ---
    tags:
      - Temperature
    responses:
      200:
        description: Returns the current temperature
        schema:
          type: object
          properties:
            temperature:
              type: number
              example: 22.5
            user:
              type: string
              example: "admin"
    """
    authenticated_user = request.authorization.username
    logger.info(f"User '{authenticated_user}' retrieved the temperature: {temperature_tag.get_value()}°C")
    return jsonify({"temperature": temperature_tag.get_value(), "user": authenticated_user})

# Flask API - Update Temperature
@app.route('/temperature', methods=['POST'])
@basic_auth.required
def update_temperature():
    """
    Updates the OPC UA server temperature value.
    ---
    tags:
      - Temperature
    parameters:
      - name: temperature
        in: body
        required: true
        schema:
          type: object
          properties:
            temperature:
              type: number
              example: 25.0
    responses:
      200:
        description: Temperature updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Temperature updated successfully"
            new_temperature:
              type: number
              example: 25.0
            user:
              type: string
              example: "admin"
    """
    try:
        data = request.get_json()
        if "temperature" not in data:
            return jsonify({"error": "Temperature value is required"}), 400

        new_temperature = data["temperature"]
        temperature_tag.set_value(new_temperature)
        logger.info(f"Temperature manually updated to: {new_temperature}°C")
        return jsonify({"message": "Temperature updated successfully", "new_temperature": new_temperature})
    except Exception as e:
        logger.error(f"Failed to update temperature: {e}")
        return jsonify({"error": "Failed to update temperature"}), 500

# Start OPC UA server and simulation in separate threads
opcua_thread = threading.Thread(target=start_opcua_server, daemon=True)
temp_thread = threading.Thread(target=temperature_simulation, daemon=True)
opcua_thread.start()
temp_thread.start()

# Initialize Dash app
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix="/dashboard/")

# Dash Layout with Live Graph
dash_app.layout = html.Div([
    html.H1("Live Temperature Dashboard"),
    html.H2("Current Temperature:"),
    html.P(id="live-value", style={"fontSize": "30px", "fontWeight": "bold", "color": "blue"}),
    dcc.Graph(id="temperature-graph"),  # Live Graph
    dcc.Interval(id="interval-update", interval=2000, n_intervals=0)  # Auto-refresh every 2 sec
])

# Callback to update displayed value and graph
@dash_app.callback(
    [Output("live-value", "children"), Output("temperature-graph", "figure")],
    Input("interval-update", "n_intervals")
)
def update_dashboard(n):
    # Line Graph for Last 10 Data Points
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=time_data, 
        y=temperature_data, 
        mode='lines+markers',
        name='Temperature'
    ))
    figure.update_layout(
        title="Last 10 Temperature Readings",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        xaxis=dict(showline=True),
        yaxis=dict(showline=True),
        plot_bgcolor="rgba(245, 245, 245, 0.9)"
    )
    
    return f"{temperature_tag.get_value()} °C", figure

# Run Flask & Dash App
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
