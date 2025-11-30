from flask import Flask, render_template, jsonify, request
import geopandas as gpd
from sqlalchemy import create_engine
import os
import zipfile
import requests
import io
import json

app = Flask(__name__)

# Constants
DB_CONNECTION_STR = "postgresql://postgres:postgres@localhost:5432/nyc"
TABLE_NAME = "ANDALUCIA_USOS_SUELO"
DATA_URL = "https://www.uhu.es/jluis.dominguez/AGI/andalucia-landuse.shp.zip"
LOCAL_DATA_DIR = "andalucia-landuse.shp"
SHAPEFILE_NAME = "gis_osm_landuse_a_free_1.shp"

def get_db_engine():
    return create_engine(DB_CONNECTION_STR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load_data', methods=['POST'])
def load_data():
    try:
        # Check if data exists locally
        shp_path = os.path.join(LOCAL_DATA_DIR, SHAPEFILE_NAME)
        if not os.path.exists(shp_path):
            if not os.path.exists(LOCAL_DATA_DIR):
                    os.makedirs(LOCAL_DATA_DIR)
            response = requests.get(DATA_URL)
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(LOCAL_DATA_DIR)

        # Read Shapefile
        gdf = gpd.read_file(shp_path)
        
        # Filter columns
        gdf = gdf[['fclass', 'name', 'geometry']]
        
        # Connect to DB and upload
        engine = get_db_engine()
        
        # Drop table if exists and create new
        gdf.to_postgis(TABLE_NAME, engine, if_exists='replace', index=False)
        
        return jsonify({"status": "success", "message": "Datos cargados correctamente."})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data')
def get_data():
    try:
        filter_val = request.args.get('filter', 'All')
        engine = get_db_engine()
        
        query = f"SELECT * FROM \"{TABLE_NAME}\""
        if filter_val != "All":
            query += f" WHERE fclass = '{filter_val}'"
        else:
            query += " WHERE fclass IN ('forest', 'nature_reserve')"

        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        if gdf.empty:
            return jsonify({"type": "FeatureCollection", "features": []})

        # Calculate area for each feature
        gdf_proj = gdf.to_crs(epsg=25830)
        gdf['area_ha'] = gdf_proj.area / 10000.0
        gdf['area_ha'] = gdf['area_ha'].round(1)

        # Convert to GeoJSON
        return gdf.to_json()
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        filter_val = request.args.get('filter', 'All')
        engine = get_db_engine()
        
        query = f"SELECT * FROM \"{TABLE_NAME}\""
        if filter_val != "All":
            query += f" WHERE fclass = '{filter_val}'"
        else:
            query += " WHERE fclass IN ('forest', 'nature_reserve')"

        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        if gdf.empty:
            return jsonify({"area_ha": 0})

        # Reproject to 25830 for area calculation
        gdf_proj = gdf.to_crs(epsg=25830)
        total_area = gdf_proj.area.sum() / 10000.0 # m2 to hectares
        
        return jsonify({"area_ha": round(total_area, 1)})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
