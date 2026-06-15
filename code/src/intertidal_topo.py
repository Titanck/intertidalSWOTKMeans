import os
import geopandas as gpd
from shapely.geometry import Point
import earthaccess
import numpy as np
import pandas as pd
from tqdm import tqdm
import re
from pathlib import Path
from collections import defaultdict
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pyproj import Transformer
from scipy.stats import binned_statistic_2d
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import griddata
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.spatial import cKDTree
from shapely.ops import unary_union
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.ticker as ticker
import zipfile
from py_hydroweb.client import Client, DownloadBasket
from datetime import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable


def unzip_file(zip_path, extract_to=None):
    """Unzip File

    Args:
        zip_path (str): The location of the zip file
        extract_to (str, optional): The location of the unzip file. Defaults to None.
    """
    zip_path = Path(zip_path)

    if extract_to is None:
        extract_to = zip_path.parent
    else:
        extract_to = Path(extract_to)

    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    print(f"Extraction terminée dans : {extract_to}")


def get_connexion_id_earthaccess():
    """Ask inline the username and password for Earthdata account

    Returns:
        str: Username and password
    """
    earth_data_username = input("What is your username for https://search.earthdata.nasa.gov/ ?")
    earth_data_password = input("What is your password for https://search.earthdata.nasa.gov/ ?")
    return earth_data_username, earth_data_password


def get_connexion_id_hydroweb():
    """Ask inline the API for Hydroweb account

    Returns:
        str: API key 
    """
    hydroweb_api_key = input("What is your API Key for https://search.earthdata.nasa.gov/ ?")
    return hydroweb_api_key


def opening_AOI(aoi_path, driver):
    """
    Opens an Area of Interest (AOI) vector file, reprojects it to WGS84,
    computes its bounding box, and returns the unified geometry.

    Parameters:
    -----------
    aoi_path : str
        Path to the vector file representing the Area of Interest (e.g., GeoJSON, Shapefile).

    Returns:
    --------
    tuple
        - bounding_box : tuple
            Bounding box coordinates in the format (minx, miny, maxx, maxy), in WGS84.
        - aoi_wgs84 : shapely.geometry.GeometryCollection or Polygon
            Unified geometry of the Area of Interest reprojected to WGS84.
    """
    try:
        aoi = gpd.read_file(aoi_path, driver=driver)
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier '{aoi_path}' est introuvable.")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier : {e}")

    if aoi.empty:
        raise ValueError("Le fichier fourni ne contient aucune géométrie.")

    aoi_wgs84 = aoi.to_crs(epsg=4326)
    minx, miny, maxx, maxy = aoi_wgs84.total_bounds
    bounding_box = (minx, miny, maxx, maxy)
    aoi_union = aoi_wgs84.union_all()

    return bounding_box, aoi_union
    

def opening_AOI_csv(aoi_path):
    """Open a csv file

    Args:
        aoi_path (str): Location of the Area Of Interest

    Returns:
        tuple, GeoDataFrame: BoundingBox and Coordinates of the Area Of Interest
    """
    try:   
        df = pd.read_csv(aoi_path)

        if not {'latitude', 'longitude'}.issubset(df.columns):
            raise ValueError("Le fichier CSV doit contenir les colonnes 'latitude' et 'longitude'.")

        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        if gdf.empty or gdf.geometry.isna().all():
            raise ValueError("Aucune géométrie valide dans le fichier.")
        merged_points = unary_union(gdf.geometry)
        if merged_points.geom_type == 'Point':
            raise ValueError("Impossible de créer un polygone avec un seul point.")
        elif merged_points.geom_type == 'MultiPoint':
            aoi_polygon = merged_points.convex_hull
        else:
            aoi_polygon = merged_points.convex_hull
        minx, miny, maxx, maxy = aoi_polygon.bounds
        bounding_box = (np.float64(minx), np.float64(miny), np.float64(maxx), np.float64(maxy))

        return bounding_box, aoi_polygon
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier '{aoi_path}' est introuvable.")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture ou du traitement du fichier : {e}")
    

