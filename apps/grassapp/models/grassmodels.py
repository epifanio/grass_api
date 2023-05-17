from pydantic import BaseModel, Field
from typing import Optional, List, Union
import pydantic
import pydantic_numpy.dtype as pnd
from pydantic_numpy import NDArray, NDArrayFp32
from fastapi import UploadFile, Form


class GeorefFile(BaseModel):
    f: UploadFile = Form(...)


class Gisdb(BaseModel):
    gisdb: Optional[str] = Field(title="GRASS GIS DATABASE")


class Location(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")


class Mapset(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    overwrite_mapset: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS MAPSET")


class Location_georef(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    georef: UploadFile = Form(...)
    overwrite_location: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS LOCATION")
    overwrite_mapset: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS MAPSET")
    output_raster_layer: Optional[str] = Field(
        title="Name of the imported raster layer")


class Location_epsg(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    epsg_code: Optional[int] = Field(default='',
                                     title="EPSG Code to create the GRASS GIS Location")
    overwrite_location: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS LOCATION")
    overwrite_mapset: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS MAPSET")


class Location(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")


# class Geomorphon(BaseModel):
#     rlayer: str = Field(default='bathy')
#     param1: float = Field(default=1.0)


class RunGeomorphon(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    region: Optional[str] = Field(default='',
                                  title="GRASS Region in the form of a comma separated string values: n,s,w,e")
    elevation: str = Field(default='bathy')
    # forms: str = Field(default='bathy_geomorphon')
    search: int = Field(default=3, title='search',
                        description='Outer search radius')
    skip: int = Field(default=0, title='skip',
                      description='Inner search radius')
    flat: float = Field(default=1, title='flat',
                        description='Flatness threshold (degrees)')
    dist: float = Field(default=0, title='flat',
                        description='Flatness distance, zero for none')
    m: Optional[bool] = Field(default=False,
                              description='Use meters to define search units (default is cells)')
    e: Optional[bool] = Field(
        default=False, description='Use extended form correction')
    overwrite: bool = Field(
        default=False, description='Allow output files to overwrite existing files')
    predictors: Optional[bool] = Field(
        default=False, description='generate extra layer form generic geomorphometry')
    output_suffix: Optional[str] = Field(
        default=None, title="suffix used for output, if None a uuid will be generated")


class RunParamScale(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    region: Optional[str] = Field(default='',
                                  title="GRASS Region in the form of a comma separated string values: n,s,w,e")
    input: str = Field(default='bathy', description='Name of input raster map')

    output: str = Field(default='bathy_morphometric',
                        description='Name for output raster map containing morphometric parameter')

    slope_tolerance: float = Field(
        default=1.0, description="Slope tolerance that defines a 'flat' surface (degrees)")
    curvature_tolerance: float = Field(
        default=0.0001, description="Curvature tolerance that defines 'planar' surface")
    exponent: float = Field(
        default=0.0, description='Exponent for distance weighting (0.0-4.0)')
    size: int = Field(
        default=3, description='Size of processing window (odd number only)')
    zscale: float = Field(default=1.0, description='Vertical scaling factor')

    method: str = Field(
        default='feature', description="Morphometric parameter in 'size' window to calculate")
    # elev, slope, aspect, profc, planc, longc, crosc, minic, maxic, feature
    c: Optional[bool] = Field(default=False,
                              description='Constrain model through central window cell ')

    overwrite: bool = Field(
        default=False, description='Allow output files to overwrite existing files')
    predictors: Optional[bool] = Field(
        default=False, description='generate all the available methods: elev, slope, aspect, profc, planc, longc, crosc, minic, maxic, feature')


class Bounds(BaseModel):
    n: Optional[float] = Field(description='Value for the northern edge')
    s: Optional[float] = Field(description='Value for the southern edge')
    e: Optional[float] = Field(description='Value for the eastern edge')
    w: Optional[float] = Field(description='Value for the western edge')


class Resolution(BaseModel):
    resolution: Optional[int] = Field(
        description='2D grid resolution (north-south and east-west)')


class RasterLayer(BaseModel):
    layer_name: str = Field(
        default='', description='Set region to match raster map(s)')
    resolution: Optional[int] = Field(default=0,
                                      description='2D grid resolution (north-south and east-west)')


class RegionRaster(BaseModel):
    location: Location | None = None
    raster_layer: RasterLayer | None = None


class RegionBounds(BaseModel):
    location: Location | None = None
    bounds: Bounds | None = None
    resolution: Resolution | None = None


class lonlat_to_proj(BaseModel):
    location: Location | None = None
    coors: NDArray[pnd.float32] = Field(default=[0.0, 0.0], description='')


class GrassQuery(BaseModel):
    location: Location | None = None
    grass_layers: List[str] = Field(default=[''], description='')
    coors: List[float] = Field(default=[0.0, 0.0], description='')
    lonlat: Optional[bool] = Field(
        default=False, description='input values are in lon lat format (decimal degre) - default False auumes coordinates matches the Location projection')


class GrassLayer(BaseModel):
    location: Location | None = None
    grass_layers: Optional[List[str]] = None
    layer_type: Optional[List[str]] = Field(default=['raster', 'vector'], description='')
    pattern: Optional[str] = Field(default="", example="g*")
    
class Datasource(BaseModel):
    data: dict = Field(
        default={"": ""},
        example={
            "123e4567-e89b-12d3-a456-426655440000": {
                "title": "osisaf sh icearea seasonal",
                "feature_type": "timeSeries",
                "resources": {
                    "opendap": [
                        "https://hyrax.epinux.com/opendap/osisaf_sh_icearea_seasonal.nc"
                    ]
                },
            },
        },
    )
    email: str = Field(default="me@you.web", example="epiesasha@me.com")
    project: Optional[str] = Field(default="METSIS", example="METSIS")
    notebook: Optional[bool] = Field(default=False, example=True)


class Choice(BaseModel):
    clean: Optional[bool] = Field(
        default=False, description='it is your choice')



class RunGrm(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")

    region: Optional[str] = Field(default='',
                                  title="GRASS Region in the form of a comma separated string values: n,s,w,e")

    elevation: str = Field(default='bathy')
    # forms: str = Field(default='bathy_geomorphon')
    swc_search: int = Field(default=9, title='search',
                            description='Outer search radius')
    swc_skip: int = Field(default=3, title='skip',
                          description='Inner search radius')
    swc_flat: float = Field(default=2, title='flat',
                            description='Flatness threshold (degrees)')
    swc_dist: float = Field(default=0, title='flat',
                            description='Flatness distance, zero for none')
    iter_thin: int = Field(default=400, title='iter_thin',
                           description='iter_thin')
    swc_area_lesser: int = Field(default=70, title='swc_area_lesser',
                                 description='swc_area_lesser')
    generalize_method: str = Field(default='douglas')
    generalize_threshold: int = Field(default=2, title='generalize_threshold',
                                      description='generalize_threshold')

    vclean_rmdangle_threshold: Optional[str] = Field(default='5,10,20,30',
                                    title="vclean_rmdangle_threshold")

    sw_search: int = Field(default=30, title='search',
                           description='Outer search radius')
    sw_skip: int = Field(default=7, title='skip',
                         description='Inner search radius')
    sw_flat: float = Field(default=3.8, title='flat',
                           description='Flatness threshold (degrees)')
    sw_dist: float = Field(default=15, title='flat',
                           description='Flatness distance, zero for none')
    sw_area_lesser: int = Field(default=1000, title='sw_area_lesser',
                                description='sw_area_lesser')
    
    
    vclean_rmarea_threshold: Optional[str] = Field(default='10',
                                    title="vclean_rmarea_threshold")

    buffer_distance: int = Field(default=1, title='buffer_distance',
                                 description='buffer_distance')
    transect_split_length: int = Field(default=1, title='transect_split_length',
                                       description='transect_split_length')
    point_dmax: int = Field(default=1, title='point_dmax',
                            description='point_dmax')
    
    transect_side_distances: Optional[str] = Field(default='70,70',
                                    title="transect_side_distances")
    clean: Optional[bool] = Field(
        default=False, description='clean output')

class RunGrmLsi(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")

    region: NDArray[pnd.float32] = Field(
        default=[4546380, 4546202, 506185, 506571], description='region: [n,s,w,e]')

    elevation: str = Field(default='bathy')
    # forms: str = Field(default='bathy_geomorphon')
    swc_search: int = Field(default=9, title='search',
                            description='Outer search radius')
    swc_skip: int = Field(default=3, title='skip',
                          description='Inner search radius')
    swc_flat: float = Field(default=2, title='flat',
                            description='Flatness threshold (degrees)')
    swc_dist: float = Field(default=0, title='flat',
                            description='Flatness distance, zero for none')
    iter_thin: int = Field(default=400, title='iter_thin',
                           description='iter_thin')
    swc_area_lesser: int = Field(default=70, title='swc_area_lesser',
                                 description='swc_area_lesser')
    generalize_method: str = Field(default='douglas')
    generalize_threshold: int = Field(default=2, title='generalize_threshold',
                                      description='generalize_threshold')

    vclean_rmdangle_threshold: List[int] = Field(
        default=[5, 10, 20, 30], description='vclean_rmdangle_threshold')

    sw_search: int = Field(default=30, title='search',
                           description='Outer search radius')
    sw_skip: int = Field(default=7, title='skip',
                         description='Inner search radius')
    sw_flat: float = Field(default=3.8, title='flat',
                           description='Flatness threshold (degrees)')
    sw_dist: float = Field(default=15, title='flat',
                           description='Flatness distance, zero for none')
    sw_area_lesser: int = Field(default=1000, title='sw_area_lesser',
                                description='sw_area_lesser')
    vclean_rmarea_threshold: List[int] = Field(default=[10], title='vclean_rmarea_threshold',
                                               description='vclean_rmarea_threshold')
    buffer_distance: int = Field(default=1, title='buffer_distance',
                                 description='buffer_distance')
    transect_split_length: int = Field(default=1, title='transect_split_length',
                                       description='transect_split_length')
    point_dmax: int = Field(default=1, title='point_dmax',
                            description='point_dmax')
    transect_side_distances: List[int] = Field(
        default=[70, 70], description='transect_side_distances')
    clean: Optional[bool] = Field(
        default=False, description='clean output')
    # m: Optional[bool] = Field(default=False,
    #                           description='Use meters to define search units (default is cells)')
    # e: Optional[bool] = Field(
    #     default=False, description='Use extended form correction')
    # overwrite: bool = Field(
    #     default=False, description='Allow output files to overwrite existing files')
    # predictors: Optional[bool] = Field(
    #     default=False, description='generate extra layer form generic geomorphometry')
    # output_suffix: Optional[str] = Field(
    #     default=None, title="suffix used for output, if None a uuid will be generated")
