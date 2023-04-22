from fastapi.responses import RedirectResponse, FileResponse
from fastapi import Request, Query, APIRouter
from worker import create_location
from models.grassmodels import (Location,
                                Mapset,
                                Gisdb,
                                GeorefFile,
                                Location_georef,
                                Location_epsg,
                                RunGeomorphon,
                                RunParamScale,
                                RegionRaster,
                                RegionBounds,
                                GrassQuery,
                                Choice,
                                lonlat_to_proj,
                                RunGrmLsi,
                                GrassLayer)

#
from scripts.grm_lsi import sw, swc, sw_side, sw_metrics, clean
from fastapi import FastAPI, File, UploadFile, Form, Depends
import pathlib
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse
from osgeo import gdal, osr

from grass_session import Session
from grass.script import core as gcore
import uuid
# Import GRASS Python bindings
import grass.script as g
import grass.script.setup as gsetup
from grass.exceptions import CalledModuleError

import shutil
import pathlib
import os
import subprocess
import tempfile


router = APIRouter()


@router.post("/api/gdalinfo")
async def gdal_info(form_data: GeorefFile = Depends()):
    print(form_data.f)
    print('\n')
    # print(dir(form_data.f))
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
    proj = osr.SpatialReference(wkt=gdalinfo_dict['projection'])
    proj.AutoIdentifyEPSG()
    gdalinfo_dict['EPSG'] = proj.GetAttrValue('AUTHORITY', 1)

    print('\n')
    print(rds.GetProjection())
    print('\n')
    print(rds.GetDescription())
    print('\n')
    print(rds.GetGeoTransform())
    print('\n')
    print(rds.GetMetadata_Dict())
    print('\n')
    # print(dir(rds.GetSpatialRef()))
    # print(type(rds.GetSpatialRef()))
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
            grass_env = g.parse_command(
                "g.gisenv", flags="s", parse=(gcore.parse_key_val, {'sep': '=', 'vsep': ';'}))
            grass_env = {key.replace("'", ""): val.replace("'", "") for key,
                         val in grass_env.items()}
            grass_region = g.parse_command(
                "g.region", flags="acpm", parse=(gcore.parse_key_val, {'sep': ':'}))
            print(grass_env)
            print(grass_region)
            gisenv_dict = {}
            gisenv_dict['status'] = 'SUCCESS'
            gisenv_dict['data'] = {'gisenv': grass_env, 'region': grass_region}
            json_compatible_item_data = jsonable_encoder(gisenv_dict)
            return JSONResponse(content=json_compatible_item_data)
    except RuntimeError as error:
        print('location or mapset doesn not exist')
        return {
            "status": "FAILED",
            "data": error
        }
    except CalledModuleError as error:
        print('missing or invalid location or mapset parameter')
        return {
            "status": "FAILED",
            "data": error
        }


@router.get("/api/create_location_epsg")
def create_location_epsg(form_data: Location_epsg = Depends()):
    location_path = pathlib.Path.joinpath(pathlib.Path(
        form_data.gisdb), pathlib.Path(form_data.location_name))
    mapset_path = pathlib.Path.joinpath(
        location_path, pathlib.Path(form_data.mapset_name))
    if form_data.overwrite_mapset:
        try:
            shutil.rmtree(mapset_path)
        except FileNotFoundError:
            print(f'no such file or directory: {mapset_path}')
    if form_data.overwrite_location:
        try:
            shutil.rmtree(location_path)
        except FileNotFoundError:
            print(f'no such file or directory: {location_path}')
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name,
                     create_opts=f"EPSG:{form_data.epsg_code}"):
            grass_env = g.parse_command(
                "g.gisenv", flags="s", parse=(gcore.parse_key_val, {'sep': '=', 'vsep': ';'}))
            grass_env = {key.replace("'", ""): val.replace("'", "") for key,
                         val in grass_env.items()}
            return {
                "status": "SUCCESS",
                "data": grass_env
            }
    except RuntimeError as error:
        # print(dir(error))
        # print("column: {}".format(ex.col))
        print(error)
        # print('error str')
        # print(str(error))
        # print(str(error).split('\n')[4].replace('\\n', '').split(':')[-1])
        for i, v in enumerate(str(error).split('\n')):
            print(v)
            if 'ERROR' in v:
                print(v)
        print('can not create location')
        return {
            "status": "FAILED",
            "data": error
        }