def download_swot_pixelcloud_from_aoi_earthaccess(bounding_box, start_date, end_date, path_swot, earth_data_user_name, earth_data_password):
    """
    Downloads SWOT Level 2 Pixel Cloud (HR_PIXC) granules for a given area and time range,
    using Earthdata credentials, and saves them to a specified local directory.

    Parameters:
    -----------
    bounding_box : tuple
        The spatial extent of the area of interest, formatted as (minx, miny, maxx, maxy) in WGS84 coordinates.

    start_date : str
        Start date of the time range in ISO 8601 format (e.g., '2023-01-01T00:00:00Z').

    end_date : str
        End date of the time range in ISO 8601 format (e.g., '2023-01-31T23:59:59Z').

    path_swot : str
        Path to the local directory where the downloaded SWOT granule files will be stored.

    earth_data_user_name : str
        NASA Earthdata login username.

    earth_data_password : str
        NASA Earthdata login password.

    Returns:
    --------
    list of str
        A list containing the file paths of the downloaded SWOT granule files.
    """
    delta = 0.03
    lonmin, latmin, lonmax, latmax = bounding_box
    lonmin_new = lonmin + delta
    latmin_new = latmin + delta
    lonmax_new = lonmax - delta
    latmax_new = latmax - delta
    bounding_box = (lonmin_new, latmin_new, lonmax_new, latmax_new)
    os.environ["EARTHDATA_USERNAME"] = earth_data_user_name
    os.environ["EARTHDATA_PASSWORD"] = earth_data_password
    shrt_nm = 'SWOT_L2_HR_PIXC_2.0'
    auth = earthaccess.login(strategy="environment")
    granules = earthaccess.search_data(
        short_name=shrt_nm,
        bounding_box=bounding_box,
        temporal=(start_date, end_date)
    )
    print(f"{len(granules)} granules trouvés dans l'AOI.")
    downloaded_files = earthaccess.download(granules, local_path=path_swot)
    return downloaded_files


def download_swot_pixelcloud_from_aoi_hydroweb(bounding_box, start_date, end_date, path_swot, api_key, aoi_name):
    """Downloads Data from Hydroweb

    Args:
        bounding_box (Bounding): Area where SWOT Granules will be searched
        path_swot (str): Location of the project
        api_key (str): API Key
        aoi_name (str): Name of the zip file

    Returns:
        _type_: _description_
    """
    fichZIP = aoi_name+".zip"
    start_iso = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00.000Z")
    end_iso = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00.000Z")
    collection = "SWOT_L2_HR_PIXC"
    client = Client(
        hydroweb_api_url="https://hydroweb.next.theia-land.fr/api", 
        api_key=api_key
    )
    basket = DownloadBasket(download_name="my_download_basket")
    basket.add_collection(
            collection_id=collection, 
            bbox=list(bounding_box), 
            query={
                "start_datetime": {"gte": start_iso},
                "end_datetime": {"lte": end_iso},
            },
        )
    client.submit_and_download_zip(
            download_basket=basket, zip_filename=fichZIP, output_folder=path_swot
        )
    PathZip = path_swot+"/"+fichZIP
    unzip_file(PathZip)
    folder_path = os.path.join(path_swot, collection, collection)
    nc_files = [
    os.path.join(folder_path, f)
    for f in os.listdir(folder_path)
    if f.endswith(".nc")
    ]
    return nc_files


def deleteSWOTFiles(SWOTFiles):
    for file in SWOTFiles:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error deleting file {file}: {e}")


def keep_highest_version(files):
    """
    Filters a list of file paths to keep only the highest version of each unique base filename.

    Parameters:
    -----------
    files : list of str
        List of file paths to SWOT granules (NetCDF format).

    Returns:
    --------
    list of str
        List of file paths corresponding to the highest version for each unique base filename.
    """
    version_map = defaultdict(list)
    for f in files:
        p = Path(f)
        name = p.name
        match = re.match(r"(.+?)_(\d{2})\.nc$", name)
        if match:
            base_name, version = match.groups()
            version_map[base_name].append((int(version), str(p)))
    highest_version_files = [
        max(file_list, key=lambda x: x[0])[1]
        for file_list in version_map.values()
    ]
    print(f"{len(highest_version_files)} granules with the most recent version.")
    return highest_version_files


def LonLat2XY(x_deb, y_deb, EPSG_init, EPSG_fin):
    """
    Converts geographic coordinates (longitude, latitude) from one coordinate reference system (CRS)
    to another using EPSG codes, a projection for example.

    Parameters:
    -----------
    x_deb : float
        Longitude in the source CRS (EPSG_init).
    
    x_fin : float
        Latitude in the source CRS (EPSG_init).
    
    EPSG_init : int or str
        EPSG code of the input coordinate reference system.
    
    EPSG_fin : int or str
        EPSG code of the target coordinate reference system.

    Returns:
    --------
    tuple of float
        Transformed coordinates (x_fin, y_fin) in the target CRS.
    """
    transformer = Transformer.from_crs(f"EPSG:{EPSG_init}", f"EPSG:{EPSG_fin}", always_xy=True)
    x_fin, y_fin = transformer.transform(x_deb, y_deb)
    return x_fin, y_fin


