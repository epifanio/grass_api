
import os

os.environ['LD_LIBRARY_PATH'] = '/usr/lib/grass83/lib/'

import matplotlib.pyplot as plt
import scipy.spatial
import numpy as np
from itertools import zip_longest
from matplotlib import pyplot as plt
from grass_session import Session
import grass.script as g
import grass.script.setup as gsetup
import sys
import matplotlib
from multiprocessing import Pool
import uuid
import base64
import io
import collections


from grass.pygrass.vector.geometry import Point, Line
from grass.pygrass.vector import VectorTopo

class DictTable(dict):
    # Overridden dict class which takes a dict in the form {'a': 2, 'b': 3},
    # and renders an HTML Table in IPython Notebook.
    def _repr_html_(self):
        html = ["<table width=100%>"]
        for key, value in self.items():
            html.append("<tr>")
            html.append("<td>{0}</td>".format(key))
            html.append("<td>{0}</td>".format(value))
            html.append("</tr>")
        html.append("</table>")
        return ''.join(html)
# matplotlib.use('TkAgg', force=True)


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def getcoords(lines):
    if type(lines[0]) == tuple:
        lines = [i[0] for i in lines]
    coords = {}
    count = 0
    for group in grouper(lines[10:], 4, fillvalue=None):
        count += 1
        coords[count] = ','.join(
            [','.join(i.strip().split(" ")).strip() for i in group[1:-1]])
    return coords


def makeprofiles(coords):
    layer = coords['layer']
    resolution = coords['resolution']
    coordinates = coords['coordinates']
    p = g.read_command('r.profile', input=layer, coordinates=coordinates,
                       resolution=resolution, flags='g').strip().split('\n')
    return p


def getprofile(p):
    profile = np.asarray([[float(j) for j in x.split()]
                         for x in p if '*' not in x])
    return profile


def makestaticmap(suffix=None,
                  raster=None,
                  vector=None,
                  line_width=[3],
                  line_color=['255:0:0'],
                  output='',
                  width=400,
                  height=100,
                  at=(40, 50, 10, 90),
                  units='',
                  digits=0,
                  label=False,
                  fontsize=12,
                  labelnum=5,
                  flags='v',
                  clean=True,
                  embed=True,
                  render=True,
                  north_arrow=False,
                  north_arrow_opts={'style': '1b',
                                    'rotation': 0,
                                    'label': 'N',
                                    'fontsize': 12,
                                    'color': 'black',
                                    'fill_color': 'gray',
                                    'at': (90, 20)}):
    if len(line_width) != len(vector):
        line_width = [line_width for i in vector]
    if len(line_color) != len(vector):
        line_color = [line_color for i in vector]
    if not suffix:
        suffix = 'g'+str(uuid.uuid1()).replace('-', '')
        print('I am using  this:', suffix)
    try:
        g.run_command('d.mon', stop='cairo')
    except:
        pass
    if not output:
        if raster:
            output = suffix+'_'+raster[0]+'.png'
        else:
            output = suffix+'_'+vector[0]+'.png'
    os.environ['GRASS_GNUPLOT'] = 'gnuplot -persist'
    os.environ['GRASS_PROJSHARE'] = '/usr/share/proj'
    os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
    os.environ['GRASS_RENDER_TRUECOLOR'] = 'TRUE'
    os.environ['GRASS_RENDER_TRANSPARENT'] = 'TRUE'
    os.environ['GRASS_HTML_BROWSER'] = 'xdg-open'
    os.environ['GRASS_RENDER_FILE_COMPRESSION'] = '9'
    os.environ['GRASS_PAGER'] = 'more'
    os.environ['GRASS_RENDER_IMMEDIATE'] = 'cairo'
    os.environ['GRASS_RENDER_WIDTH'] = '%s' % width
    os.environ['GRASS_RENDER_HEIGHT'] = '%s' % height
    os.environ['GRASS_RENDER_FILE'] = '%s' % output
    g.run_command('d.mon', start='cairo', width=width,
                  height=height, overwrite=True)
    if raster:
        for i in raster:
            g.run_command('d.rast', map=i)
    if vector:
        for i, v in enumerate(vector):
            g.run_command('d.vect', map=v,
                          width=line_width[i], color=line_color[i])
    if raster:
        g.run_command('d.legend',
                      flags=flags,
                      raster=raster[0],
                      fontsize=fontsize,
                      labelnum=labelnum,
                      at='%s,%s,%s,%s' % (at[0], at[1], at[2], at[3]), units=units, digits=digits)
    if north_arrow:
        g.run_command('d.northarrow',
                      style=north_arrow_opts['style'],
                      rotation=north_arrow_opts['rotation'],
                      label=north_arrow_opts['label'],
                      fontsize=north_arrow_opts['fontsize'],
                      color=north_arrow_opts['color'],
                      fill_color=north_arrow_opts['fill_color'],
                      at=f"{north_arrow_opts['at'][0]},{north_arrow_opts['at'][1]}",
                      flags='w')
    g.run_command('d.mon', stop='cairo')
    del os.environ['GRASS_RENDER_FILE']
    # outname = os.path.join(output,i+'.png')
    if embed:
        imageFile = open(output, "rb")
        imagebyte = base64.b64encode(imageFile.read())
        imagestr = imagebyte.decode()
    if clean:
        os.remove(output)
    return imagestr