@router.post("/api/create_location_file")
async def create_location_file(form_data: Location_georef = Depends()):
    contents = await form_data.georef.read()
    location_path = pathlib.Path.joinpath(pathlib.Path(
        form_data.gisdb), pathlib.Path(form_data.location_name))
    mapset_path = pathlib.Path.joinpath(
        location_path, pathlib.Path(form_data.mapset_name))
    if form_data.overwrite_mapset:
        print('################################################################')
        print('########         ATTEMPT to remove MAPSET      #################')
        try:
            shutil.rmtree(mapset_path)
        except FileNotFoundError:
            print(f'no such file or directory: {mapset_path}')
    if form_data.overwrite_location:
        print('################################################################')
        print('########         ATTEMPT to remove LOCATION    #################')
        try:
            shutil.rmtree(location_path)
        except FileNotFoundError:
            print(f'no such file or directory: {location_path}')

    with open(f'/tmp/{form_data.georef.filename}', 'wb') as f:
        f.write(contents)
        f.flush()
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name,
                     create_opts=f'/tmp/{form_data.georef.filename}'):
            print(gcore.parse_command("g.gisenv", flags="s"))
    except RuntimeError as error:
        print('====== ERR 1 ==========')
        print(error)
        # print(str(error).split('\n'))
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
            # print(str(error).split('\n'))
            print('=======================')
            return {
                "status": "FAILED",
                "data": error
            }
        except ValueError as error:
            print('invalid location, can not create a mapset without permanent')
            print('====== ERR 3 ==========')
            print(error)
            # print(str(error).split('\n'))
            print('=======================')
            return {
                "status": "FAILED",
                "data": error
            }
    except ValueError as error:
        print('invalid location, can not create a mapset without permanent')
        print('====== ERR 4 ==========')
        print(error)
        # print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": error
        }
    except CalledModuleError as error:
        print('===== ERR 5 ===========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": error
        }
    try:
        session = gsetup.init(
            form_data.gisdb, form_data.location_name, form_data.mapset_name)
        # show current GRASS GIS settings
        print(g.read_command("g.gisenv"))
    except ValueError as error:
        print('invalid location, can not create a mapset without permanent')
        print('====== ERR 6 ==========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        shutil.rmtree(location_path)
        return {
            "status": "FAILED",
            "data": error
        }
    try:
        if form_data.output_raster_layer:
            g.run_command('r.in.gdal',
                          input=f'/tmp/{form_data.georef.filename}',
                          output=form_data.output_raster_layer,
                          flags="oe")
    except CalledModuleError as error:
        print('===== ERR 4 ===========')
        print(error)
        print(str(error).split('\n'))
        print('=======================')
        return {
            "status": "FAILED",
            "data": error
        }
    print('arrived here')
    grass_region = g.parse_command('g.region', raster=form_data.output_raster_layer,
                                   flags='acpm', parse=(gcore.parse_key_val, {'sep': ':'}))
    return {
        "status": "SUCCESS",
        "data": {'location': form_data.location_name,
                 'mapset': form_data.mapset_name,
                 'gisdb': form_data.gisdb,
                 'rlayer': form_data.output_raster_layer,
                 'region': grass_region}
    }


@router.get("/api/create_mapset")
def create_location_epsg(form_data: Mapset = Depends()):
    location_path = pathlib.Path.joinpath(pathlib.Path(
        form_data.gisdb), pathlib.Path(form_data.location_name))
    mapset_path = pathlib.Path.joinpath(
        location_path, pathlib.Path(form_data.mapset_name))
    if form_data.overwrite_mapset:
        try:
            shutil.rmtree(mapset_path)
        except FileNotFoundError:
            print(f'no such file or directory: {mapset_path}')
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name,
                     create_opts=""):
            grass_env = g.parse_command(
                "g.gisenv", flags="s", parse=(gcore.parse_key_val, {'sep': '=', 'vsep': ';'}))
            grass_env = {key.replace("'", ""): val.replace("'", "") for key,
                         val in grass_env.items()}
            return {
                "status": "SUCCESS",
                "data": grass_env
            }
    except RuntimeError as error:
        # print(dir(error))
        # print("column: {}".format(ex.col))
        print(error)
        # print('error str')
        # print(str(error))
        # print(str(error).split('\n')[4].replace('\\n', '').split(':')[-1])
        for i, v in enumerate(str(error).split('\n')):
            print(v)
            if 'ERROR' in v:
                print(v)
        print('can not create mapset')
        return {
            "status": "FAILED",
            "data": error
        }


