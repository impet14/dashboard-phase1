# app.py
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import requests
import dash_leaflet as dl

# Flask URL where MQTT data is served
FLASK_URL = 'http://127.0.0.1:5000/data'

# ------------------------------------------------------------------------------
# 1) INITIAL / DEFAULT VALUES FOR EACH SENSOR
#    Adjust or remove sensors you do not need.
# ------------------------------------------------------------------------------
initial_air_quality = {
    "TKC": {
        "temperature": 29.1,
        "humidity": 70,
        "co2": 400,
        "pm2_5": 12,
        "pm10": 20,
        "tvoc": 300,
        "pressure": 1013,
        "hcho": 0.05,
        "light_level": 300,
        "battery": 40,
        "water_level": 60.0,
        "latitude": 14.2123873,
        "longitude": 100.7405519
    },
    "supanburi": {
        "temperature": 25.0,
        "humidity": 60,
        "co2": 350,
        "pm2_5": 10,
        "pm10": 18,
        "tvoc": 280,
        "pressure": 1012,
        "hcho": 0.04,
        "light_level": 320,
        "battery": 95,
        "water_level": 20.0,
        "latitude": 14.407399699427653,
        "longitude": 100.07982902339289
    }
}

# Use this fallback if an incoming sensor ID is not listed above
default_fallback = {
    "temperature": 0.0,
    "humidity": 0,
    "co2": 0,
    "pm2_5": 0,
    "pm10": 0,
    "tvoc": 0,
    "pressure": 0,
    "hcho": 0,
    "light_level": 0,
    "battery": 0,
    "water_level": 0,
    "latitude": 0,
    "longitude": 0
}

# ------------------------------------------------------------------------------
# 2) HELPER FUNCTIONS FOR BUILDING DASHBOARD COMPONENTS
# ------------------------------------------------------------------------------

def create_metric_card(icon_class, label, value):
    """Helper function to create a responsive metric card with Font Awesome icons and tooltips."""
    return dbc.Col(
        dbc.Card(
            [
                dbc.Tooltip(label, target=f"{label.replace(' ', '').lower()}-icon"),
                html.I(className=icon_class + " metric-icon", id=f"{label.replace(' ', '').lower()}-icon"),
                html.H6(f"{label}: {value}", className="metric-value")
            ],
            className="metric-card",
        ),
        xs=12, sm=6, md=4, lg=3, xl=2  # Responsive column sizes
    )

def create_water_level_card(water_level_cm):
    """Creates a water level indicator card with animation."""
    try:
        water_level_cm = float(water_level_cm)
        water_level_cm = max(0, min(water_level_cm, 100))  # Clamp between 0 and 100
    except (TypeError, ValueError):
        water_level_cm = 0  # Default to 0 if invalid

    return dbc.Col(
        dbc.Card(
            [
                html.Div("💧 ระดับน้ำ", className="metric-label"),
                html.Div(
                    className="water-container",
                    children=[
                        html.Div(
                            className="water-level",
                            style={"height": f"{water_level_cm}%"},  # Dynamic height
                        )
                    ]
                ),
                html.Div(f"{water_level_cm} cm", className="water-level-text")
            ],
            className="water-level-card",
        ),
        xs=12, sm=6, md=4, lg=3, xl=2
    )

def create_map_section(lat, lon):
    """Helper function to create the map section using dash-leaflet with Esri satellite view."""
    return dl.Map(
        center=[lat, lon],
        zoom=15,
        style={'width': '100%', 'height': '450px'},
        children=[
            dl.TileLayer(
                url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attribution='Tiles © Esri'
            ),
            dl.Marker(position=[lat, lon])
        ]
    )

def create_sensor_dashboard(sensor_id, sensor_data):
    """Creates a dashboard section for a single sensor_id and its merged sensor_data."""
    # Define metric data with Font Awesome icons
    metric_data = [
        ("fas fa-thermometer-half", "อุณหภูมิ", f"{sensor_data.get('temperature', 'N/A')}°C"),
        ("fas fa-tint", "ความชื้น", f"{sensor_data.get('humidity', 'N/A')}%"),
        ("fas fa-cloud", "CO2", f"{sensor_data.get('co2', 'N/A')} ppm"),
        ("fas fa-smog", "PM2.5", f"{sensor_data.get('pm2_5', 'N/A')} µg/m³"),
        ("fas fa-industry", "PM10", f"{sensor_data.get('pm10', 'N/A')} µg/m³"),
        ("fas fa-vial", "TVOC", f"{sensor_data.get('tvoc', 'N/A')} ppb"),
        ("fas fa-wind", "ความดัน", f"{sensor_data.get('pressure', 'N/A')} hPa"),
        ("fas fa-flask", "HCHO", f"{sensor_data.get('hcho', 'N/A')} mg/m³"),
        ("fas fa-lightbulb", "แสงสว่าง", f"{sensor_data.get('light_level', 'N/A')}"),
        ("fas fa-battery-full", "แบตเตอรี่", f"{sensor_data.get('battery', 'N/A')}%"),
    ]

    # Create metric cards
    metric_cards = [create_metric_card(icon, label, value) for icon, label, value in metric_data]

    # Create water level card
    water_level_cm = sensor_data.get('water_level', 0)  # Default if not available
    water_level_card = create_water_level_card(water_level_cm)

    # Combine all metric cards including water level
    all_cards = metric_cards + [water_level_card]

    # Use lat/lon from sensor_data
    latitude = sensor_data.get('latitude', 0)
    longitude = sensor_data.get('longitude', 0)

    # Create map
    map_section = create_map_section(latitude, longitude)

    # Create a Card Group for metrics
    metrics_group = dbc.Row(all_cards, className="mb-3", style={"gap": "20px"})

    sensor_card = dbc.Card(
        [
            # Header text uses helper for area name
            dbc.CardHeader(f"เซ็นเซอร์นาข้าว {get_sensor_area(sensor_id)}", className="card-header"),
            dbc.CardBody(
                [
                    metrics_group,
                    html.Div(map_section, className='gps-map-section', style={"marginTop": "20px"})
                ]
            ),
        ],
        className="graph-card",
        style={"width": "100%"},
    )

    return sensor_card

