from fastapi.responses import RedirectResponse, FileResponse
from fastapi import Request, Query, APIRouter
from worker import create_location
from models.grassmodels import Location, GeorefFile, NewLocation, runGeomorphon
from fastapi import FastAPI, File, UploadFile, Form, Depends
import pathlib
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse
from osgeo import gdal

from grass_session import Session
from grass.script import core as gcore
# Import GRASS Python bindings
import grass.script as gs
import grass.script.setup as gsetup
from grass.exceptions import CalledModuleError

import shutil
import pathlib
import os

router = APIRouter()


@router.post("/api/gdalinfo")
async def form_post(form_data: GeorefFile = Depends()):
    print(form_data.f)
    print('\n')
    print(dir(form_data.f))
    print('\n')
    print(form_data.f.filename)
    print('\n')
    print(float(form_data.f.size) * 10E-06)
    # pathlib.Path('form_data.f.filename')
    print('\n')
    contents = await form_data.f.read()
    with open(f'/app/grassdata/{form_data.f.filename}', 'wb') as f:
        f.write(contents)
        f.flush()
    # rds = gdal.Open(form_data.f.filename)
    rds = gdal.Open(f'/app/grassdata/{form_data.f.filename}')
    metadata = rds.GetMetadata_Dict()
    metadata['size'] = float(form_data.f.size) * 10E-05
    gdalinfo_dict = {}
    gdalinfo_dict['filename'] = rds.GetDescription()
    gdalinfo_dict['projection'] = rds.GetProjection()
    gdalinfo_dict['geotransform'] = rds.GetGeoTransform()

    print('\n')
    print(rds.GetProjection())
    print('\n')
    print(rds.GetDescription())
    print('\n')
    print(rds.GetGeoTransform())
    print('\n')
    print(rds.GetMetadata_Dict())
    print('\n')
    print(dir(rds.GetSpatialRef()))
    print(type(rds.GetSpatialRef()))
    try:
        gdalinfo_dict['proj4'] = rds.GetSpatialRef().ExportToProj4()
        print(rds.GetSpatialRef().ExportToProj4())
    except AttributeError:
        print('No projection info found')
        print("NoneType' object has no attribute 'ExportToProj4")
        gdalinfo_dict['proj4'] = None
    gdalinfo_dict['metadata'] = metadata
    json_compatible_item_data = jsonable_encoder(gdalinfo_dict)
    return JSONResponse(content=json_compatible_item_data)


@router.get("/api/gisenv")
def get_grass_gisenv(form_data: Location = Depends()):
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name):
            grass_env = gcore.parse_command("g.gisenv", flags="s")
            grass_region = gcore.parse_command("g.region", flags="p")
            print(grass_env)
            print(grass_region)
            gisenv_dict = {}
            gisenv_dict['gisenv'] = grass_env
            gisenv_dict['region'] = grass_region
            json_compatible_item_data = jsonable_encoder(gisenv_dict)
            return JSONResponse(content=json_compatible_item_data)
    except:
        print('location or mapset doesn not exist')


@router.get("/api/create_location")
def get_grass_gisenv(form_data: Location = Depends()):
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name,
                     create_opts=form_data.create_opts):
            grass_env = gcore.parse_command("g.gisenv", flags="s")
            print(grass_env)
    except RuntimeError as ex:
        print(dir(ex))
        #print("column: {}".format(ex.col))
        print(ex)
        print('ex str')
        print(str(ex))
        print(str(ex).split('\n')[4].replace('\\n', '').split(':')[-1])
        for i, v in enumerate(str(ex).split('\n')):
            print(v)
            if 'ERROR' in v:
                print(v)
        print('can not create location')


@router.post("/api/create_location_from_file")
async def get_grass_gisenv(form_data: NewLocation = Depends()):
    contents = await form_data.georef.read()
    location_path = pathlib.Path.joinpath(pathlib.Path(
        form_data.gisdb), pathlib.Path(form_data.location_name))
    mapset_path = pathlib.Path.joinpath(
        location_path, pathlib.Path(form_data.mapset_name))
    if form_data.overwrite_location:
        shutil.rmtree(location_path)
    if form_data.overwrite_mapset:
        shutil.rmtree(mapset_path)
    with open(f'/app/grassdata/{form_data.georef.filename}', 'wb') as f:
        f.write(contents)
        f.flush()
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name,
                     create_opts=f'/app/grassdata/{form_data.georef.filename}'):
            print(gcore.parse_command("g.gisenv", flags="s"))
    except RuntimeError as error:
        print('====== ERR 1 ==========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        try:
            with Session(gisdb=form_data.gisdb,
                         location=form_data.location_name,
                         mapset=form_data.mapset_name,
                         create_opts=""):
                print(gcore.parse_command("g.gisenv", flags="s"))
        except RuntimeError as error:
            print('====== ERR 2 ==========')
            print(error)
            print(str(error).split('\n'))
            print('=======================')
            return {
                "status": "FAILED",
                "data": ''
            }
        except ValueError as error:
            print('invalid location, can not create a mapset without permanent')
            print('====== ERR 3 ==========')
            print(error)
            print(str(error).split('\n'))
            print('=======================')
            return {
                "status": "FAILED",
                "data": ''
            }
    except ValueError as error:
        print('invalid location, can not create a mapset without permanent')
        print('====== ERR 4 ==========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": ''
        }
    except CalledModuleError as error:
        print('===== ERR 5 ===========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": ''
        }
    try:
        session = gsetup.init(
            form_data.gisdb, form_data.location_name, form_data.mapset_name)
        # show current GRASS GIS settings
        print(gs.read_command("g.gisenv"))
    except ValueError as error:
        print('invalid location, can not create a mapset without permanent')
        print('====== ERR 6 ==========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        shutil.rmtree(location_path)
        return {
            "status": "FAILED",
            "data": ''
        }
    try:
        gs.run_command('r.in.gdal',
                       input=f'/app/grassdata/{form_data.georef.filename}',
                       output=form_data.output_raster_layer,
                       flags="oe")
    except CalledModuleError as error:
        print('===== ERR 4 ===========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": ''
        }
    print('arrived here')
    print(gs.read_command('g.region', raster=form_data.output_raster_layer, flags='ap'))
    return {
        "status": "SUCCESS",
        "data": {'location': form_data.location_name,
                 'mapset': form_data.mapset_name,
                 'gisdb': form_data.gisdb,
                 'rlayer': form_data.output_raster_layer}
    }


@router.post("/api/geomorphon")
def run_grass_command(form_data: runGeomorphon = Depends()):
    # Start GRASS Session
    flags = []
    if form_data.m:
        flags.append('m')
    if form_data.e:
        flags.append('e')
    if len(flags) >= 1:
        fl = ''.join(str(i) for i in flags)
    else:
        fl = ''
    session = gsetup.init(
        form_data.gisdb, form_data.location_name, form_data.mapset_name)
    if len(form_data.region) == 4:
        n, s, e, w = form_data.region
        gs.read_command('g.region', n=n, s=s, e=e, w=w, flags='ap')
    else:
        gs.read_command('g.region', raster=form_data.elevation, flags='ap')
    gs.run_command('r.geomorphon', elevation=form_data.elevation,
                   forms=form_data.forms, flags=fl)
    gs.run_command('r.out.gdal', input=form_data.forms,
                   output=str(form_data.forms)+'.tif', type='Byte', overwrite=True)
    return FileResponse(str(form_data.forms)+'.tif', media_type='image/tiff', filename=str(form_data.forms)+'.tif')
