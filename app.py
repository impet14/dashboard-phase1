# app.py
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import requests
import dash_leaflet as dl

# Flask URL where MQTT data is served
FLASK_URL = 'http://127.0.0.1:5000/data'

# Initialize Dash app with a custom theme and Font Awesome for icons
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.LUX,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"
])  # Using LUX theme and Font Awesome for icons

# Initial Values for Air Quality Metrics for each sensor
initial_air_quality = {
    "nongseua": {
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
        "water_level":60.0,
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
        water_level_cm = max(0, min(water_level_cm, 100))  # Clamp between 0 and 100 cm
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
                            style={"height": f"{water_level_cm}%"},  # Dynamic height based on water level
                        )
                    ]
                ),
                html.Div(f"{water_level_cm} cm", className="water-level-text")
            ],
            className="water-level-card",
        ),
        xs=12, sm=6, md=4, lg=3, xl=2  # Responsive column sizes
    )

def create_map_section(lat, lon):
    """Helper function to create the map section using dash-leaflet with Esri satellite view."""
    return dl.Map(center=[lat, lon], zoom=15, style={'width': '100%', 'height': '450px'}, children=[
        dl.TileLayer(
            url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attribution='Tiles © Esri'
        ),
        dl.Marker(position=[lat, lon])
    ])

def create_sensor_dashboard(sensor_id, sensor_data):
    """Creates a dashboard section for a single sensor."""
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

    # Create metric cards with icons
    metric_cards = [
        create_metric_card(icon, label, value)
        for icon, label, value in metric_data
    ]

    # Create water level card
    water_level_cm = sensor_data.get('water_level', 0)  # Default to 0 if not available
    water_level_card = create_water_level_card(water_level_cm)

    # Combine all metric cards including water level
    all_cards = metric_cards + [water_level_card]

    # Extract GPS data
    latitude = sensor_data.get('latitude', initial_air_quality[sensor_id]['latitude'])
    longitude = sensor_data.get('longitude', initial_air_quality[sensor_id]['longitude'])

    # Create map section with satellite view
    map_section = create_map_section(latitude, longitude)

    # Create a Card Group for metrics
    metrics_group = dbc.Row(
        all_cards,
        className="mb-3",
        style={"gap": "20px"}  # Adjust gap between cards
    )

    # Create a Card for the sensor
    sensor_card = dbc.Card(
        [
            dbc.CardHeader(f"เซ็นเซอร์นาข้าว {get_sensor_area(sensor_id)}", className="card-header"),
            dbc.CardBody(
                [
                    # Air Quality Metrics
                    metrics_group,
                    # GPS Map
                    html.Div(map_section, className='gps-map-section', style={"marginTop": "20px"})
                ]
            ),
        ],
        className="graph-card",
        style={"width": "100%"},
    )

    return sensor_card

def get_sensor_area(sensor_id):
    """Returns the area name based on sensor ID."""
    sensor_areas = {
        "nongseua": "หนองเสือปทุมธานี",
        "supanburi": "สุพรรณบุรี"
    }
    return sensor_areas.get(sensor_id, "Unknown Area")

# Layout for responsive dimensions
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
                dcc.Interval(id='interval-component', interval=2 * 1000, n_intervals=0),  # Update every 2 seconds

                # Sensors Dashboard
                html.Div(
                    id='sensors-dashboard',
                    children=[
                        # Sensor cards will be dynamically inserted here
                    ]
                ),

                # Powered by RaasPal text at the bottom
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

@app.callback(
    Output('sensors-dashboard', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Fetch data from Flask server
    try:
        response = requests.get(FLASK_URL)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        # In case of connection error, use initial values
        data = initial_air_quality

    sensor_sections = []
    for sensor_id, sensor_data in data.items():
        # Merge with initial data to ensure all fields are present
        merged_data = {**initial_air_quality.get(sensor_id, {}), **sensor_data.get("airquality", {})}
        # Include GPS data
        merged_data["latitude"] = sensor_data.get("gps", {}).get("latitude", merged_data.get("latitude", 0))
        merged_data["longitude"] = sensor_data.get("gps", {}).get("longitude", merged_data.get("longitude", 0))
        # Include water level
        merged_data["water_level"] = sensor_data.get("airquality", {}).get("water_level", merged_data.get("water_level", 0))

        # Create sensor dashboard section
        sensor_card = create_sensor_dashboard(sensor_id, merged_data)
        sensor_sections.append(
            dbc.Row(
                dbc.Col(sensor_card, width=12),
                className="mb-4"
            )
        )

    return sensor_sections

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True, dev_tools_ui=False, dev_tools_props_check=False)
