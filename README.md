# Andalucía Landuse Web Viewer

This application visualizes land use data (Forest and Nature Reserves) from OpenStreetMap for Andalucía using a Web Interface.

## Requirements

- Python 3.x
- PostgreSQL database named `nyc`
- PostGIS extension enabled
- User `postgres` with password `postgres`

## Installation

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your PostgreSQL database is running and configured:
   ```sql
   CREATE DATABASE nyc;
   -- Connect to nyc
   CREATE EXTENSION postgis;
   ```

## Usage

1. Run the Flask application (ensure venv is activated):

   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   http://127.0.0.1:5000

3. **In the Web Interface**:
   - Click **"Cargar Datos"** to load the shapefile into the database.
   - Select a filter (All, Forest, or Nature Reserve).
   - Click **"Visualizar Datos"** to see the map and total area.
   - Click on any colored zone in the map to see a tooltip with its Name and Area.

## Features

- **Web Interface**: Modern web UI using Leaflet.js.
- **Data Loading**: Reads shapefile and uploads to PostGIS.
- **Visualization**: Interactive map with color-coded zones.
- **Filtering**: Filter by type.
- **Area Calculation**: Calculates total area in hectares.
- **Interactive Tooltips**: Click to see details.