@router.post("/api/set_region_bounds")
def set_grass_region_bounds(form_data: RegionBounds = Depends()):
    try:
        with Session(gisdb=form_data.location.gisdb,
                     location=form_data.location.location_name,
                     mapset=form_data.location.mapset_name):
            # print('this:', gs.read_command(
            #    "g.gisenv", flags="s"))
            grass_env = g.parse_command(
                "g.gisenv", flags="s", parse=(gcore.parse_key_val, {'sep': '=', 'vsep': ';'}))
            grass_env = {key.replace("'", ""): val.replace("'", "") for key,
                         val in grass_env.items()}
            print('grass_env:', grass_env)
            n, s, e, w = form_data.bounds.n, form_data.bounds.s, form_data.bounds.e, form_data.bounds.w
            print(n, s, e, w)
            if all(v is not None for v in [n, s, e, w]):
                if n > s or e > w:
                    grass_region = g.parse_command(
                        "g.region", n=n, s=s, e=e, w=w, flags="acpm", parse=(gcore.parse_key_val, {'sep': ':'}))
                    print(grass_env)
                    print(grass_region)
                    gisenv_dict = {}
                    gisenv_dict['status'] = 'SUCCESS'
                    gisenv_dict['data'] = {
                        'gisenv': grass_env, 'region': grass_region}
                    json_compatible_item_data = jsonable_encoder(gisenv_dict)
                    return JSONResponse(content=json_compatible_item_data)
                else:
                    return {
                        "status": "FAILED",
                        "data": f'check the values for n:{n}, s:{s}, e:{e}, w:{w}'
                    }
            else:
                return {
                    "status": "FAILED",
                    "data": f'set all the available values for n:{n}, s:{s}, e:{e}, w:{w}'
                }
    # except RuntimeError as error:
    #     print('RuntimeError')
    #     return {
    #         "status": "FAILED",
    #         "data": error
    #     }
    except CalledModuleError as error:
        print('CalledModuleError')
        print(error.output, error.stderr, error.stdout)
        return {
            "status": "FAILED",
            "data": error
        }


@router.post("/api/set_region_raster")
def set_grass_region_raster(form_data: RegionRaster = Depends()):
    try:
        with Session(gisdb=form_data.location.gisdb,
                     location=form_data.location.location_name,
                     mapset=form_data.location.mapset_name):
            grass_env = gcore.parse_command("g.gisenv", flags="s")
            raster_list_read = gcore.read_command(
                "g.list", type="raster").strip().split('\n')
            if form_data.raster_layer.layer_name is not None and form_data.raster_layer.layer_name in raster_list_read:
                grass_region = g.parse_command(
                    "g.region", raster=form_data.raster_layer.layer_name, flags="acpm", parse=(gcore.parse_key_val, {'sep': ':'}))
                if form_data.raster_layer.resolution != 0:
                    grass_region = g.parse_command(
                        "g.region", res=form_data.raster_layer.resolution, flags="acpm", parse=(gcore.parse_key_val, {'sep': ':'}))
                print(grass_env)
                print(grass_region)
                gisenv_dict = {}
                gisenv_dict['status'] = 'SUCCESS'
                gisenv_dict['data'] = {
                    'gisenv': grass_env, 'region': grass_region}
                json_compatible_item_data = jsonable_encoder(gisenv_dict)
                return JSONResponse(content=json_compatible_item_data)
            else:
                return {
                    "status": "FAILED",
                    "data": f'raster map {form_data.raster_layer.layer_name} not found - set a value for an existent raster layer:{form_data.raster_layer}'
                }
    except RuntimeError as error:
        print('location or mapset doesn not exist')
        return {
            "status": "FAILED",
            "data": error
        }


