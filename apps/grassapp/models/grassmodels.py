from pydantic import BaseModel, Field
from typing import Optional, List
import pydantic

from fastapi import UploadFile, Form


class GeorefFile(BaseModel):
    f: UploadFile = Form(...)


class Location(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")


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
    epsg_code: Optional[int] = Field(default='',
                                     title="EPSG Code to create the GRASS GIS Location")
    overwrite_location: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS LOCATION")
    overwrite_mapset: Optional[bool] = Field(
        default=False, title="Overwrite existent GRASS GIS MAPSET")


class Geomorphon(BaseModel):
    rlayer: str = Field(default='bathy')
    param1: float = Field(default=1.0)


class runGeomorphon(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    raster_region: Optional[str] = Field(
        title="GRASS Region in the form of a comma separated string values: n,s,w,e")
    elevation: str = Field(default='bathy')
    forms: str = Field(default='bathy_geomorphon')
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


class runParamScale(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    raster_region: Optional[str] = Field(
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
        default='elev', description="Morphometric parameter in 'size' window to calculate")
    # elev, slope, aspect, profc, planc, longc, crosc, minic, maxic, feature
    c: Optional[bool] = Field(default=False,
                              description='Constrain model through central window cell ')

    overwrite: bool = Field(
        default=False, description='Allow output files to overwrite existing files')
    predictors: Optional[bool] = Field(
        default=False, description='generate all the available methods: elev, slope, aspect, profc, planc, longc, crosc, minic, maxic, feature')


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
