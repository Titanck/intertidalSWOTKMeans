# IntertidalSWOTKMeans
IntertidalSWOTKMeans was developed as part of the SWOT 4 COST project. One of the objectives of this proposal is to develop methods for generating digital elevation models (DEMs) of the intertidal topography using SWOT PIXC satellite imagery. This GitHub project is a tool for generating Digital Elevation Models (DEM) of Intertidal Zones from SWOT Altimetry Data PIXC using K-means Clustering. This tool is based on the method described in the article Evaluating SWOT’s Interferometric Capabilities for Mapping Intertidal Topography[¹]

---

## Installation Guide
To install the dependencies required by the script, please run the following command:

```bash
conda env create -f IntertiKmeans.yaml
```
---

## User Guide
To authenticate with your Earthdata account at https://search.earthdata.nasa.gov/, you can create a .env file at the root of the project with your credentials, then run this command.
```bash
echo "EARTHDATA_USERNAME=your_username" >> .env
echo "EARTHDATA_PASSWORD=your_password" >> .env
```
Otherwise, to authenticate with your Hydroweb account at "https://hydroweb.next.theia-land.fr/api", you can create a .env file at the root of the project with your credentials, then run this command.<br>

```bash
echo "APIKEY_HYDROWEB=your_APIkey" >> .env
```
### User Parameters
The tool's input parameters must be specified in the params.txt file located in the “data” folder. Parameters should be added as individual lines. The user can add as many lines as desired. The parameters to be specified are detailed in the following section: 

---

### Input Parameters
   **Parameter**       | **Type**               | **Description**                                                                                                                                                     | **Default**       | **Required** |
 |---------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|--------------|
 | **`FileAOI`**       | File (Shapefile, GeoJSON, KML, GPKG) | Path to the **Area of Interest (AOI)** file. Defines the geographic zone for DEM generation.                                                          | -                 | ✅ Yes       |
 | **`FileTypeAOI`**   | String                | Type of the AOI file. Supported formats: `shapefile`, `geojson`, `kml`, `gpkg`.                                                                                      | -                 | ✅ Yes        |
 | **`BeginDate`**     | Date (YYYY-MM-DD)     | Start date for SWOT data selection. Data before this date will be ignored.                                                                                       | -                 | ✅ Yes        |
 | **`EndDate`**       | Date (YYYY-MM-DD)     | End date for SWOT data selection. Data after this date will be ignored.                                                                                         | -                 | ✅ Yes        |
 | **`Method`**        | String                | Classification method for elevation data. Options: `Kmeans`, `Mean5p100`.                                                                                 | `Kmeans`          | ❌ No         |
 | **`Reso`**          | Integer (meters)      | Spatial resolution of the output DEM (in meters). Lower values = higher precision but longer processing time.                                               | `20`              | ❌ No         |
 | **`WaterThreshold`** | Float (meters)       | Elevation threshold to classify water areas. Values below this threshold are considered water.                                                               | `1`             | ❌ No         |
 | **`DistMaxInterpo`** | Integer (meters)      | Maximum distance for interpolation of missing data. Values beyond this distance will not be interpolated.                                                     | `2e3`            | ❌ No
 | **`DataWebsite`**   | String           | Name of the website where to search for data. Supported websites: `Earthaccess` and `Hydroweb`                                                                        | -                 | ✅ Yes        |
 | **`Interpolateur`** | String                | Interpolation method for DEM generation. Options: `IDW`, `Moyenne`.                                                                                   | `Moyenne`             | ❌ No         |
 | **`MAJ_data`**      | Boolean (`True`/`False`) | If `True`, the tool automatically updates SWOT data from `DataWebsite` before processing. If `False`, uses local data.                          | `True`           | ❌ No

### Launching the script
To run the **IntertidalSWOTKMeans Tool**, follow these steps:

1. **Open a terminal** in the `code` folder of the project.
2. **Run the script** using the following command:
To run the tool for the **first time**, execute the following command to make the script executable and then run it:

```bash
chmod +x run_intertidal_swot.sh  # Only needed once to make the script executable
./run_intertidal_swot.sh         # Run the script
```
If the .env file has not been created, the script will prompt you for your login credentials. 

---

## Project Structure
Put your AOI file in AOI folder. The results will be saved to the output folder. The SWOT images will be written in input folder<br>
``` bash
├── AOI
│   └── FileAOI.csv/.kml/.shp/.geojson/.gpkg
│
├── output
│   └── FileAOI_BeginDate_EndDate_Method
│       └── Parquet
│	└── results
│	    └── figRecap.png
│	    └── MethodYourAOIBeginDate_EndDate.tif
│	└── SWOTFiles
│	    └── list_granules_FileAOI.txt
│
├── code
│   └── src
│       └── intertidal_topo.py
│	└── swot_images_interface.py
│   └──IntertidalKMeans.py
│   └──run_intertidalKMeans.sh
│
├── IntertiKmeans.yml
└── README.md
```
---

## Data Source
SWOT data is accessed from [https://search.earthdata.nasa.gov](https://search.earthdata.nasa.gov) or [https://hydroweb.next.theia-land.fr/api](https://hydroweb.next.theia-land.fr/api).<br>
You must have a NASA EarthData or a Hydroweb account to download data.


## Contributors
Tancrède MAYTIE
Edward SALAMEH <br>
[¹]: https://doi.org/10.1016/j.rse.2024.114401 