def grid(bounding_box, reso, OutputEPSG):
    """
    Generates a regular grid over a given bounding box at a specified resolution,
    projected in EPSG:2154 (Lambert-93), and returns the grid along with bin edges and dimensions.

    Parameters:
    -----------
    bounding_box : tuple
        Bounding box in WGS84 coordinates (EPSG:4326), formatted as (min_lon, min_lat, max_lon, max_lat).

    reso : float
        Resolution of the grid cells in meters (applied in both x and y directions in projected space).

    Returns:
    --------
    tuple
        - grid_swot : pandas.DataFrame
            DataFrame containing the center coordinates (X, Y) of the grid cells in EPSG:2154.
        - x_binning : numpy.ndarray
            Array of bin edges along the x-axis.
        - y_binning : numpy.ndarray
            Array of bin edges along the y-axis.
        - nx : int
            Number of grid cells along the x-axis.
        - ny : int
            Number of grid cells along the y-axis.
        - X : numpy.ndarray
            2D array of x coordinates (meshgrid).
        - Y : numpy.ndarray
            2D array of y coordinates (meshgrid).
    """
    bb_lon = np.array([bounding_box[0], bounding_box[2]])
    bb_lat = np.array([bounding_box[1], bounding_box[3]])
    bb_proj = LonLat2XY(bb_lon, bb_lat, 4326, OutputEPSG)
    x_binning = np.arange(bb_proj[0][0], bb_proj[0][1]+ 2 * reso, reso)
    y_binning = np.arange(bb_proj[1][0], bb_proj[1][1]+ 2 * reso, reso)
    x_fin = np.arange(bb_proj[0][0], bb_proj[0][1]+ reso, reso)
    y_fin = np.arange(bb_proj[1][0], bb_proj[1][1]+ reso, reso)
    X, Y = np.meshgrid(x_fin, y_fin)
    grid_swot = pd.DataFrame({'X': X.flatten(), 'Y': Y.flatten()})
    nx, ny = np.shape(x_fin)[0], np.shape(y_fin)[0]
    return grid_swot, x_binning, y_binning, nx, ny, X, Y


def filtering_data(SWOTFiles, AOIWGS84):
    """
    Filters SWOT pixel cloud data by spatial location (within the Area of Interest)
    and by classification (open water), and returns the filtered results as a GeoDataFrame.

    Parameters:
    -----------
    SWOTFiles : list of str
        List of file paths to SWOT Level 2 HR_PIXC NetCDF files.

    AOIWGS84 : shapely.geometry or geopandas.GeoSeries/GeoDataFrame
        The Area of Interest geometry in WGS84 (EPSG:4326) used to spatially filter the data.

    Returns:
    --------
    geopandas.GeoDataFrame
        Filtered SWOT pixel cloud data containing only points:
        - located within the AOI, and
        - classified as open water (classification code == 4).
    """
    pattern = re.compile(
        r"SWOT_L2_HR_PIXC_"
        r"(?P<cycle>\d+)_"
        r"(?P<pass>\d+)_"
        r"(?P<tile>\d+[LR])_"
        r"(?P<date_debut>\d{8}T\d{6})_"
        r"(?P<date_fin>\d{8}T\d{6})_"
        r"(?P<version>[A-Z0-9]+)_"
        r"(?P<compteur>\d+).nc"
    )

    df_list = []
    for file in tqdm(SWOTFiles):
        filename = Path(file).name
        match = pattern.match(filename)
        meta = match.groupdict() if match else {}

        ds = xr.open_dataset(file, group="pixel_cloud", engine="h5netcdf")
        PIXC_subset = ds[[
            "height", "sig0", "coherent_power", "classification",
            "prior_water_prob", "water_frac", "bright_land_flag",
            "false_detection_rate", "inc"
        ]]
        df = PIXC_subset.to_dataframe().reset_index()

        for k, v in meta.items():
            df[k] = v

        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
            crs="EPSG:4326"
        )
        gdf = gdf[gdf.geometry.within(AOIWGS84)]
        gdf = gdf[gdf["classification"] == 4]

        df_list.append(gdf)

    final_df = pd.concat(df_list, ignore_index=True)
    return final_df