def swc(suffix=None,
        n=4546380,
        s=4546202,
        w=506185,
        e=506571,
        elevation='bathy',
        search=9,
        skip=3,
        flat=2.0,
        dist=0,
        iter_thin=400,
        area_lesser=70,
        generalize_method='douglas',
        generalize_threshold=2,
        vclean_rmdangle_threshold=[5, 10, 20, 30]):
    if not suffix:
        suffix = 'g'+str(uuid.uuid1()).replace('-', '')
        print('I am using  this:', suffix)
    g.read_command('g.region',
                   n=n,
                   s=s,
                   w=w,
                   e=e,
                   flags='ap')
    g.run_command('r.geomorphon',
                  elevation=elevation,
                  forms=f"{suffix}_forms_swc",
                  search=search,
                  skip=skip,
                  flat=flat,
                  dist=dist,
                  overwrite=True)
    g.run_command('r.mapcalc',
                  expression='%s=if(%s==3 | %s==2,1, null())' % (
                      f'{suffix}_swc', f'{suffix}_forms_swc', f'{suffix}_forms_swc'),
                  overwrite=True)
    g.run_command('r.thin',
                  input=f'{suffix}_swc',
                  output=f'{suffix}_swc_thin',
                  iterations=iter_thin,
                  overwrite=True)
    g.run_command('r.clump',
                  input=f'{suffix}_swc_thin',
                  output=f'{suffix}_swc_thin_clump',
                  flags='d',
                  overwrite=True)
    g.run_command('r.area',
                  input=f'{suffix}_swc_thin_clump',
                  output=f'{suffix}_swc_thin_long',
                  lesser=area_lesser,
                  overwrite=True)
    g.run_command('r.to.vect',
                  input=f'{suffix}_swc_thin_long',
                  output=f'{suffix}_swc_thin_long_v',
                  type='line',
                  overwrite=True)
    g.run_command('v.generalize',
                  input=f'{suffix}_swc_thin_long_v',
                  output=f'{suffix}_swc_thin_long_smooth_v',
                  method=generalize_method,
                  threshold=generalize_threshold,
                  overwrite=True)
    clean_tool = (',').join(['rmdangle' for i in vclean_rmdangle_threshold])
    clean_threshold = (',').join([str(i) for i in vclean_rmdangle_threshold])
    g.run_command('v.clean',
                  input=f'{suffix}_swc_thin_long_smooth_v',
                  output=f'{suffix}_swc_thin_long_smooth_clean_v',
                  type='line',
                  tool=clean_tool,
                  threshold=clean_threshold,
                  overwrite=True)
    return suffix