@router.get("/api/get_raster_list")
async def get_rasterlist(form_data: Location = Depends()):
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name):
            grass_env = gcore.parse_command("g.gisenv", flags="s")
            raster_list_read = gcore.read_command(
                "g.list", type="raster").strip().split('\n')
            # raster_list_parse = gcore.parse_command("g.list", type="raster")
            # raster_list_parse_colon = gcore.parse_command(
            #    "g.list", type="raster", sep=':')
            print(grass_env, raster_list_read)
            # raster_list_parse, raster_list_parse_colon)
            gisenv_dict = {}
            gisenv_dict['status'] = 'SUCCESS'
            gisenv_dict['data'] = raster_list_read
            json_compatible_item_data = jsonable_encoder(gisenv_dict)
            return JSONResponse(content=json_compatible_item_data)
    except RuntimeError as error:
        print(error)
        return {
            "status": "FAILED",
            "data": error
        }


@router.post("/api/geomorphon")
def run_geomorphon(form_data: RunGeomorphon = Depends()):
    # Start GRASS Session
    if not form_data.output_suffix:
        output_suffix = 'g'+str(uuid.uuid1()).replace('-', '')
    else:
        output_suffix = form_data.output_suffix+'_'
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
        g.read_command('g.region', n=n, s=s, e=e, w=w, flags='acpm')
    else:
        g.read_command('g.region', raster=form_data.elevation, flags='acpm')
    if form_data.predictors:
        try:
            g.run_command('r.geomorphon', elevation=form_data.elevation,
                          search=form_data.search,
                          skip=form_data.skip,
                          flat=form_data.flat,
                          dist=form_data.dist,
                          forms=output_suffix+'_forms',
                          intensity=output_suffix+'_intensity',
                          exposition=output_suffix+'_exposition',
                          range=output_suffix+'_range',
                          variance=output_suffix+'_variance',
                          elongation=output_suffix+'_elongation',
                          azimuth=output_suffix+'_azimuth',
                          extend=output_suffix+'_extend',
                          width=output_suffix+'_width',
                          overwrite=form_data.overwrite,
                          flags=fl)
            g.run_command('r.out.gdal', input=output_suffix+'_forms',
                  output='/tmp/'+str(output_suffix)+'_forms'+'.tif', type='Byte', overwrite=True)
            return FileResponse('/tmp/'+str(output_suffix)+'_forms'+'.tif', media_type='image/tiff', filename=str(output_suffix)+'_forms'+'.tif')
            # return {
            #    "status": "SUCCESS",
            #    "data": f'geomorphon completed find predictors layer with suffix {output_suffix}'
            # }
        except CalledModuleError as error:
            return {
                "status": "FAILED",
                "data": error
            }
    else:
        try:
            g.run_command('r.geomorphon', 
                        elevation=form_data.elevation,
                        forms=output_suffix+'_forms',
                        search=form_data.search,
                        skip=form_data.skip,
                        flat=form_data.flat,
                        dist=form_data.dist,
                        flags=fl,
                        overwrite=form_data.overwrite)
            g.run_command('r.out.gdal', input=output_suffix+'_forms',
                  output='/tmp/'+str(output_suffix)+'_forms'+'.tif', type='Byte', overwrite=True)
            return FileResponse('/tmp/'+str(output_suffix)+'_forms'+'.tif', media_type='image/tiff', filename=str(output_suffix)+'_forms'+'.tif')
        except CalledModuleError as error:
            return {
                "status": "FAILED",
                "data": error
            }
    


