import os
import xarray as xr
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import contextily as ctx
import geopandas as gpd
from shapely.geometry import box
import re
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

class SWOTApp:
    MIN_POINTS = 1000  # Seuil minimal de points à l'intérieur de la bounding box

    def __init__(self, root, filepaths, bounding_box, icon_path=None):
        self.root = root
        self.filepaths = filepaths
        self.bounding_box = bounding_box
        self.index = 0
        self.selected_files = []

        # Configuration de l'icône de la fenêtre
        if icon_path:
            try:
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((32, 32), Image.LANCZOS)  # Redimensionne si nécessaire
                icon = ImageTk.PhotoImage(icon_image)
                root.iconphoto(True, icon)
            except Exception as e:
                print(f"Impossible de charger l'icône : {e}")

        self.label = tk.Label(root, text="", wraplength=800, justify="left")
        self.label.pack(pady=10)
        self.canvas = None

        self.keep_btn = tk.Button(root, text="Keep this file", command=self.on_keep)
        self.keep_btn.pack(side="left", expand=True, fill="x")
        self.skip_btn = tk.Button(root, text="Ignore this file", command=self.on_skip)
        self.skip_btn.pack(side="right", expand=True, fill="x")

        self.show_next_file()

    def filtering_data_set(self, ds):
        lat = ds['latitude'].values.flatten()
        lon = ds['longitude'].values.flatten()
        height = ds['height'].values.flatten()
        classification = ds['classification'].values.flatten()
        mask = ~pd.isnull(height)
        lat = lat[mask]
        lon = lon[mask]
        height = height[mask]
        classification = classification[mask]
        df = pd.DataFrame({
            'lat': lat,
            'lon': lon,
            'height': height,
            'classification': classification
        })
        return df[df['classification'] == 4].sample(frac=0.5)

    def plot_scatter(self, df, filepath):
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df['lon'], df['lat']),
            crs="EPSG:4326"
        )
        gdf = gdf.to_crs(epsg=3857)
        fig, ax = plt.subplots(figsize=(16, 10))
        mean_height = df['height'].mean()
        std_height = df['height'].std()
        vmin = mean_height - std_height
        vmax = mean_height + std_height
        gdf.plot(
            ax=ax,
            column='height',
            cmap='terrain',
            markersize=0.5,
            vmin=vmin,
            vmax=vmax,
            legend=True,
            legend_kwds={'label': "Height (m)"}
        )
        minx, miny, maxx, maxy = self.bounding_box
        bbox_geom = gpd.GeoDataFrame(
            geometry=[box(minx, miny, maxx, maxy)],
            crs="EPSG:4326"
        ).to_crs(epsg=3857).total_bounds
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14)
        filename = os.path.basename(filepath)
        match = re.match(r"SWOT_L2_HR_PIXC_(\d{3})_(\d{3})_(\d{3}[LR])_(\d{8})T\d+", filename)
        if match:
            cycle, swot_pass, tile, date_str = match.groups()
            date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            title = f"Cycle {cycle} | Pass {swot_pass} | Tile {tile} | Date {date_formatted}"
        else:
            title = f"File : {Path(filename).name}"
        ax.set_title(title)
        return fig

    def show_next_file(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        while self.index < len(self.filepaths):
            filepath = self.filepaths[self.index]
            self.label.config(text=f"File {self.index + 1}/{len(self.filepaths)}:\n{filepath}")
            try:
                ds = xr.open_dataset(filepath, group="pixel_cloud", engine="h5netcdf")
                sample = self.filtering_data_set(ds)
                in_bbox = sample[
                    (sample['lon'] >= self.bounding_box[0]) &
                    (sample['lon'] <= self.bounding_box[2]) &
                    (sample['lat'] >= self.bounding_box[1]) &
                    (sample['lat'] <= self.bounding_box[3])
                ]
                # if len(in_bbox) < self.MIN_POINTS:
                #     print(f"Not enough points ({len(in_bbox)}) in the bounding box pour {filepath}. Ignored.")
                #     self.index += 1
                #     continue
                print(f"Number of points to plot : {len(in_bbox)}")
                fig = self.plot_scatter(in_bbox, filepath)
                self.canvas = FigureCanvasTkAgg(fig, master=self.root)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill="both", expand=True)
                self.root.update_idletasks()
                plt.close(fig)
                return
            except Exception as e:
                print(f"Error on {filepath}: {e}")
                self.index += 1
        self.label.config(text="All files have been processed.")
        self.keep_btn.config(state="disabled")
        self.skip_btn.config(state="disabled")
        print("Files kept :", self.selected_files)
        self.root.after(500, self.root.destroy)

    def on_keep(self):
        self.selected_files.append(self.filepaths[self.index])
        self.index += 1
        self.show_next_file()

    def on_skip(self):
        self.index += 1
        self.show_next_file()

def afficher_fichiers(filepaths, bounding_box):
    root = tk.Tk()
    root.title("IntertidalSWOT")
    icon_path = "./src/icone.png"
    icon_pathSWOT = "./src/icon_swot.jpeg"
    app = SWOTApp(root, filepaths, bounding_box, icon_pathSWOT)
    root.mainloop()
    return app.selected_files