def sw(suffix=None,
       n=4546380,
       s=4546202,
       w=506185,
       e=506571,
       elevation='bathy',
       search=30,
       skip=7,
       flat=3.8,
       dist=15,
       area_lesser=1000,
       vclean_rmarea_threshold=[10]):
    if not suffix:
        suffix = 'g'+str(uuid.uuid1()).replace('-', '')
    g.read_command('g.region',
                   n=n,
                   s=s,
                   w=w,
                   e=e)
    g.run_command('r.geomorphon',
                  elevation=elevation,
                  forms=f'{suffix}_forms_sw',
                  search=search,
                  skip=skip,
                  flat=flat,
                  dist=dist,
                  overwrite=True)
    g.run_command('r.mapcalc',
                  expression="%s=if(%s==3 | %s==2 | %s==6 | %s==5 , 1, null())" % (f'{suffix}_sw',
                                                                                   f'{suffix}_forms_sw',
                                                                                   f'{suffix}_forms_sw',
                                                                                   f'{suffix}_forms_sw',
                                                                                   f'{suffix}_forms_sw'),
                  overwrite=True)
    g.run_command('r.clump',
                  input=f'{suffix}_sw',
                  output=f'{suffix}_sw_clump',
                  flags='d',
                  overwrite=True)
    g.run_command('r.area',
                  input=f'{suffix}_sw_clump',
                  output=f'{suffix}_sw_clean',
                  lesser=area_lesser,
                  overwrite=True)
    g.run_command('r.neighbors',
                  input=f'{suffix}_sw_clean',
                  output=f'{suffix}_sw_clean_fill',
                  method='maximum',
                  overwrite=True)
    g.run_command('r.to.vect',
                  input=f'{suffix}_sw_clean_fill',
                  output=f'{suffix}_sw_clean_fill_v',
                  type='area',
                  overwrite=True)
    clean_tool = (',').join(['rmarea' for i in vclean_rmarea_threshold])
    clean_threshold = (',').join([str(i) for i in vclean_rmarea_threshold])
    g.run_command('v.clean',
                  input=f'{suffix}_sw_clean_fill_v',
                  output=f'{suffix}_sw_clean_fill_v_clean',
                  tool=clean_tool,
                  threshold=clean_threshold,
                  overwrite=True)
    return suffix


def sw_side(swc_suffix,
            sw_suffix,
            buffer_distance=1,
            elevation='bathy'):
    g.run_command('v.overlay',
                  ainput=f'{swc_suffix}_swc_thin_long_smooth_clean_v',
                  atype='line',
                  binput=f'{sw_suffix}_sw_clean_fill_v_clean',
                  out=f'{sw_suffix}_sw_ridges_v',
                  operator='and',
                  olayer='0,1,0',
                  overwrite=True)
    g.run_command('v.buffer',
                  input=f'{sw_suffix}_sw_ridges_v',
                  output=f'{sw_suffix}_sw_buffer_v',
                  distance=buffer_distance,
                  overwrite=True)
    g.run_command('v.overlay',
                  ainput=f'{sw_suffix}_sw_clean_fill_v_clean',
                  binput=f'{sw_suffix}_sw_buffer_v',
                  operator='not',
                  output=f'{sw_suffix}_sw_splitted_v',
                  overwrite=True)
    g.run_command('v.colors',
                  map=f'{sw_suffix}_sw_splitted_v',
                  use='cat',
                  color='random')
    g.run_command('v.to.rast',
                  input=f'{sw_suffix}_sw_splitted_v',
                  output=f'{sw_suffix}_sw_splitted',
                  type='area', use='cat', overwrite=True)
    g.run_command('r.slope.aspect',
                  elevation=elevation,
                  slope=f'{sw_suffix}_slope_deg',
                  overwrite=True)
    # TODO store stats?
    stats = g.read_command('r.univar',
                           map=f'{sw_suffix}_slope_deg',
                           zones=f'{sw_suffix}_sw_splitted',
                           flags='ge',
                           overwrite=True, sep='=')
    side_a, side_b = [{i.split('=')[0]:float(i.split('=')[1]) for i in j} for j in grouper(
        [i for i in stats.replace(';', '').strip().split('\n')], 17)]
    if side_a['mean'] > side_b['mean']:
        print(side_a['zone'], 'is lee side')
        side_a['side'] = 'lee'
        side_b['side'] = 'stoss'
        g.run_command('v.db.update', map=f'{sw_suffix}_sw_splitted_v',
                      column='a_label', value='lee', where=f"cat={side_a['zone']}")
        g.run_command('v.db.update', map=f'{sw_suffix}_sw_splitted_v', column='a_label',
                      value='stoss', where=f"cat={side_b['zone']}")
    else:
        print(side_b['zone'], 'is lee side')
        side_b['side'] = 'lee'
        side_a['side'] = 'stoss'
        g.run_command('v.db.update', map=f'{sw_suffix}_sw_splitted_v', column='a_label',
                      value='stoss', where=f"cat={side_a['zone']}")
        g.run_command('v.db.update', map=f'{sw_suffix}_sw_splitted_v',
                      column='a_label', value='lee', where=f"cat={side_b['zone']}")
    # TODO: this is a read command .. what to do with it?
    # try print out the output for debug
    g.read_command(
        'v.db.select', map=f'{sw_suffix}_sw_splitted_v').strip().split('\n')
    # TODO: something to return? we may want to export something?
    return side_a, side_b


