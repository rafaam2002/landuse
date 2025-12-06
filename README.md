# Andalucía Landuse Streamlit Viewer

This application visualizes land use data (Forest and Nature Reserves) from OpenStreetMap for Andalucía using a **Streamlit** Web Interface.

**Live Demo:** [https://rafaam2002-landuse-app-rkn4sg.streamlit.app/](https://rafaam2002-landuse-app-rkn4sg.streamlit.app/)

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

1. Run the Streamlit application (ensure venv is activated):

   ```bash
   streamlit run app.py
   ```

2. The application will open in your default web browser (usually http://localhost:8501).

3. **In the Web Interface**:
   - **Sidebar**: Use the controls to load data and filter by type.
   - **Cargar Datos**: Click to load the shapefile into the database.
   - **Filtrar**: Select 'All', 'forest', or 'nature_reserve'.
   - **Map**: Interactive map showing the selected zones. Hover to see details.
   - **Stats**: Total area in hectares is displayed in the sidebar.

## Features

- **Pure Python UI**: Built with Streamlit.
- **Interactive Map**: Powered by Folium.
- **Data Loading**: Reads shapefile and uploads to PostGIS.
- **Filtering & Stats**: Dynamic filtering and area calculation.
