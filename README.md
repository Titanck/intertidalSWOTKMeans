# 🔍 IntertidalSWOT Tool

Generate Digital Elevation Models (DEM) of Intertidal Zones from SWOT Altimetry Data PIXC using K-means Clustering

## 🚀 Installation

To install the dependencies required by the script, please run the following command:

conda env create -f IntertiKmeans.yaml<br>

## 🔧 User Parameters

Edit the params.txt file in data folder 


### Input Parameters
   **Parameter**       | **Type**               | **Description**                                                                                                                                                     | **Default**       | **Required** |
 |---------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|--------------|
 | **`FileAOI`**       | File (Shapefile, GeoJSON, KML, GPKG) | Path to the **Area of Interest (AOI)** file. Defines the geographic zone for DEM generation.                                                                     | -                 | ✅ Yes        |
 | **`FileTypeAOI`**   | String                | Type of the AOI file. Supported formats: `shapefile`, `geojson`, `kml`, `gpkg`.                                                                                 | -                 | ✅ Yes        |
 | **`BeginDate`**     | Date (YYYY-MM-DD)     | Start date for SWOT data selection. Data before this date will be ignored.                                                                                       | -                 | ✅ Yes        |
 | **`EndDate`**       | Date (YYYY-MM-DD)     | End date for SWOT data selection. Data after this date will be ignored.                                                                                         | -                 | ✅ Yes        |
 | **`Method`**        | String                | Classification method for elevation data. Options: `kmeans`, `dbscan`, `manual`.                                                                                 | `kmeans`          | ❌ No         |
 | **`Reso`**          | Integer (meters)      | Spatial resolution of the output DEM (in meters). Lower values = higher precision but longer processing time.                                               | `10`              | ❌ No         |
 | **`WaterThreshold`** | Float (meters)       | Elevation threshold to classify water areas. Values below this threshold are considered water.                                                               | `0.0`             | ❌ No         |
 | **`DistMaxInterpo`** | Integer (meters)      | Maximum distance for interpolation of missing data. Values beyond this distance will not be interpolated.                                                     | `100`             | ❌ No
 | **`DataWebsite`**   | URL or Path           | URL or local path to the **SWOT data source** (e.g., [NASA PO.DAAC](https://podaac.jpl.nasa.gov/swot)).                     | -                 | ✅ Yes        |
 | **`Interpolateur`** | String                | Interpolation method for DEM generation. Options: `idw`, `kriging`, `linear`.                                                                                   | `idw`             | ❌ No         |
 | **`MAJ_data`**      | Boolean (`True`/`False`) | If `True`, the tool automatically updates SWOT data from `DataWebsite` before processing. If `False`, uses local data.                          | `False`           | ❌ No

To authenticate with your Earthdata account at https://search.earthdata.nasa.gov/, you can create a .env file at the root of the project with your credentials, then run this command.<br>

echo "EARTHDATA_USERNAME=your_username" >> .env<br>
echo "EARTHDATA_PASSWORD=your_password" >> .env<br>

Otherwise, to authenticate with your Hydroweb account at "https://hydroweb.next.theia-land.fr/api", you can create a .env file at the root of the project with your credentials, then run this command.<br>

echo "APIKEY_HYDROWEB=your_APIkey" >> .env<br>
---

## 📂 Project Structure
Put your AOI file in AOI folder. The results will be saved to the output folder. The SWOT images will be written in input folder<br>

├── AOI<br>
│   └── YourAOI.csv/.kml/.shp/.geojson/.gpkg<br>
├── output<br>
│   └── YourAOI_BeginDate_EndDate_Method<br>
│       └── Parquet<br>
│	└── results<br>
│	    └── figRecap.png<br>
│	    └── MethodYourAOIBeginDate_EndDate.tif
│	└── SWOTFiles
│	    └── list_granules_YourAOI.txt
├── code
│   └── src
│       └── intertidal_topo.py
│	└── swot_images_interface.py
│   └──IntertidalKMeans.py
│   └──run_intertidalKMeans.sh
│
├── IntertiKmeans.yml
├── .gitignore
└── README.md

---

## 🌍 Data Source

SWOT data is accessed from [https://search.earthdata.nasa.gov](https://search.earthdata.nasa.gov) or [https://hydroweb.next.theia-land.fr/api](https://hydroweb.next.theia-land.fr/api).<br>
You must have a NASA EarthData or a Hydroweb account to download data.