def get_sensor_area(sensor_id):
    """Return the friendly location/area name based on sensor ID."""
    sensor_areas = {
        "nongseua": "หนองเสือปทุมธานี",
        "supanburi": "สุพรรณบุรี",
        "TKC": "หนองเสือปทุมธานี (TKC)",       # Example mapping for "TKC"
        "WaterLevelSensor_02": "Water-Level Field"  # Example for custom sensor
    }
    return sensor_areas.get(sensor_id, "Unknown Area")

# ------------------------------------------------------------------------------
# 3) DASH LAYOUT
# ------------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.LUX,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"
    ]
)

app.layout = dbc.Container(
    [
        html.Div(
            className="background",
            children=[
                # Image title from assets folder
                html.Div(
                    html.Img(src='/assets/tkc-title.png', className="main-title"),
                    style={"text-align": "center", "margin-bottom": "0vh", "margin-top": "0vh"}
                ),
                # Interval to periodically fetch the latest data
                dcc.Interval(id='interval-component', interval=2 * 1000, n_intervals=0),

                # Sensor dashboards will be placed here
                html.Div(id='sensors-dashboard'),

                # Powered by ...
                html.Div("Powered by TKC-RD", className="powered-by"),
            ],
            style={
                "width": "100%",
                "min-height": "100vh",
                "margin": "auto",
                "padding": "1vh",
                "display": "flex",
                "flex-direction": "column",
                "justify-content": "center",
                "align-items": "center",
                "overflow-y": "auto",
                "overflow-x": "hidden",
            },
        )
    ],
    fluid=True,
)

# ------------------------------------------------------------------------------
# 4) DASH CALLBACK
# ------------------------------------------------------------------------------
@app.callback(
    Output('sensors-dashboard', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """
    Periodically fetch the latest data from the Flask endpoint.
    Merge it with any initial/default values, then display sensor dashboards.
    """
    try:
        response = requests.get(FLASK_URL)
        response.raise_for_status()
        data = response.json()  # Data should be a dict: { sensor_id: {...} }
    except requests.exceptions.RequestException:
        # If cannot connect to Flask, just use an empty dict so we only see "initial_air_quality" or none
        data = {}

    sensor_sections = []

    # data is expected to have the form:
    # {
    #   "WaterLevelSensor_02": {
    #       "device_name": "WaterLevelSensor_02",
    #       "water_level": 21,
    #       "latitude": 13.86336,
    #       "longitude": 100.5807,
    #       "Battery Voltage": 3.7,
    #       "temperature": 53.33333,
    #       ... (any other fields) ...
    #   },
    #   "TKC": {...},
    #   ...
    # }

    # If data is empty or you have no sensors, fallback to the initial sensors
    # so the dashboard doesn't just vanish. That is optional:
    if not data:
        data = {k: v for k, v in initial_air_quality.items()}

    for sensor_id, sensor_data in data.items():
        # ---------------------------------------------------------
        #  A) Determine a base data dictionary
        #     - if sensor_id exists in initial_air_quality, use it
        #     - else use the default fallback
        # ---------------------------------------------------------
        base_data = initial_air_quality.get(sensor_id, default_fallback)

        # ---------------------------------------------------------
        #  B) Merge actual sensor data from MQTT/Flask with base
        #     (The new MQTT data has top-level fields, e.g. .get("temperature"))
        # ---------------------------------------------------------
        merged_data = {
            "temperature": sensor_data.get("temperature", base_data["temperature"]),
            "humidity": sensor_data.get("humidity", base_data["humidity"]),
            "co2": sensor_data.get("co2", base_data["co2"]),
            "pm2_5": sensor_data.get("pm2_5", base_data["pm2_5"]),
            "pm10": sensor_data.get("pm10", base_data["pm10"]),
            "tvoc": sensor_data.get("tvoc", base_data["tvoc"]),
            "pressure": sensor_data.get("pressure", base_data["pressure"]),
            "hcho": sensor_data.get("hcho", base_data["hcho"]),
            "light_level": sensor_data.get("light_level", base_data["light_level"]),

            # The MQTT data calls the battery voltage "Battery Voltage", so we map that:
            "battery": sensor_data.get("Battery Voltage", base_data["battery"]),

            "water_level": sensor_data.get("water_level", base_data["water_level"]),
            "latitude": sensor_data.get("latitude", base_data["latitude"]),
            "longitude": sensor_data.get("longitude", base_data["longitude"]),
        }

        # ---------------------------------------------------------
        #  C) Create sensor dashboard
        # ---------------------------------------------------------
        sensor_card = create_sensor_dashboard(sensor_id, merged_data)
        sensor_sections.append(
            dbc.Row(
                dbc.Col(sensor_card, width=12),
                className="mb-4"
            )
        )

    return sensor_sections

# ------------------------------------------------------------------------------
# 5) RUN THE DASH APP
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, dev_tools_ui=False, dev_tools_props_check=False)
