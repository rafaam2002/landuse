import tkinter as tk
from tkinter import ttk, messagebox
import geopandas as gpd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import zipfile
import requests
import io

# Constants
DB_CONNECTION_STR = "postgresql://postgres:postgres@localhost:5432/nyc"
TABLE_NAME = "ANDALUCIA_USOS_SUELO"
DATA_URL = "https://www.uhu.es/jluis.dominguez/AGI/andalucia-landuse.shp.zip"
LOCAL_DATA_DIR = "andalucia-landuse.shp"
SHAPEFILE_NAME = "gis_osm_landuse_a_free_1.shp"

class LanduseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Andalucía Landuse Viewer")
        self.root.geometry("1000x800")

        # Main Layout
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        self.map_frame = ttk.Frame(self.root)
        self.map_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Controls
        self.btn_load = ttk.Button(self.control_frame, text="Cargar datos", command=self.load_data)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar(value="All")
        ttk.Label(self.control_frame, text="Filtrar:").pack(side=tk.LEFT, padx=5)
        
        self.radio_all = ttk.Radiobutton(self.control_frame, text="Todos", variable=self.filter_var, value="All")
        self.radio_all.pack(side=tk.LEFT, padx=2)
        
        self.radio_forest = ttk.Radiobutton(self.control_frame, text="Forest", variable=self.filter_var, value="forest")
        self.radio_forest.pack(side=tk.LEFT, padx=2)
        
        self.radio_nature = ttk.Radiobutton(self.control_frame, text="Nature Reserve", variable=self.filter_var, value="nature_reserve")
        self.radio_nature.pack(side=tk.LEFT, padx=2)

        self.btn_visualize = ttk.Button(self.control_frame, text="Visualizar datos", command=self.visualize_data)
        self.btn_visualize.pack(side=tk.LEFT, padx=5)

        self.lbl_area = ttk.Label(self.control_frame, text="Superficie Total: - ha")
        self.lbl_area.pack(side=tk.RIGHT, padx=10)

        # Matplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.map_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Tooltip annotation
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.hover)

        self.gdf_display = None

    def load_data(self):
        try:
            # Check if data exists locally
            shp_path = os.path.join(LOCAL_DATA_DIR, SHAPEFILE_NAME)
            if not os.path.exists(shp_path):
                # Download if not exists (though user said it is unzipped, we handle the case)
                if not os.path.exists(LOCAL_DATA_DIR):
                     os.makedirs(LOCAL_DATA_DIR)
                     # Logic to download would go here if needed, but assuming local presence based on prompt
                     # If strictly following "read from link", we might need to download every time or check.
                     # Given "already downloaded" in prompt introduction but "proceed with reading from link" in functionality.
                     # I will implement download logic just in case it's missing or to satisfy "read from link".
                     response = requests.get(DATA_URL)
                     z = zipfile.ZipFile(io.BytesIO(response.content))
                     z.extractall(LOCAL_DATA_DIR)

            # Read Shapefile
            gdf = gpd.read_file(shp_path)
            
            # Filter columns
            gdf = gdf[['fclass', 'name', 'geometry']]
            
            # Connect to DB and upload
            engine = create_engine(DB_CONNECTION_STR)
            
            # Drop table if exists and create new
            # geopandas to_postgis handles table creation. 'replace' drops it.
            gdf.to_postgis(TABLE_NAME, engine, if_exists='replace', index=False)
            
            messagebox.showinfo("Éxito", "Datos cargados correctamente en la base de datos.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")

    def visualize_data(self):
        try:
            engine = create_engine(DB_CONNECTION_STR)
            filter_val = self.filter_var.get()
            
            query = f"SELECT * FROM \"{TABLE_NAME}\""
            if filter_val != "All":
                query += f" WHERE fclass = '{filter_val}'"
            else:
                # Requirement says: "forest or nature_reserve, or process all"
                # But description says "visualize info of green zones (forest and nature_reserve)"
                # And "filter info showing type (forest or nature_reserve) or process all existing data"
                # It's slightly ambiguous if "all" means ALL landuse or just forest+nature_reserve.
                # "Se pide ... aplicación ... para visualizar información de 'zonas verdes' (forest y nature_reserve)."
                # So likely "All" means both forest and nature_reserve.
                query += " WHERE fclass IN ('forest', 'nature_reserve')"

            self.gdf_display = gpd.read_postgis(query, engine, geom_col='geometry')
            
            if self.gdf_display.empty:
                messagebox.showwarning("Aviso", "No hay datos para mostrar.")
                return

            # Reproject to 25830 for area calculation
            gdf_proj = self.gdf_display.to_crs(epsg=25830)
            total_area = gdf_proj.area.sum() / 10000.0 # m2 to hectares
            self.lbl_area.config(text=f"Superficie Total: {total_area:.1f} ha")

            # Plot
            self.ax.clear()
            
            # Color mapping
            colors = {'forest': 'forestgreen', 'nature_reserve': 'limegreen'}
            
            # We can plot directly with 'fclass' column for categorical coloring if we want, 
            # but manual control is easier for specific colors.
            
            # Plot forest
            forests = self.gdf_display[self.gdf_display['fclass'] == 'forest']
            if not forests.empty:
                forests.plot(ax=self.ax, color='forestgreen', label='Forest')
                
            # Plot nature_reserve
            reserves = self.gdf_display[self.gdf_display['fclass'] == 'nature_reserve']
            if not reserves.empty:
                reserves.plot(ax=self.ax, color='limegreen', label='Nature Reserve')

            self.ax.set_title("Andalucía Green Zones")
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al visualizar: {str(e)}")

    def update_annot(self, ind):
        # Get the index of the polygon
        # ind["ind"] contains indices of the artists (polygons) that contain the mouse
        # This is tricky with geopandas plot.
        # A better way for tooltips in matplotlib with geopandas is checking containment manually or using pick_event.
        # However, 'motion_notify_event' is requested.
        pass

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            # We need to find which polygon is under the mouse
            # Transforming mouse coordinates to map coordinates
            # This is complex with simple matplotlib plot. 
            # We will iterate over the geometry to find containment. 
            # Optimization: Use spatial index if possible, but for this assignment simple check might suffice or be slow.
            # Given it's a GUI assignment, let's try a simple approach.
            
            found = False
            if self.gdf_display is not None:
                # Convert event coords to data coords
                # Point(event.xdata, event.ydata)
                # Check containment
                # This can be slow for many polygons.
                # Let's rely on 'picker' if possible, but standard plot doesn't enable it easily for all patches.
                pass
                
            # Implementing a basic tooltip might be too heavy if we iterate all polygons on every move.
            # Let's try to use 'contains' on the whole GDF with a small buffer around the point?
            # Or just skip complex tooltip for now and focus on 'click' if mouseover is too hard.
            # Requirement: "Al posicionar el ratón o clicar... mostraría un tooltip"
            # Let's implement 'click' (button_press_event) as it's lighter, or hover with optimization.
            
            # For now, let's leave the hook.
            pass

    def on_click(self, event):
        # Optional requirement: Tooltip on click or hover. Click is safer for performance.
        if event.inaxes != self.ax: return
        if self.gdf_display is None: return
        
        from shapely.geometry import Point
        pt = Point(event.xdata, event.ydata)
        
        # Check intersection
        # We can use spatial index for speed
        # sindex = self.gdf_display.sindex
        # possible_matches_index = list(sindex.intersection(pt.bounds))
        # possible_matches = self.gdf_display.iloc[possible_matches_index]
        # precise_matches = possible_matches[possible_matches.contains(pt)]
        
        # Since we don't know if rtree is installed (dependency of sindex), we might fallback to slow check
        # But 'geopandas' usually comes with it.
        
        # Let's try simple iteration for the "optional" part if dataset is not huge.
        # Or just use the first match.
        
        match = self.gdf_display[self.gdf_display.contains(pt)]
        if not match.empty:
            row = match.iloc[0]
            name = row['name'] if row['name'] else "Unknown"
            # Calculate area of this specific feature
            # Need to reproject single geometry
            geom_proj = gpd.GeoSeries([row.geometry], crs=self.gdf_display.crs).to_crs(epsg=25830)
            area_ha = geom_proj.area.iloc[0] / 10000.0
            
            self.annot.xy = (event.xdata, event.ydata)
            text = f"{name}\n{area_ha:.1f} ha"
            self.annot.set_text(text)
            self.annot.set_visible(True)
            self.canvas.draw()
        else:
            if self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LanduseApp(root)
    # Bind click event for tooltip
    app.canvas.mpl_connect("button_press_event", app.on_click)
    root.mainloop()