def plot_base(x, y, c, lo_mi, la_mi, lo_ma, la_ma, cmap, label='', norm=None, vmin=None, vmax=None):
    """
    Plots a scatter map of georeferenced points with color-coded values and a colorbar.

    Parameters:
    -----------
    x : array-like
        X-axis coordinates (e.g., longitude or projected x).

    y : array-like
        Y-axis coordinates (e.g., latitude or projected y).

    c : array-like
        Values used to color the points (e.g., height, classification, etc.).

    lo_mi : float
        Minimum limit for the x-axis (longitude or x).

    la_mi : float
        Minimum limit for the y-axis (latitude or y).

    lo_ma : float
        Maximum limit for the x-axis.

    la_ma : float
        Maximum limit for the y-axis.

    cmap : str or matplotlib.colors.Colormap
        Colormap used for the point values.

    label : str, optional
        Label for the colorbar (default is empty).

    norm : matplotlib.colors.Normalize, optional
        A normalization instance to scale luminance data (optional).

    vmin : float, optional
        Minimum value for color scaling (overrides automatic scaling).

    vmax : float, optional
        Maximum value for color scaling (overrides automatic scaling).

    Returns:
    --------
    None
        The function plots directly using matplotlib and does not return any object.
    """
    sc = plt.scatter(x=x, y=y, c=c, cmap=cmap, s=0.25, norm=norm, vmin=vmin, vmax=vmax)
    plt.xlim(lo_mi, lo_ma)
    plt.ylim(la_mi, la_ma)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True)
    cbar = plt.colorbar(sc)
    cbar.set_label(label)


def min_max_values(df, param):
    """Min and Max values of a column of df for plotting
    Args:
        df (Panda DataFrame)
        param (str): column of the dataframe for which the minimum and maximum values must be determined 

    Returns:
        _type_: _description_
    """
    mean_height = df[param].mean()
    std_height = df[param].std()
    vmin = mean_height - std_height
    vmax = mean_height + std_height
    return vmin, vmax


def fig_recap(swot_grid, param_swot, path_fig_recap, nom_fich, bounding_box):
    """
    Generates and saves a multi-panel summary figure showing various SWOT parameters
    and intertidal height over a given bounding box.

    Parameters:
    -----------
    swot_grid : pandas.DataFrame
        DataFrame containing gridded SWOT results, including columns 'Longitude', 'Latitude',
        and 'Intertidal Height'.

    param_swot : pandas.DataFrame
        DataFrame containing raw SWOT pixel data with columns such as 'longitude', 'latitude',
        'height', 'sig0', 'coherent_power', and 'inc'.

    path_fig_recap : str
        Path to the directory where the output figure will be saved.

    nom_fich : str
        Filename (with extension, e.g., 'recap.png') for the saved figure.

    bounding_box : tuple
        Bounding box for the plots in WGS84 coordinates, formatted as (lon_min, lat_min, lon_max, lat_max).

    Returns:
    --------
    None
        The function saves the generated figure to disk and does not return any object.
    """
    lon_min, lat_min, lon_max, lat_max = bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]
    vmin_ps, vmax_ps = min_max_values(param_swot, "height")
    plt.figure(figsize=(20, 15))

    plt.subplot(4, 2, 1)
    plot_base(param_swot["longitude"], param_swot["latitude"], param_swot["height"], lon_min, lat_min, lon_max, lat_max, 
              cmap='terrain', label='Height (m)', vmin=vmin_ps, vmax=vmin_ps)

    plt.subplot(4, 2, 2)
    plot_base(param_swot["longitude"], param_swot["latitude"], param_swot["sig0"], lon_min, lat_min, lon_max, lat_max,
              cmap='gray', label='Backscattering (dB)', norm=mcolors.LogNorm())

    plt.subplot(4, 2, 3)
    plot_base(param_swot["longitude"], param_swot["latitude"], param_swot["coherent_power"], lon_min, lat_min, lon_max, lat_max,
              cmap='gray', label='Coherent Power (dB)', norm=mcolors.LogNorm())

    plt.subplot(4, 2, 4)
    plot_base(param_swot["longitude"], param_swot["latitude"], param_swot["inc"], lon_min, lat_min, lon_max, lat_max,
              cmap='gray', label="Angle d'incidence (°)")
    
    plt.subplot(4, 2, 5)
    plot_base(param_swot["longitude"], param_swot["latitude"], param_swot["prior_water_prob"], lon_min, lat_min, lon_max, lat_max,
              cmap='viridis', label="Prior Water Probability")

    plt.subplot(4, 2, 6)
    plot_base(swot_grid["Longitude"], swot_grid["Latitude"], swot_grid["Intertidal height"], lon_min, lat_min, lon_max, lat_max,
              cmap='terrain', label='height (m)', vmin=vmin_ps, vmax=vmax_ps)
    
    plt.subplot(4, 2, 7)
    col_dict = {1: "red", 2: "orange", 3: "green", 4: "blue", 5: "purple", 6: "pink", 7: "magenta"}
    labels = np.array([
        "land", "land_near_water", "water_near_land", "open_water",
        "dark_water", "low_coh_water_near_land", "open_low_coh_water"
    ])
    cmap = ListedColormap([col_dict[k] for k in col_dict])
    norm_bins = np.arange(1.5, 8.5, 1)
    norm = mcolors.BoundaryNorm(boundaries=np.insert(norm_bins, 0, 0.5), ncolors=len(labels))
    fmt = plt.FuncFormatter(lambda val, _: labels[int(val - 1)] if 1 <= val <= 7 else '')
    sc4 = plt.scatter(x=param_swot["longitude"], y=param_swot["latitude"], c=param_swot["classification"],
              cmap=cmap, label='classification', norm=norm)
    plt.xlim(lon_min, lon_max)
    plt.ylim(lat_min, lat_max)
    plt.grid(True)
    cbar = plt.colorbar(sc4, ticks=np.arange(1, 8), format=fmt)
    plt.gca().set_aspect('equal', adjustable='box')
    cbar.set_label('Classification SWOT')
    os.makedirs(path_fig_recap, exist_ok=True)
    plt.savefig(os.path.join(path_fig_recap, f"{nom_fich}"))
    plt.close()