def sw_metrics(swc_suffix,
               sw_suffix,
               side_stats,
               workers=None,
               transect_split_length=1,
               point_dmax=1,
               elevation='bathy',
               transect_side_distances=[70, 70]):
    g.run_command('v.build.polylines',
                  type='line',
                  input=f'{sw_suffix}_sw_ridges_v',
                  output=f'{sw_suffix}_sw_ridges_v_poliline',
                  cats='no',
                  overwrite=True)
    g.run_command('v.category', option='add',
                  type='line',
                  input=f'{sw_suffix}_sw_ridges_v_poliline',
                  output=f'{sw_suffix}_sw_ridges_v_polilineCAT',
                  overwrite=True)
    g.run_command('v.db.addtable',
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT',
                  layer=1,
                  columns='Length double precision')
    g.run_command('v.to.db',
                  type='line',
                  layer=1,
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT',
                  option='cat',
                  columns='cat', overwrite=True)
    g.run_command('v.to.db',
                  type='line',
                  layer=1,
                  units='meters',
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT',
                  option='length',
                  columns='Length', overwrite=True)
    g.read_command('v.db.select',
                   map=f'{sw_suffix}_sw_ridges_v_polilineCAT')
    # SWC 3D length
    g.run_command('v.split',
                  input=f'{sw_suffix}_sw_ridges_v_polilineCAT',
                  output=f'{sw_suffix}_sw_ridges_v_polilineCAT_split',
                  length=transect_split_length,
                  flags='f',
                  overwrite=True)
    g.run_command('v.to.points',
                  input=f'{sw_suffix}_sw_ridges_v_polilineCAT_split',
                  output=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP',
                  dmax=point_dmax,
                  overwrite=True)
    g.run_command('v.db.droptable',
                  flags='f',
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP',
                  layer=1)
    g.run_command('v.db.droptable',
                  flags='f',
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP',
                  layer=2)
    g.run_command('v.db.addtable',
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP',
                  layer=2,
                  columns='x DOUBLE PRECISION, y DOUBLE PRECISION, z DOUBLE PRECISION')
    g.run_command('v.to.3d',
                  input=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP',
                  output=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP3D',
                  type='point',
                  column='z',
                  layer=2,
                  overwrite=True)
    g.run_command('v.drape',
                  input=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP3D',
                  output=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP3D_draped',
                  elevation=elevation,
                  overwrite=True)
    g.run_command('v.to.db',
                  type='point',
                  layer=2,
                  map=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP3D_draped',
                  option='coor',
                  columns='x,y,z', overwrite=True)
    dp = g.read_command('v.db.select',
                        map=f'{sw_suffix}_sw_ridges_v_polilineCAT_splitP3D_draped',
                        layer=2,
                        separator=',').strip().split('\n')
    matx = np.array([float(i.split(',')[1]) for i in dp[1:]])
    maty = np.array([float(i.split(',')[2]) for i in dp[1:]])
    matz = np.array([float(i.split(',')[3]) for i in dp[1:]])
    pp = np.array([list(i) for i in zip(matx, maty, matz)])
    dist = scipy.spatial.distance.cdist(pp, pp)
    # Distance between endpoints
    max_dist = dist.max()
    # 3D Distance along the line
    max_3d_dist = dist.diagonal(1).sum()
    g.run_command('v.transects',
                  input=f'{sw_suffix}_sw_ridges_v',
                  output=f'{sw_suffix}_sw_ridges_transect_v',
                  transect_spacing=1,
                  dleft=transect_side_distances[0],
                  dright=transect_side_distances[1],
                  overwrite=True)
    lines = g.read_command('v.out.ascii',
                           input=f'{sw_suffix}_sw_ridges_transect_v',
                           output='-',
                           type='line',
                           format='standard',
                           overwrite=True, sep='/n').strip().split('\n')
    coords = getcoords(lines)
    current_region = {i.split('=')[0]: i.split('=')[1] for i in g.read_command(
        'g.region', flags='mu', raster=elevation).strip().split('\n')}
    cc = [{'layer': elevation, 'resolution': current_region['nsres'], 'coordinates': v}
          for i, v in coords.items()]
    prof_ = []
    if not workers:
        workers = os.cpu_count()
    with Pool(workers) as p:
        prof_.append(p.map(makeprofiles, cc))
    prof = prof_[0]
    pr_ = []
    with Pool(workers) as p:
        pr_.append(p.map(getprofile, prof))
    pr = pr_[0]
    plt.figure(figsize=(12, 4))
    plt.grid(True)

    for i in pr:
        plt.plot(i[:, 2], i[:, 3])
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded_profiles_string = base64.b64encode(buf.read())
    # plt.savefig(f"{sw_suffix}_profiles.png")
    # with open(f"{sw_suffix}_profiles.png", "rb") as image_file:
    #    encoded_profiles_string = base64.b64encode(image_file.read())
    dz = [float(np.abs(np.min(i[:, 3])) - np.abs(np.max(i[:, 3]))) for i in pr]
    H = max(dz)
    # Vertical Profile
    new = VectorTopo(f'{sw_suffix}_profile_line')
    cols = [(u'cat', 'INTEGER PRIMARY KEY'),
            (u'heigth', 'DOUBLE')]
    new.open('w', tab_name=f'{sw_suffix}_profile_line', tab_cols=cols)
    line = Line(np.array([pr[np.argmax(dz)][:, 0], pr[np.argmax(dz)][:, 1]]).T)
    new.write(line, cat=1, attrs=(H,))
    new.table.conn.commit()
    new.table.execute().fetchall()
    new.close()
    zc = pr[np.argmax(dz)][:, 3]
    dc = pr[np.argmax(dz)][:, 2]
    plt.figure(figsize=(12, 4))
    plt.grid(True)
    plt.plot(dc, zc, '-')
    plt.ylabel('Depth [m]')
    plt.xlabel('Distance [m]')
    buf = io.BytesIO()
    # plt.savefig(f"{sw_suffix}_profile.png")
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded_profile_string = base64.b64encode(buf.read())
    # with open(f"{sw_suffix}_profile.png", "rb") as image_file:
    #    encoded_profile_string = base64.b64encode(image_file.read())
    # Summit
    x = pr[np.argmax(dz)][np.argmax(pr[np.argmax(dz)][:, 3]), 0]
    y = pr[np.argmax(dz)][np.argmax(pr[np.argmax(dz)][:, 3]), 1]
    z = pr[np.argmax(dz)][np.argmax(pr[np.argmax(dz)][:, 3]), 3]
    # h = max(dz)
    # SW Width
    side_a = side_stats[0]
    side_b = side_stats[1]
    W = H*np.tan(float(side_a['mean'])) + H*np.tan(float(side_b['mean']))
    # SWC Validation
    # SWC reconstruction and matching
    xc = [i[np.argmax(i[:, 3]), 0] for i in pr]
    yc = [i[np.argmax(i[:, 3]), 1] for i in pr]
    zc = [i[np.argmax(i[:, 3]), 3] for i in pr]
    plt.figure(figsize=(12, 4))
    plt.grid(True)
    plt.plot(xc, yc, 'o')
    plt.plot(x, y, 'or')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded_swc_string = base64.b64encode(buf.read())
    # plt.savefig(f"{sw_suffix}_crest_reconstruction.png")
    # with open(f"{sw_suffix}_profile.png", "rb") as image_file:
    #    encoded_swc_string = base64.b64encode(image_file.read())
    xyz = [i for i in map(lambda x: str(x).replace(
        '(', '').replace(')', '').replace(' ', ''), zip(xc, yc, zc))]
    with open(f'{sw_suffix}_t.csv', 'w') as t:
        for i in xyz:
            t.write(i)
            t.write('\n')
    g.run_command('v.in.ascii',
                  input=f'{sw_suffix}_t.csv',
                  output=f'{sw_suffix}_crest_point',
                  separator=',',
                  format='point',
                  columns="x double precision, y double precision, z double precision",
                  z=3,
                  flags='z',
                  overwrite=True)
    g.run_command('v.db.addtable',
                  map=f'{sw_suffix}_crest_point',
                  table=f'{sw_suffix}_crest_point',
                  columns="dist double precision, dist2 double precision",
                  overwrite=True)
    g.run_command('v.db.connect',
                  map=f'{sw_suffix}_crest_point',
                  table=f'{sw_suffix}_crest_point',
                  flags='p',
                  overwrite=True)
    g.run_command('v.distance',
                  from_=f'{sw_suffix}_crest_point',
                  to=f'{sw_suffix}_sw_ridges_v',
                  upload='dist',
                  column='dist')
    g.run_command('v.distance',
                  from_=f'{sw_suffix}_crest_point',
                  to=f'{swc_suffix}_swc_thin_long_v',
                  upload='dist',
                  column='dist2')
    dist = g.read_command('v.db.select',
                          map=f'{sw_suffix}_crest_point').strip().split('\n')
    distance1 = [i.split("|")[1] for i in dist[1:]]
    distance2 = [i.split("|")[2] for i in dist[1:]]
    # Mean displacements
    displacement_1 = np.array(distance1, np.dtype(float)).mean(), np.array(
        distance1, np.dtype(float)).std()
    displacement_2 = np.array(distance2, np.dtype(float)).mean(), np.array(
        distance2, np.dtype(float)).std()

    encoded_img_profile_map_string = makestaticmap(raster=[elevation],
                                                   vector=[
                                                       f'{sw_suffix}_profile_line',
                                                       f'{swc_suffix}_swc_thin_long_smooth_clean_v'],
                                                   fontsize=12,
                                                   units=' m',
                                                   label=elevation,
                                                   width=800,
                                                   height=400,
                                                   at=(5, 8, 10, 90),
                                                   north_arrow=True)
    mean_displacement = np.mean([[displacement_1, displacement_2]])

    results = {'max_dist': max_dist,
               'max_3d_dist': max_3d_dist,
               'H': H,
               'W': W,
               'side_a': side_a,
               'side_b': side_b,
               'mean_displacement': mean_displacement,
               'encoded_profile_string': encoded_profile_string,
               'encoded_profiles_string': encoded_profiles_string,
               'encoded_swc_string': encoded_swc_string,
               'img_profile_map': encoded_img_profile_map_string,
               }
    return results


def clean(suffix):
    g.run_command('g.remove', type_='raster,vector',
                  pattern=f'{suffix}*', flags='f')
