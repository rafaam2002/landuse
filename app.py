import streamlit as st
import geopandas as gpd
from sqlalchemy import create_engine
import folium
from streamlit_folium import st_folium
import os
import zipfile
import requests
import io

# Constants
# Try to get connection string from secrets, otherwise use localhost
try:
    if "DB_CONNECTION_STR" in st.secrets:
        DB_CONNECTION_STR = st.secrets["DB_CONNECTION_STR"]
    else:
        DB_CONNECTION_STR = "postgresql://postgres:postgres@localhost:5432/nyc"
except FileNotFoundError:
    # Secrets file not found, use localhost
    DB_CONNECTION_STR = "postgresql://postgres:postgres@localhost:5432/nyc"
except Exception:
    # Any other error accessing secrets (e.g. StreamlitSecretNotFoundError which might not be importable easily)
    DB_CONNECTION_STR = "postgresql://postgres:postgres@localhost:5432/nyc"

TABLE_NAME = "andalucia_usos_suelo"
DATA_URL = "https://www.uhu.es/jluis.dominguez/AGI/andalucia-landuse.shp.zip"
LOCAL_DATA_DIR = "andalucia-landuse.shp"
SHAPEFILE_NAME = "gis_osm_landuse_a_free_1.shp"

st.set_page_config(page_title="Andalucía Landuse Viewer", layout="wide")

def get_db_engine():
    return create_engine(DB_CONNECTION_STR)

def load_data_to_db():
    try:
        # Check if data exists locally
        shp_path = os.path.join(LOCAL_DATA_DIR, SHAPEFILE_NAME)
        if not os.path.exists(shp_path):
            if not os.path.exists(LOCAL_DATA_DIR):
                    os.makedirs(LOCAL_DATA_DIR)
            with st.spinner("Descargando datos..."):
                response = requests.get(DATA_URL)
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall(LOCAL_DATA_DIR)

        # Read Shapefile
        with st.spinner("Leyendo Shapefile..."):
            gdf = gpd.read_file(shp_path)
        
        # Filter columns
        gdf = gdf[['fclass', 'name', 'geometry']]
        
        # Connect to DB and upload
        engine = get_db_engine()
        
        # Drop table if exists and create new
        with st.spinner("Subiendo a PostGIS..."):
            gdf.to_postgis(TABLE_NAME, engine, if_exists='replace', index=False)
            
        st.success("Datos cargados correctamente en la base de datos.")
        return True
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return False

@st.cache_data
def get_data_from_db(filter_val):
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM \"{TABLE_NAME}\""
        if filter_val != "All":
            query += f" WHERE fclass = '{filter_val}'"
        else:
            query += " WHERE fclass IN ('forest', 'nature_reserve')"

        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        return gdf
    except Exception as e:
        st.error(f"Error al leer de la base de datos: {str(e)}")
        return None

# Sidebar
st.sidebar.title("Controles")

if st.sidebar.button("Cargar Datos"):
    load_data_to_db()

filter_option = st.sidebar.radio(
    "Filtrar por tipo:",
    ("All", "forest", "nature_reserve")
)

# Main Area
st.title("Andalucía Landuse Viewer")

# Fetch Data
gdf = get_data_from_db(filter_option)

if gdf is not None and not gdf.empty:
    # Calculate Area
    gdf_proj = gdf.to_crs(epsg=25830)
    total_area = gdf_proj.area.sum() / 10000.0 # ha
    
    # Add area column to gdf for tooltip
    gdf['area_ha'] = (gdf_proj.area / 10000.0).round(1)
    
    st.sidebar.metric("Superficie Total", f"{total_area:,.1f} ha")

    # Map
    with st.spinner("Generando mapa..."):
        # Center map on the data
        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)

        # Style function
        def style_function(feature):
            fclass = feature['properties']['fclass']
            color = 'forestgreen' if fclass == 'forest' else 'limegreen'
            return {
                'fillColor': color,
                'color': color,
                'weight': 1,
                'fillOpacity': 0.6
            }

        # Add GeoJSON
        # We can add a tooltip
        folium.GeoJson(
            gdf,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['name', 'fclass', 'area_ha'],
                aliases=['Nombre:', 'Tipo:', 'Superficie (ha):'],
                localize=True,
                style="font-family: sans-serif; font-size: 12px; padding: 3px; background-color: rgba(255, 255, 255, 0.9);",
                sticky=True
            )
        ).add_to(m)

        st_folium(m, width=1000, height=600, returned_objects=[])

elif gdf is not None and gdf.empty:
    st.warning("No hay datos para mostrar. Asegúrate de cargar los datos primero.")