def height_maps_per_tile(param_swot, bounding_box, output_dir="height_per_tile"):
    """
    Generate and save a map of 'height' for each tile/pass/cycle/date combination in param_swot.

    Parameters
    ----------
    param_swot : pandas.DataFrame
        DataFrame containing raw SWOT pixel data with columns 'longitude', 'latitude',
        'height', 'tile', 'swot_pass', 'cycle', 'datedebut'.
    bounding_box : tuple
        Bounding box in WGS84 (lon_min, lat_min, lon_max, lat_max).
    output_dir : str
        Directory to save the generated maps (default 'height_per_tile').
    """
    os.makedirs(output_dir, exist_ok=True)

    lon_min, lat_min, lon_max, lat_max = bounding_box

    groups = param_swot.groupby(["tile", "pass", "cycle", "date_debut"])

    for (tile, swot_pass, cycle, datedebut), df in groups:
        if df.empty:
            continue

        fig, ax = plt.subplots(figsize=(10, 8))

        sc = ax.scatter(
            df["longitude"], df["latitude"],
            c=df["height"],
            cmap="terrain",
            s=2,
            vmin=df["height"].min(),
            vmax=df["height"].max()
        )

        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"Height - Tile {tile} | Pass {swot_pass} | Cycle {cycle} | Date {datedebut}")

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = plt.colorbar(sc, cax=cax)
        cbar.set_label("Height (m)")

        plt.grid(True)
        plt.tight_layout()

        filename = f"height_tile{tile}_pass{swot_pass}_cycle{cycle}_date{datedebut}.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close(fig)


def plot_classif_swot(param_swot, path_fig_recap, nom_fich, bounding_box, IMaxSig0, IMinSig0):
    """Plotting classification graphs

    Args:
        param_swot (df): containing all SWOT data
        path_fig_recap (str): Location of the output graphs
        nom_fich (str): file name
        bounding_box (tuple): geographical boundaries of the graph
        IMaxSig0 (int): label of the cluster with maximum sigma 0 value
        IMinSig0 (int): label of the cluster with minimum sigma 0 value
    """
    lon_min, lat_min, lon_max, lat_max = bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]
    col_dict = {IMaxSig0: "red", IMinSig0: "blue"}
    labels = ["mudflat", "water"]
    classes = list(col_dict.keys())
    cmap = ListedColormap([col_dict[k] for k in classes])
    norm_bins = np.sort(classes) + 0.5
    norm_bins = np.insert(norm_bins, 0, norm_bins[0] - 1.0)
    norm = BoundaryNorm(norm_bins, len(labels), clip=True)
    ticks = norm_bins[:-1] + np.diff(norm_bins) / 2
    fmt = ticker.FuncFormatter(lambda val, _: labels[classes.index(int(val))] if int(val) in classes else '')
    plt.subplot(1,1,1)
    sc4 = plt.scatter(x=param_swot["longitude"], y=param_swot["latitude"], c=param_swot["classe"],
              cmap=cmap, label='classification', norm=norm, s=0.25)
    plt.xlim(lon_min, lon_max)
    plt.ylim(lat_min, lat_max)
    cbar = plt.colorbar(sc4, ticks=ticks, format=fmt)
    plt.gca().set_aspect('equal', adjustable='box')
    cbar.set_label('Classification')
    plt.grid(True)
    os.makedirs(path_fig_recap, exist_ok=True)
    plt.savefig(os.path.join(path_fig_recap, f"{nom_fich}"))
    plt.close()

    plt.figure()
    sc5 = plt.scatter(x=param_swot["height"], y=param_swot["sig0_log"], c=param_swot["classe"],
              cmap=cmap, label='classification', norm=norm, s=0.25)
    cbar = plt.colorbar(sc5, ticks=ticks, format=fmt)
    cbar.set_label('Classification')
    plt.xlabel("height")
    plt.ylabel("sig0_log")
    plt.grid(True)
    os.makedirs(path_fig_recap, exist_ok=True)
    plt.savefig(os.path.join(path_fig_recap, f"dim{nom_fich}"))
    plt.close()


