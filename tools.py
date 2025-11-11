import ee
import matplotlib.pyplot as plt
import requests
from io import BytesIO

import matplotlib.patches as mpatches
import matplotlib.patheffects as PathEffects

from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize
from matplotlib.colorbar import ColorbarBase
import numpy as np
from PIL import Image
import urllib.request
# import rasterio
import pandas as pd

ee.Authenticate()
ee.Initialize()

class Collection():
    def __init__(self, 
            source, 
            boundaries,
            start_date=None,
            end_date=None,
            img = None,
            mask = None,
            new_name = None,
            scale = None,
            reprojection = None,
            reducer = None):
        self.boundaries = boundaries
        if start_date and end_date:
            if img:
                collection = (ee.ImageCollection(source)
                    .select(img)
                    .filterDate(start_date, end_date)
                    .filterBounds(self.boundaries)
                )
            else:
                collection = (ee.ImageCollection(source)
                    .filterDate(start_date, end_date)
                    .filterBounds(self.boundaries)
                )
        else:
            if img:
                collection = (ee.ImageCollection(source)
                    .select(img)
                    .filterBounds(self.boundaries)
                )
            else:
                collection = (ee.ImageCollection(source)
                    .filterBounds(self.boundaries)
                )
        if reducer:
            collection = collection.map(
                lambda image: image.reduceResolution(reducer=reducer, bestEffort=True, maxPixels=1024)
            )
        if reprojection:
            collection = collection.map(lambda image: image.reproject(
                crs=reprojection['crs'], 
                scale=reprojection['scale']
            ))
        if mask:
            collection = collection.map(lambda image: image.updateMask(mask))   
        if scale and new_name:
            collection = collection.map(
                lambda image: image.select(img)
                    .multiply(scale)
                    .rename(new_name)
            )
        elif scale:
            collection = collection.map(
                lambda image: image.select(img)
                    .multiply(scale)
            )
        elif new_name:
            collection = collection.map(
                lambda image: image.select(img)
                    .rename(new_name)
            )
        self.collection = collection
        self.events = {}
    def get_event(self, start_date, end_date, name, type = None) -> None:
        if type == 'sum':
            event = self.collection.filterDate(start_date, end_date).sum().clip(self.boundaries)
        elif type == 'median':
            event = self.collection.filterDate(start_date, end_date).median().clip(self.boundaries)
        elif type == 'min':
            event = self.collection.filterDate(start_date, end_date).min().clip(self.boundaries)
        elif type == 'max':
            event = self.collection.filterDate(start_date, end_date).max().clip(self.boundaries)
        elif type == 'std':
            event = self.collection.filterDate(start_date, end_date).std().clip(self.boundaries)
        elif type == 'first':   
            event = self.collection.filterDate(start_date, end_date).first().clip(self.boundaries)
        elif type == 'last':
            event = self.collection.filterDate(start_date, end_date).last().clip(self.boundaries)
        elif type == 'count':
            event = self.collection.filterDate(start_date, end_date).count().clip(self.boundaries)
        elif type == 'moisac':
            event = self.collection.filterDate(start_date, end_date).mosaic().clip(self.boundaries)
        elif type == 'mean':
            event = self.collection.filterDate(start_date, end_date).mean().clip(self.boundaries)
        else: # mean
            event = self.collection.filterDate(start_date, end_date).mean().clip(self.boundaries)
        self.events.update({name: event})
    def get_diff_event(self, name1, name2, new_name)    :
        event1 = self.events[name1]
        event2 = self.events[name2]
        diff_event = event2.subtract(event1).clip(self.boundaries)
        self.events.update({new_name: diff_event})
    def set_viz_params(self, params):
        self.viz_params = params
    def plot_event(self, name, title, legend_label=None):
        event = self.events[name]
        url = event.getThumbURL({
                **self.viz_params,
                'region': self.boundaries,
                'dimensions': 512
            })
        with urllib.request.urlopen(url) as f:
            img = np.array(Image.open(f).convert("RGB"))
        

        bounds = self.boundaries.bounds().getInfo()['coordinates'][0]
        lons, lats = zip(*bounds)
        extent = [min(lons), max(lons), min(lats), max(lats)]

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(img, extent=extent, origin="upper")

        # Etiquetas y ejes
        ax.set_xlabel("Longitud", fontsize=12)
        ax.set_ylabel("Latitud", fontsize=12)
        ax.set_title(title, fontsize=14)
        plt.xticks(rotation=45)  # inclinamos etiquetas del eje X

        # Leyenda opcional
        if legend_label:
            # === Colorbar (leyenda del mapa) ===
            if "min" in self.viz_params and "max" in self.viz_params and "palette" in self.viz_params:
                vmin = self.viz_params["min"]
                vmax = self.viz_params["max"]
                colors = self.viz_params["palette"]
                cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)
                norm = Normalize(vmin=vmin, vmax=vmax)

                # Colorbar a la derecha
                cax = fig.add_axes([0.15, -0.02, 0.6, 0.03])  # [x0, y0, width, height]
                cb = ColorbarBase(cax, cmap=cmap, norm=norm, orientation='horizontal')
                cb.set_label(self.viz_params.get("value", "value")+ " ["+ self.viz_params.get("unit", "")+ "]", fontsize=10)
        # x0, x1 = ax.get_xlim()
        # y0, y1 = ax.get_ylim()
        # arrow_len = (y1 - y0) * 0.05  
        # ax.arrow(x1 + (x1 - x0)*0.1, y1 - (y1 - y0)*0.1, 
        #         0, arrow_len, 
        #         head_width=(x1 - x0)*0.015, 
        #         head_length=arrow_len*0.3, 
        #         fc='k', ec='k')
        # text = ax.text(x1 + (x1 - x0)*0.1, y1 - (y1 - y0)*0.1, 'N', 
        #             ha='center', va='bottom', fontsize=12, fontweight='bold', color='k')
        # text.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='white')])

        plt.tight_layout(rect=[0, 0, 0.9, 1])  
        plt.show()
    def plot_timeseries(self, reducer=ee.Reducer.mean(), scale=7000, title=None, ylabel=None):
        """Genera una serie temporal promedio dentro de la región (self.boundaries)."""

        # Reducimos cada imagen al valor medio dentro del ROI
        def reduce_region(img):
            mean = img.reduceRegion(
                reducer=reducer,
                geometry=self.boundaries,
                scale=scale,
                maxPixels=1e9
            )
            return ee.Feature(None, mean.set('date', img.date().format('YYYY-MM-dd')))
        
        # Convertimos la colección en una lista de features con fecha y valor
        stats_fc = self.collection.map(reduce_region)
        stats = stats_fc.aggregate_array('features').getInfo()

        # Extraemos fechas y valores
        dates = []
        values = []
        for feature in stats_fc.getInfo()['features']:
            props = feature['properties']
            if 'date' in props and len(props) > 1:
                dates.append(props['date'])
                # Tomamos la primera propiedad que no sea 'date'
                val_key = [k for k in props.keys() if k != 'date'][0]
                values.append(props[val_key])

        # Graficamos con matplotlib
        plt.figure(figsize=(8, 4))
        plt.plot(dates, values, 'o-', markersize=3, linewidth=1)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel('Fecha')
        plt.ylabel(ylabel or 'Valor medio')
        plt.title(title or 'Serie temporal')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

    def to_timeseries_df(self, reducer=ee.Reducer.mean(), scale=7000):
        def safe_add_date(img):
            """Asegura que la imagen tenga un 'system:time_start'."""
            time = ee.Algorithms.If(
            img.propertyNames().contains('system:time_start'),
            img.get('system:time_start'),
            ee.Date.parse(
                'yyyyMMdd', ee.String(img.get('system:index')).slice(0, 8)
            ).millis()
            )
            return img.set('system:time_start', time)

        # Aplicar la corrección a toda la colección
        collection = self.collection.map(safe_add_date)

        def reduce_region(img):
            """Reduce cada imagen a un valor dentro de la región."""
            mean_dict = img.reduceRegion(
                reducer=reducer,
                geometry=self.boundaries,
                scale=scale,
                maxPixels=1e9
            )
            date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
            return ee.Feature(None, mean_dict.combine(ee.Dictionary({'date': date})))

        # Convertir a FeatureCollection
        fc = collection.map(reduce_region)

        # Descargar como lista de features
        features = fc.getInfo()['features']

        # Convertir a DataFrame
        rows = []
        for f in features:
            props = f['properties']
            if 'date' not in props:
                continue
            values = {k: v for k, v in props.items() if k != 'date'}
            row = {'date': props['date'], **values}
            rows.append(row)

        df = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date'])
        return df


    def get_info(self):
        return self.collection.getInfo()