@router.post("/api/paramscale")
async def run_paramscale(form_data: RunParamScale = Depends()):
    # Start GRASS Session
    flags = []
    if form_data.c:
        flags.append('c')
    if len(flags) >= 1:
        fl = ''.join(str(i) for i in flags)
    else:
        fl = ''
    session = gsetup.init(
        form_data.gisdb, form_data.location_name, form_data.mapset_name)
    if form_data.raster_region and len(form_data.raster_region.split(',')) == 4:
        n, s, e, w = form_data.raster_region.split(',')
        g.read_command('g.region', n=n, s=s, e=e, w=w, flags='acpm')
    else:
        g.read_command('g.region', raster=form_data.input, flags='acpm')
    try:
        g.run_command('r.param.scale', input=form_data.input,
                      output=form_data.output+'_'+form_data.method,
                      slope_tolerance=form_data.slope_tolerance,
                      curvature_tolerance=form_data.curvature_tolerance,
                      size=form_data.size,
                      method=form_data.method,
                      exponent=form_data.exponent,
                      zscale=form_data.zscale,
                      overwrite=form_data.overwrite,
                      flags=fl)
    except CalledModuleError as error:
        return {
            "status": "FAILED",
            "data": error
        }

    if form_data.predictors:
        for i in ['elev', 'slope', 'aspect', 'profc', 'planc', 'longc', 'crosc', 'minic', 'maxic', 'feature']:
            try:
                g.run_command('r.param.scale', input=form_data.input,
                              output=form_data.output+'_'+i,
                              slope_tolerance=form_data.slope_tolerance,
                              curvature_tolerance=form_data.curvature_tolerance,
                              size=form_data.size,
                              method=i,
                              exponent=form_data.exponent,
                              zscale=form_data.zscale,
                              overwrite=form_data.overwrite,
                              flags=fl)
            except CalledModuleError as error:
                return {
                    "status": "FAILED",
                    "data": error
                }

    g.run_command('r.out.gdal', input=form_data.output+'_'+form_data.method,
                  output=str('/tmp/'+form_data.output+'_'+form_data.method)+'.tif', type='Byte', overwrite=True)
    # zip_file = zipfiles(
    #    '/app/grassdata/'+str(form_data.output+'_'+form_data.method)+'.tif')
    return FileResponse('/tmp/'+str(form_data.output+'_'+form_data.method)+'.tif', media_type='image/tiff', filename=str(form_data.output+'_'+form_data.method)+'.tif')
    # return FileResponse(zip_file, media_type='application/x-zip-compressed', filename=zip_file)


@router.post("/api/r_what")
async def r_what(form_data: GrassQuery = Depends()):
    try:
        with Session(gisdb=form_data.location.gisdb,
                     location=form_data.location.location_name,
                     mapset=form_data.location.mapset_name):
            n, s = form_data.coors
            if form_data.lonlat:
                n, s, z = g.read_command(
                    'm.proj', flags='i', separator=',', coordinates=(n, s)).split(',')
                print(n, s)
            raster_query_results = g.raster_what(map=form_data.grass_layers,
                                                 coord=(float(n), float(s)))
            json_compatible_item_data = jsonable_encoder(raster_query_results)
            return JSONResponse(content=json_compatible_item_data)
    except CalledModuleError as error:
        return {
            "status": "FAILED",
            "data": error
        }
# convert fearture to vector and return geojson
# opt: simplify vector feature

# r.what on a raster list
# v.what on a vector list

# r.what on a raster list but on a neighbourud of a point
# e,g,: mean/std/max/min over a mxn window (which means set a region with bounds using ncell from given point
#
# set grass region from qgis extent
#
# run grass command on selected raster (right click on raster -> list of command -> open command window)


