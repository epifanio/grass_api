from pydantic import BaseModel, Field
from typing import Optional

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


class Geomorphon(BaseModel):
    rlayer: str = Field(default='bathy')
    param1: float = Field(default=1.0)


class runGeomorphon(BaseModel):
    location_name: Optional[str] = Field(title="GRASS GIS LOCATION name")
    mapset_name: Optional[str] = Field(
        default='PERMANENT', title="GRASS GIS MAPSET name")
    gisdb: Optional[str] = Field(
        default='/tmp', title="PATH to the GRASSDATA directory")
    region: Optional[list] = Field(default=[],
                                   title="GRASS Region in the form of a list [n, s, w, e]")
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
