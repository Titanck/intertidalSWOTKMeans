from dotenv import load_dotenv
from src import intertidal_topo
import os 
from src import swot_images_interface
import importlib
import pandas as pd
from pathlib import Path
import panel as pn
import sys
pn.extension()

importlib.reload(intertidal_topo)
importlib.reload(swot_images_interface)

def OpenByType(AOIPath, AOIType):
    drivers = {'shp':'ESRI Shapefile', 'geojson':'GeoJSON', 'kml':'KML', 'gpkg':'GPKG'}
    if AOIType.lower() == 'csv':
        BoundingBox, AOIWGS84 = intertidal_topo.opening_AOI_csv(AOIPath)
    else:
        driver = drivers.get(AOIType.lower())
        if driver is None:
            raise ValueError(f"Format AOI inconnu : {AOIType}")
        BoundingBox, AOIWGS84 = intertidal_topo.opening_AOI(AOIPath, driver)
    return BoundingBox, AOIWGS84
def GetPassWord(DataWebsite):
        load_dotenv(dotenv_path=".././data/.env")
        if DataWebsite =='Earthaccess':
            if not os.path.exists(".././data/.env"):
                EarthDataUserName, EarthDataPassword = intertidal_topo.get_connexion_id_earthaccess()
            else:
                EarthDataUserName = os.getenv("EARTHDATA_USER_EARTHACCESS")
                EarthDataPassword = os.getenv("EARTHDATA_PASS_EARTHACCESS")
            return EarthDataUserName, EarthDataPassword, ""
        elif DataWebsite =='Hydroweb':
            if not os.path.exists(".././data/.env"):
                ApiKeyHydroweb = intertidal_topo.get_connexion_id_hydroweb()
            else:
                ApiKeyHydroweb = os.getenv("APIKEY_HYDROWEB")
            return "", "", ApiKeyHydroweb
def ListingSWOTFiles(SWOTFiles, PathSWOT):
    SWOTFiles_sns_doublons = list(set(SWOTFiles))
    fichier = Path(f"{PathSWOT}list_granules_{AOIName}.txt")
    SWOTFiles_sns_doublons_str = [str(granule) for granule in SWOTFiles_sns_doublons]
    fichier.write_text("\n".join(SWOTFiles_sns_doublons_str), encoding="utf-8")

if __name__ == "__main__":
    AOIName=sys.argv[1]              
    AOIType=sys.argv[2]                     
    StartDate=sys.argv[3]                   
    EndDate=sys.argv[4]                      
    Reso=int(sys.argv[5])                      
    Method=sys.argv[6]                        
    WaterThreshold=int(sys.argv[7])                  
    DistMaxInterpo=float(sys.argv[8])                 
    OutputEPSG=sys.argv[9]               
    DataWebsite=sys.argv[10]           
    Interpolateur = sys.argv[11]                      
    MAJ_data=sys.argv[12]                        

    AOIPath = f".././AOI/{AOIName}.{AOIType.lower()}"
    Project = os.path.splitext(os.path.basename(AOIPath))[0]
    PathProject = f".././output/{Project}{StartDate}_{EndDate}{Method}"
    PathSWOT = f"{PathProject}/SWOTFiles/"
    os.makedirs(PathSWOT, exist_ok=True)
    PathOutput = f"{PathProject}/results/"
    os.makedirs(PathOutput, exist_ok=True)
    PathSWOTParquet = f"{PathProject}/Parquet/"
    os.makedirs(PathSWOTParquet, exist_ok=True)

    BoundingBox, AOIWGS84 = OpenByType(AOIPath, AOIType)
    EarthDataUserName, EarthDataPassword, ApiKeyHydroweb = GetPassWord(DataWebsite)

    if MAJ_data == 'True':
        if DataWebsite =='Earthaccess':
            SWOTFiles = intertidal_topo.download_swot_pixelcloud_from_aoi_earthaccess(BoundingBox, StartDate, EndDate, PathSWOT, EarthDataUserName, EarthDataPassword)
        if DataWebsite =='Hydroweb':
            SWOTFiles = intertidal_topo.download_swot_pixelcloud_from_aoi_hydroweb(BoundingBox, StartDate, EndDate, PathSWOT, ApiKeyHydroweb, AOIName)
        SWOTFiles = intertidal_topo.keep_highest_version(SWOTFiles)
        if Method == "Kmeans" or Method == None: 
            SWOTFiles = swot_images_interface.afficher_fichiers(SWOTFiles, BoundingBox)
            print(SWOTFiles)
        ListingSWOTFiles(SWOTFiles, PathSWOT)
        SWOTData = intertidal_topo.filtering_data(SWOTFiles, AOIWGS84)
        intertidal_topo.deleteSWOTFiles(SWOTFiles)
        SWOTData.to_parquet(PathSWOTParquet+AOIName+StartDate+".parquet", engine="pyarrow", index=False)
    else:
        SWOTData = pd.read_parquet(PathSWOTParquet+AOIName+StartDate+".parquet", engine="pyarrow")
    SWOTData = intertidal_topo.mask_water(SWOTData, WaterThreshold)
    SWOTData["X"], SWOTData["Y"] = intertidal_topo.LonLat2XY(SWOTData["longitude"], SWOTData["latitude"], 4326, OutputEPSG)
    GridSWOT, x_binning, y_binning, Width, Height, XGrid, YGrid = intertidal_topo.grid(BoundingBox, Reso, OutputEPSG)
    if Method == 'Mean5p100':
        GridSWOT = intertidal_topo.binning(SWOTData, GridSWOT, intertidal_topo.mean_lowest_5_percent, x_binning, y_binning, "height")
    if Method == "Kmeans" or Method == None:
        SWOTData = intertidal_topo.Kmeans(SWOTData)
        SWOTData, IMaxSig0, IMinSig0 = intertidal_topo.association_classe_topo(SWOTData)
        SWOTData = intertidal_topo.apply_mask(SWOTData, "height", "height_mask", "Intertidal height")
        GridSWOT = intertidal_topo.gridding(SWOTData, GridSWOT, x_binning, y_binning, DistMaxInterpo, Interpolateur)
    GridSWOT['Longitude'], GridSWOT['Latitude'] = intertidal_topo.LonLat2XY(GridSWOT['X'], GridSWOT['Y'], OutputEPSG, 4326)
    intertidal_topo.fig_recap(GridSWOT, SWOTData, PathOutput, Method+StartDate+"_"+EndDate+"recap.png", BoundingBox)
    intertidal_topo.height_maps_per_tile(SWOTData, BoundingBox, output_dir=PathOutput+"height_per_tile")
    if Method == "Kmeans" or Method == None:
        intertidal_topo.plot_classif_swot(SWOTData, PathOutput, Method+"classif.png", BoundingBox, IMaxSig0, IMinSig0)
    intertidal_topo.export_raster(GridSWOT, XGrid, AOIName, Height, Width, PathOutput, Project, Method, OutputEPSG, Reso, StartDate, EndDate)