@router.post("/api/m_proj")
async def m_proj(form_data: lonlat_to_proj = Depends()):
    data = []
    try:
        with Session(gisdb=form_data.location.gisdb,
                     location=form_data.location.location_name,
                     mapset=form_data.location.mapset_name):
            coords = form_data.coors
            for i in coords:
                print(i)
                x, y, z = g.read_command(
                    'm.proj', flags='i', separator=',', coordinates=(i[0], i[1])).split(',')
                print(x, y, z)
                data.append([x, y])
            results = {'status': 'SUCCESS', 'data': data}
            json_compatible_item_data = jsonable_encoder(results)
            return JSONResponse(content=json_compatible_item_data)
    except CalledModuleError as error:
        return {
            "status": "FAILED",
            "data": error
        }


@router.get("/api/get_current_region")
async def get_current_region(form_data: Location = Depends()):
    try:
        with Session(gisdb=form_data.gisdb,
                     location=form_data.location_name,
                     mapset=form_data.mapset_name):
            grass_env = g.parse_command(
                "g.gisenv", flags="s", parse=(gcore.parse_key_val, {'sep': '=', 'vsep': ';'}))
            grass_env = {key.replace("'", ""): val.replace("'", "") for key,
                         val in grass_env.items()}
            grass_region = g.parse_command(
                "g.region", flags="acpm", parse=(gcore.parse_key_val, {'sep': ':'}))
            print(grass_env)
            print(grass_region)
            g.run_command(
                "v.in.region", output="region_bbox", overwrite=True)
            g.run_command("v.out.ogr", input='region_bbox', type='area',
                          output='/tmp/region_bbox.GeoJSON', format='GeoJSONSeq', overwrite=True)
            # gisenv_dict = {}
            # gisenv_dict['gisenv'] = grass_env
            # gisenv_dict['region'] = grass_region
            # json_compatible_item_data = jsonable_encoder(gisenv_dict)
            return FileResponse(str('/tmp/region_bbox.GeoJSON'),  filename=str('region_bbox.GeoJSON'))
            # return JSONResponse(content=json_compatible_item_data)
    except CalledModuleError as error:
        print('location or mapset doesn not exist')
        return {
            "status": "FAILED",
            "data": error
        }


@router.post("/api/g_remove")
async def g_remove(form_data: GrassLayer = Depends()):
    try:
        with Session(gisdb=form_data.location.gisdb,
                     location=form_data.location.location_name,
                     mapset=form_data.location.mapset_name):
            if form_data.grass_layers:
                g.run_command('g.remove', 
                              type_='raster,vector', 
                              name=f"{(',').join(form_data.grass_layers)}", flags='f')
            if form_data.pattern:
                g.run_command('g.remove', 
                              type_='raster,vector', 
                              pattern=f"{form_data.pattern}", flags='f')
                
            json_compatible_item_data = jsonable_encoder({'status': 'SUCCESS'})
            return JSONResponse(content=json_compatible_item_data)
    except CalledModuleError as error:
        return {
            "status": "FAILED",
            "data": error
        }

@router.post("/api/clear_tmp")
async def clean_tmp(form_data: Choice = Depends()):
    print(os.listdir('/tmp'))
    tmp_size = get_size_format(get_directory_size('/tmp'))
    json_compatible_item_data = jsonable_encoder(tmp_size)
    return JSONResponse(content=json_compatible_item_data)


def get_directory_size(directory):
    """Returns the `directory` size in bytes."""
    total = 0
    try:
        # print("[+] Getting the size of", directory)
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                try:
                    total += get_directory_size(entry.path)
                except FileNotFoundError:
                    pass
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total


def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


