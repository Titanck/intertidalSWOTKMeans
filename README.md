# IntertidalSWOTKMeans

IntertidalSWOTKMeans is a tool for generating Digital Elevation Models (DEM) of Intertidal Zones from SWOT Altimetry Data PIXC using K-means Clustering
---
## Installation

To install the dependencies required by the script, please run the following command:

```bash
conda env create -f IntertiKmeans.yaml
```
---
## User Parameters

The tool's input parameters must be specified in the params.txt file located in the “data” folder. Parameters should be added as individual lines. The user can add as many lines as desired. The parameters to be specified are detailed in the following section: 

---
## Input Parameters
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
 | **`DataWebsite`**   | String           | Name of the website where to search for data. Supported websites: `Earthaccess` and `Hydroweb`                     | -                 | ✅ Yes        |
 | **`Interpolateur`** | String                | Interpolation method for DEM generation. Options: `idw`, `moyenne`, `linear`.                                                                                   | `idw`             | ❌ No         |
 | **`MAJ_data`**      | Boolean (`True`/`False`) | If `True`, the tool automatically updates SWOT data from `DataWebsite` before processing. If `False`, uses local data.                          | `False`           | ❌ No
---
## User Guide
To run the **IntertidalSWOTKMeans Tool**, follow these steps:

1. **Open a terminal** in the `code` folder of the project.
2. **Run the script** using the following command:

```bash
bash ./run_intertidalKMeans.sh
```
To authenticate with your Earthdata account at https://search.earthdata.nasa.gov/, you can create a .env file at the root of the project with your credentials, then run this command.<br>
echo "EARTHDATA_USERNAME=your_username" >> .env<br>
echo "EARTHDATA_PASSWORD=your_password" >> .env<br>

Otherwise, to authenticate with your Hydroweb account at "https://hydroweb.next.theia-land.fr/api", you can create a .env file at the root of the project with your credentials, then run this command.<br>

echo "APIKEY_HYDROWEB=your_APIkey" >> .env<br>
---
## Project Structure
Put your AOI file in AOI folder. The results will be saved to the output folder. The SWOT images will be written in input folder<br>

├── AOI<br>
│   └── YourAOI.csv/.kml/.shp/.geojson/.gpkg<br>
│<br>
├── output<br>
│   └── YourAOI_BeginDate_EndDate_Method<br>
│       └── Parquet<br>
│	└── results<br>
│	    └── figRecap.png<br>
│	    └── MethodYourAOIBeginDate_EndDate.tif<br>
│	└── SWOTFiles<br>
│	    └── list_granules_YourAOI.txt<br>
│<br>
├── code<br>
│   └── src<br>
│       └── intertidal_topo.py<br>
│	└── swot_images_interface.py<br>
│   └──IntertidalKMeans.py<br>
│   └──run_intertidalKMeans.sh<br>
│<br>
├── IntertiKmeans.yml<br>
├── .gitignorev
└── README.md<br>

---

## Data Source

SWOT data is accessed from [https://search.earthdata.nasa.gov](https://search.earthdata.nasa.gov) or [https://hydroweb.next.theia-land.fr/api](https://hydroweb.next.theia-land.fr/api).<br>
You must have a NASA EarthData or a Hydroweb account to download data.
