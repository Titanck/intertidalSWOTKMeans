# 🔍 IntertidalSWOT Tool

This project allows you to generate a Digital Elevation Model (DEM) of Intertidal zone from SWOT altimetry files.<br>

---<br>

## 🚀 Installation

To install the dependencies required by the script, please run the following command:<br>

conda env create -f earthaccess.yaml<br>

---<br>

## 🔧 User Parameters

Edit the following section in the script:<br>

#--------------------------------USER INPUTS-----------------------------------#<br>
AOIName               #Name of the AOI (Area Of Interest) <br> 
AOIType                       #AOI file type : shp/geojson/KML/GPKG/CSV <br>
StartDate                     #SWOT Granule research Start Date 'yyy-mm-dd' format<br>
EndDate =                      #SWOT Granule research End Date 'yyy-mm-dd' format<br>
Reso =                                 #Final resolution of the MNT<br>
Method =                         #Method for extract intertidal topography : Kmeans/Mean5p100<br>
WaterTreshold =                    #Maximum threshold of the prior_water_probability parameter<br>
DistMaxInterpo =                #Maximum search distance for points by the interpolators<br>
OutputEPSG =                    #EPSG of output files<br>
DataWebsite =            #Website where SWOT data are downloaded : Earthaccess/Hydroweb<br>

To authenticate with your Earthdata account at https://search.earthdata.nasa.gov/, you can create a .env file at the root of the project with your credentials, then run this command.<br>

echo "EARTHDATA_USERNAME=your_username" >> .env<br>
echo "EARTHDATA_PASSWORD=your_password" >> .env<br>

Otherwise, to authenticate with your Hydroweb account at "https://hydroweb.next.theia-land.fr/api", you can create a .env file at the root of the project with your credentials, then run this command.<br>

echo "APIKEY_HYDROWEB=your_APIkey" >> .env<br>
---

## 📂 Project Structure
Put your AOI file in AOI folder. The results will be saved to the output folder. The SWOT images will be written in input folder<br>
\`\`\`<br>
.<br>
├── main.ipynb<br>
├── AOI<br>
│   └── your_AOI.csv/.kml/.shp/.geojson/.gpkg<br>
├── tests<br>
│   └── your_AOI/<br>
│       └── input/<br>
│	└── output/<br>
├── src/<br>
│   └──intertidal_topo.py<br>
│   └──swot_images_interface.py<br>
├── earthaccess.yml<br>
├── .gitignore<br>
└── README.md<br>
\`\`\`<br>

---

## 🌍 Data Source

SWOT data is accessed from [https://search.earthdata.nasa.gov](https://search.earthdata.nasa.gov) or [https://hydroweb.next.theia-land.fr/api](https://hydroweb.next.theia-land.fr/api).<br>
You must have a NASA EarthData or a Hydroweb account to download data.