@router.get("/api/get_location_list")
def get_valid_location(form_data: Gisdb = Depends()):
    checklist = ['DEFAULT_WIND', 'PROJ_UNITS',
                 'WIND', 'PROJ_INFO', 'PROJ_EPSG', 'VAR']
    valid_location = []
    if os.path.isdir(form_data.gisdb):
        for location in os.scandir(form_data.gisdb):
            if location.is_dir():
                for mapset in os.scandir(location):
                    if mapset.is_dir() and mapset.name == 'PERMANENT':
                        tocheck = []
                        print("LOCATION:", location.name,
                              "MAPSET:", mapset.name)
                        for content in os.scandir(mapset):
                            if content.is_file():
                                print(content)
                                tocheck.append(content.name)
                        if any(item in tocheck for item in checklist):
                            valid_location.append(location.name)
    if len(valid_location) >= 1:
        location = {}
        for i in valid_location:
            location[i] = os.listdir(os.path.join(form_data.gisdb, i))
        return {
            "status": "SUCCESS",
            "data": location
        }
    else:
        return {
            "status": "FAILED",
            "data": f"{form_data.gisdb} do not contain a valid GRASS GIS location"
        }


checklist = ['DEFAULT_WIND', 'PROJ_UNITS',
             'WIND', 'PROJ_INFO', 'PROJ_EPSG', 'VAR']


@router.post("/api/GRM")
def run_grm(form_data: RunGrmLsi = Depends()):
    # Start GRASS Session
    print('do nothing')
    with Session(gisdb=form_data.gisdb,
                 location=form_data.location_name,
                 mapset=form_data.mapset_name):
        # g.run_command('g.region', raster=form_data.elevation, flags='ap')
        # g.run_command('r.colors', color='haxby', map=form_data.elevation, flags='e')

        # common parameters
        n, s, w, e = form_data.region
        elevation = form_data.elevation
        # SWC_parameters
        swc_suffix = 'g'+str(uuid.uuid1()).replace('-', '')
        swc_search = form_data.swc_search
        swc_skip = form_data.swc_skip
        swc_flat = form_data.swc_flat
        swc_dist = form_data.swc_dist
        iter_thin = form_data.iter_thin
        swc_area_lesser = form_data.swc_area_lesser
        generalize_method = form_data.generalize_method
        generalize_threshold = form_data.generalize_threshold
        vclean_rmdangle_threshold = form_data.vclean_rmdangle_threshold
        # SWC_parameters
        sw_suffix = 'g'+str(uuid.uuid1()).replace('-', '')
        sw_search = form_data.sw_search
        sw_skip = form_data.sw_skip
        sw_flat = form_data.sw_flat
        sw_dist = form_data.sw_dist
        sw_area_lesser = form_data.sw_area_lesser
        vclean_rmarea_threshold = form_data.vclean_rmarea_threshold
        # sw_side
        buffer_distance = form_data.buffer_distance
        # sw_metrics
        transect_split_length = form_data.transect_split_length
        point_dmax = form_data.point_dmax
        transect_side_distances = form_data.transect_side_distances

        swc(suffix=swc_suffix,
            n=n,
            s=s,
            w=w,
            e=e,
            search=swc_search,
            skip=swc_skip,
            flat=swc_flat,
            dist=swc_dist,
            iter_thin=iter_thin,
            area_lesser=swc_area_lesser,
            generalize_method=generalize_method,
            generalize_threshold=generalize_threshold,
            vclean_rmdangle_threshold=vclean_rmdangle_threshold)

        sw(suffix=sw_suffix,
           n=n,
           s=s,
           w=w,
           e=e,
           elevation=elevation,
           search=sw_search,
           skip=sw_skip,
           flat=sw_flat,
           dist=sw_dist,
           area_lesser=sw_area_lesser,
           vclean_rmarea_threshold=vclean_rmarea_threshold)

        side_stats = sw_side(swc_suffix=swc_suffix,
                             sw_suffix=sw_suffix,
                             buffer_distance=buffer_distance,
                             elevation=elevation)

        results = sw_metrics(swc_suffix=swc_suffix,
                             sw_suffix=sw_suffix,
                             side_stats=side_stats,
                             transect_split_length=transect_split_length,
                             point_dmax=point_dmax,
                             elevation=elevation,
                             transect_side_distances=transect_side_distances)

        print(results)
        if form_data.clean:
            clean(swc_suffix)
            clean(sw_suffix)
        json_compatible_item_data = jsonable_encoder(results)
        return JSONResponse(content=json_compatible_item_data)