def mean_lowest_5_percent(values):
    """
    Computes the mean of the lowest 5% of non-NaN values in an array.

    Parameters:
    -----------
    values : array-like
        Input numeric values (e.g., water height observations).

    Returns:
    --------
    float
        Mean of the lowest 5% of values. Returns NaN if only Nan values are provided.
    """
    if np.all(np.isnan(values)):
        return np.nan  
    sorted_vals = np.sort(values)
    n = max(1, int(0.05 * len(values)))
    return np.nanmean(sorted_vals[:n])


def binning(swot_data, swot_grid, stat, x_binning, y_binning, param):
    """
    Aggregates SWOT data by applying a 2D binned statistic over specified grid bins,
    and adds the resulting statistic to the SWOT grid DataFrame.

    Parameters:
    -----------
    swot_data : pandas.DataFrame
        DataFrame containing SWOT pixel data with 'X', 'Y', and the parameter column.

    swot_grid : pandas.DataFrame
        Grid DataFrame to which the binned statistic will be added.

    stat : str or callable
        Statistic to compute within each bin (e.g., 'mean', 'median', 'max').

    x_binning : array-like
        Bin edges along the X-axis.

    y_binning : array-like
        Bin edges along the Y-axis.

    param : str
        Column name in `swot_data` for which the statistic is computed.

    Returns:
    --------
    pandas.DataFrame
        The `swot_grid` DataFrame updated with the computed binned statistic in the `param` column.
    """
    swot_data = apply_mask(swot_data, param, "height_mask", "Intertidal height")
    param_SWOT, ___, ____, ____ = binned_statistic_2d(
        x=swot_data["X"].values,
        y=swot_data["Y"].values,
        values=swot_data["Intertidal height"].values,
        statistic=stat,
        bins=[x_binning, y_binning]
    )
    swot_grid["Intertidal height"] = param_SWOT.T.flatten()
    return swot_grid


def Kmeans(Swot_data):
    """Kmeans processing

    Args:
        Swot_data (DataFrame): containing SWOT pixel data

    Returns:
        DataFrame: containing SWOT pixel data with classification
    """
    Swot_data["sig0_log"] = np.log10(Swot_data["sig0"])
    data_classif = ["height", "sig0_log"]
    scaler = StandardScaler()
    for data in data_classif:
        Swot_data.loc[:, data + "_scaled"] = scaler.fit_transform(Swot_data[data].values.reshape(-1, 1))
        Swot_data = Swot_data.dropna(subset=[data + "_scaled"])
    cols_classif = [col for col in Swot_data.columns if col.endswith(("_scaled"))]
    data_swot_mer_classif = Swot_data[cols_classif].copy()
    kmeans = KMeans(n_clusters=2, random_state=0)
    clusters = kmeans.fit_predict(data_swot_mer_classif)
    centroids = kmeans.cluster_centers_
    Swot_data.loc[:, 'cluster'] = clusters
    return Swot_data
    

def gridding(Swot_data, grid_swot, x_binning, y_binning, dist_max_interpo, Interpolateur):
    """
    Aggregates SWOT data by applying a 2D binned statistic over specified grid bins,
    and adds the resulting statistic to the SWOT grid DataFrame.

    Parameters:
    -----------
    swot_data : pandas.DataFrame
        DataFrame containing SWOT pixel data with 'X', 'Y', and the parameter column.

    swot_grid : pandas.DataFrame
        Grid DataFrame to which the binned statistic will be added.

    stat : str or callable
        Statistic to compute within each bin (e.g., 'mean', 'median', 'max').

    x_binning : array-like
        Bin edges along the X-axis.

    y_binning : array-like
        Bin edges along the Y-axis.

    param : str
        Column name in `swot_data` for which the statistic is computed.

    Returns:
    --------
    pandas.DataFrame
        The `swot_grid` DataFrame updated with the computed binned statistic in the `param` column.
    """
    Z_SWOT, _, _, _ = binned_statistic_2d(Swot_data["X"], Swot_data["Y"], Swot_data["Intertidal height"], statistic='mean', bins=[x_binning, y_binning])
    grid_swot['height_avg'] = Z_SWOT.T.flatten()
    if Interpolateur == "Moyenne":
        grid_swot['Intertidal height'] = Z_SWOT.T.flatten()
    if Interpolateur == "IDW":
        grid_swot['Intertidal height'] = interpolate_idw_massive(Swot_data, grid_swot['X'], grid_swot['Y'], dist_max_interpo)
        grid_swot.loc[grid_swot['height_avg'].isna(), 'Intertidal height'] = np.nan
    return grid_swot


def apply_mask(df, col_values, col_mask, new_colonne):
    """
    Applies a boolean mask to a column in a DataFrame.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the data.
    col_values : str
        Name of the column containing the values to mask.
    col_mask : str
        Name of the column containing the boolean mask (True = mask).
    new_colonne : str
        Name of the new column to store the masked values.

    Returns:
    --------
    pd.DataFrame
        DataFrame with the new column added.
    """
    df[new_colonne] = np.where(df[col_mask], np.nan, df[col_values])
    return df


def association_classes(data, data_classif, centroids):
    """
    Associates clusters with physical classes (water vs mudflat) based on the backscattering/coherent power parameter value.

    Parameters
    ----------
    data : pd.DataFrame
        Classified data containing a 'cluster' column. A 'classe' column will be added/updated.
    data_classif : list of str
        List of parameter names used for classification (without the `_scaled` suffix).
    centroids : np.ndarray
        Array (n_clusters, n_features) representing the cluster centroids in normalized space.

    Returns
    -------
    data : pd.DataFrame
        Original DataFrame with the 'classe' column updated (0 = water, 1 = mudflat).
    ind_max_sig0 : int
        Index of the cluster with the highest sigma0 value (water).
    ind_min_sig0 : int
        Index of the cluster with the lowest sigma0 value (mudflat).
    """
    indice_height = data_classif.index('height')

    ind_max = np.argmax(centroids[:, indice_height])  
    ind_min = np.argmin(centroids[:, indice_height])  

    data.loc[data['cluster'] == ind_max, 'classe'] = 0  #Mudflat
    data.loc[data['cluster'] == ind_min, 'classe'] = 1  #Water

    return data, ind_max, ind_min


def association_classe_topo(Swot_data):
    """Associates clusters with physical classes (mudflat vs water) based on the maximum height value.
    This function identifies the cluster with the highest height value and assigns it as 'mudflat' (class 0),
    while all other clusters are assigned as 'water' (class 1). It also updates the 'Intertidal height' column
    for points classified as mudflat.

    Parameters
    ----------
    Swot_data : pd.DataFrame
        DataFrame containing SWOT pixel data with 'height' and 'cluster' columns.
        A 'classe' column will be added or updated, and 'Intertidal height' will be populated for mudflat points.

    Returns
    -------
    tuple
        - Swot_data : pd.DataFrame
            DataFrame with the 'classe' column updated (0 = mudflat, 1 = water) and 'Intertidal height' set for mudflat points.
        - ind_max : int
            Index of the cluster with the maximum height (mudflat), always 0 in this implementation.
        - ind_min : int
            Index of the cluster with the minimum height (water), always 1 in this implementation.
    """
    idx_max_height = Swot_data['height'].idxmax()

    cluster_max_height = Swot_data.loc[idx_max_height, 'cluster']

    Swot_data['classe'] = 1 
    Swot_data.loc[Swot_data['cluster'] == cluster_max_height, 'classe'] = 0
    Swot_data.loc[Swot_data["classe"] == 0, 'Intertidal height'] = Swot_data["height"]
    return Swot_data, 0, 1


def interpolate_idw_massive(df_xyz, new_x, new_y, radius, power=2, batch_size=10000):
    """
    Performs Inverse Distance Weighting (IDW) interpolation in batch mode.

    This function applies IDW interpolation to a large grid of target points from a DataFrame of source points.
    The interpolation is performed in batches to optimize memory performance.

    Parameters
    ----------
    df_xyz : pandas.DataFrame
        DataFrame containing the columns 'X', 'Y', and 'height' representing coordinates
        and values to interpolate.
    new_x : np.ndarray
        2D or 1D array of X coordinates for the target grid points.
    new_y : np.ndarray
        2D or 1D array of Y coordinates for the target grid points. Must have the same shape as `new_x`.
    radius : float
        Search radius around each grid point to include neighboring points.
    power : float, optional
        Power of the inverse distance used for weight calculation (default = 2).
    batch_size : int, optional
        Number of target points to process at once (default = 10000).

    Returns
    -------
    interpolated_z : np.ndarray
        1D array of interpolated values for each (new_x, new_y) point.
        Points without neighbors within the specified radius are set to NaN.
    """
    grid_points = np.column_stack((new_x, new_y))
    interpolated_z = np.full(grid_points.shape[0], np.nan)

    tree = cKDTree(df_xyz[['X', 'Y']].values)

    for start in tqdm(range(0, grid_points.shape[0], batch_size), desc='IDW Interpolation'):
        end = min(start + batch_size, grid_points.shape[0])
        batch_points = grid_points[start:end]
        all_neighbors = tree.query_ball_point(batch_points, r=radius)

        for i, idxs in enumerate(all_neighbors):
            if not idxs:
                continue
            pts = df_xyz.iloc[idxs]
            dx = pts['X'].values - batch_points[i, 0]
            dy = pts['Y'].values - batch_points[i, 1]
            dists = np.hypot(dx, dy)

            if np.any(dists == 0):
                interpolated_z[start + i] = pts['height'].values[dists == 0][0]
            else:
                weights = 1 / dists**power
                interpolated_z[start + i] = np.dot(weights, pts['height'].values) / np.sum(weights)

    return interpolated_z


def nearest(swot_data, swot_grid, grid_x, grid_y, param):
    """
    Exports the 'Intertidal Height' grid data as a GeoTIFF raster file.

    Parameters:
    -----------
    grid_swot : pandas.DataFrame
        DataFrame containing the 'Intertidal Height' column.

    x_grid : numpy.ndarray
        2D array of grid x-coordinates (used to get shape).

    bbox : tuple
        Bounding box in WGS84 coordinates (minx, miny, maxx, maxy) defining raster extent.

    h : int
        Height (number of rows) of the raster.

    w : int
        Width (number of columns) of the raster.

    path_raster : str
        Directory path where the raster file will be saved.

    project : str
        Name of the raster file (without extension) to be created.

    Returns:
    --------
    None
        Writes the raster to disk and prints a confirmation message.
    """
    grid_param = griddata(
        points=(swot_data["X"], swot_data["Y"]),
        values=swot_data[param],
        xi=(grid_x, grid_y),
        method='nearest'  
    )
    swot_grid[param] = grid_param.flatten()
    return swot_grid


def mask_water(data_swot, water_tre):
    """
    Masks grid points classified as water based on the prior water probability.

    Parameters:
    -----------
    data_swot : pandas.DataFrame
        SWOT pixel data containing 'X', 'Y', and 'prior_water_prob' columns.

    swot_grid : pandas.DataFrame
        Grid DataFrame to be updated with water masking.

    x_grid : numpy.ndarray
        2D array of grid x-coordinates.

    y_grid : numpy.ndarray
        2D array of grid y-coordinates.

    water_tre : float
        Threshold below which points are considered water.

    Returns:
    --------
    pandas.DataFrame
        Updated grid DataFrame where 'Intertidal Height' is set to NaN over water points.
    """
    data_swot['prior_water_prob'] = np.where(data_swot['prior_water_prob'] < water_tre, data_swot['prior_water_prob'], np.nan)
    data_swot['height_mask'] = data_swot['prior_water_prob'].isna()
    return data_swot


def export_raster(grid_swot, x_grid, bbox, h, w, path_raster, project, method, output_epsg, reso, sd, ed):
    """
    Exports the 'Intertidal Height' grid data as a GeoTIFF raster file.

    Parameters:
    -----------
    grid_swot : pandas.DataFrame
        DataFrame containing the 'Intertidal Height' column.

    x_grid : numpy.ndarray
        2D array of grid x-coordinates, used to determine grid shape.

    bbox : tuple
        Bounding box coordinates in WGS84 (minx, miny, maxx, maxy).

    h : int
        Raster height (number of rows).

    w : int
        Raster width (number of columns).

    path_raster : str
        Directory path where the raster file will be saved.

    project : str
        Filename (without extension) for the exported raster.

    Returns:
    --------
    None
        Saves a GeoTIFF file at the specified location.
    """
    grid_intertidal = grid_swot["Intertidal height"].values.reshape(x_grid.shape)
    h, w = grid_intertidal.shape

    x_origin, y_origin = grid_swot.iloc[:, 0].min(), grid_swot.iloc[:, 1].max()
    transform = from_origin(x_origin, y_origin, reso, reso)
    with rasterio.open(
        path_raster+method+project+sd+"_"+ed+'.tif',
        'w',
        driver='GTiff',
        height=h,
        width=w,
        count=1,
        dtype='float32', 
        crs=f'EPSG:{output_epsg}',  
        transform=transform
    ) as dst:
        dst.write(np.flipud(grid_intertidal), 1) 
    print("Export completed : "+path_raster+method+project+'.tif')