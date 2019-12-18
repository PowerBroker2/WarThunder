import json
import math
import os
import urllib.request
import loguru

from xmltodict import unparse
from PIL import Image, ImageDraw
from requests import get
from requests.exceptions import ReadTimeout, ConnectTimeout

# from main import debug_mode
debug_mode = False
informed = False
mimg = 'http://localhost:8111/map.img'
mobj = 'http://localhost:8111/map_obj.json'
minf = 'http://localhost:8111/map_info.json'

path = os.environ['APPDATA'] + r'\Tacview\Data\Terrain\Textures'


def pythag(a, b):
    return math.sqrt((a ** 2) + (b ** 2))


def get_distance(x1, y1, x2, y2):
    return math.sqrt(((y2 - y1) ** 2) + ((x2 - x1) ** 2))


def latlon2meters(lat1, lon1, lat2, lon2):
    r = 6378.137
    dLat = lat2 * math.pi / 180 - lat1 * math.pi / 180
    dLon = lon2 * math.pi / 180 - lon1 * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * math.sin(dLon/2) * math.sin(dLon/2)
    math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = r * c
    return d * 1000


while True:
    try:
        # with open('map.jpg', 'w') as f:
        #     map_req = get(mimg, timeout=0.02)
        #     f.write(map_req.content)

        urllib.request.urlretrieve('http://localhost:8111/map.img', 'map.jpg')
        inf_req = get(minf, timeout=0.02).json()
        map_obj = get(mobj, timeout=0.02).json()
        loguru.logger.debug(str("map_info.json retrieved"))
        break

    except (json.decoder.JSONDecodeError) as err:
        if not informed:
            loguru.logger.info("WAITING: Halting map information retrieval; REASON: Waiting to join a match")
            informed = True
    except (ReadTimeout, ConnectTimeout) as err:
        pass
        # print(err)


image = Image.open('map.jpg')
image_draw = ImageDraw.Draw(image)

map_max = inf_req['map_max']
map_min = inf_req['map_min']
map_total = map_max[0] - map_min[0]
map_total_x = map_max[0] - map_min[0]
map_total_y = map_max[1] - map_min[1]

grid_zero = inf_req['grid_zero']
grid_step = inf_req['grid_steps']

step_qnty = map_total / grid_step[0]
step_size = image.width / step_qnty
step_offset = map_min[0] - grid_zero[0]

if step_size == map_max[0]:
    # TODO: document this, it was a hack fix for the odd maps that cause scale problems
    '''assuming duel map until found to be other'''
    step_offset = 0
    step_size = 256


pixels_x, pixels_y = image.width, image.height

x_start = 0
y_start = 0
x_end = pixels_x
y_end = pixels_y

for x in range(int(step_offset), int(image.width), int(step_size)):
    line = ((x, y_start), (x, y_end))
    image_draw.line(line, fill=256)

for y in range(int(step_offset), int(image.width), int(step_size)):
    line = ((x_start, y), (x_end, y))
    image_draw.line(line, fill=256)

loguru.logger.debug(str("drawing grid lines"))

af_list = [el for el in map_obj if el['type'] == 'airfield']
for i in range(len(af_list)):
    afsx = af_list[i]['sx'] * pixels_x
    afsy = af_list[i]['sy'] * pixels_y
    afex = af_list[i]['ex'] * pixels_x
    afey = af_list[i]['ey'] * pixels_y
    acol = tuple(af_list[i]['color[]'])
    afln = get_distance(afsx, afsy, afex, afey)

    # prevent the aircraft carriers from being drawn as static objects
    if afln > 20:
        line = ((afsx, afsy), (afex, afey))
        image_draw.line(line, fill=acol, width=10)

loguru.logger.debug(str("drawing airfields"))

if os.path.exists('map.jpg'):
    os.remove('map.jpg')

# TODO: provide a standard .xml to display the custom textures
# lat long (tacview) to mach (war thunder)
# we are using a 1 x 1 (lat x long) grid south west of 0,0
# (lat, long)
UpperLeft  = UL = ( 0, 0)
LowerLeft  = LL = (-1, 0)
UpperRight = UR = ( 0, 1)
LowerRight = LR = (-1, 1)





tex_insert = {
    "Resources": {
        "CustomTextureList": {
            "CustomTexture": {
                "File": "wt.jpg",
                "Projection": "Triangle",
                "BottomLeft": {
                    "Longitude": "0",
                    "Latitude": "-0.5888095854284137"
                },
                "BottomRight": {
                    "Longitude": "0.5887199046005696",
                    "Latitude": "-0.5888095854284137"
                },
                "TopRight": {
                    "Longitude": "0.5887199046005696",
                    "Latitude": "0"
                },
                "TopLeft": {
                    "Longitude": "0",
                    "Latitude": "0"
                }
            }
        }
    }
}

# take away:
# 1 latitudinal degree (in meters) is always the same
# latlon2meters(lat0, lon0, lat1, lon1)

# latlon2meters(0,0,-1,0)
# >>> 111319.49079327357
# latlon2meters(0,1,-1,1)
# >>> 111319.49079327357

# 1 longitudinal degree (in meters) is longer closer to the equator
# length (in meters) of 1 longitudinal degree at 0 degrees of latitude
# latlon2meters(0, 0, 0, 1)
# >>> 111319.49079327357

# length (in meters) of 1 longitudinal degree at 1 degrees of latitude
# latlon2meters(-1, 0, -1, 1)
# >>> 111302.53586533663



scalar_lon_min = latlon2meters( 0,  0,  0,  1)
scalar_lon_max = latlon2meters(-1,  0, -1,  1)
# these two are the same; kept for consistency
scalar_lat_min = latlon2meters( 0,  0, -1,  0)
scalar_lat_max = latlon2meters( 0,  1, -1,  1)



tl_lat =  0
tl_lon =  0

bl_lat = map_total_y / scalar_lat_max * -1
bl_lon = 0

tr_lat = 0
tr_lon = map_total_x / scalar_lon_max

br_lat = map_total_y / scalar_lat_min * -1
br_lon = map_total_x / scalar_lon_min

tex_insert['Resources']['CustomTextureList']['CustomTexture']['BottomLeft']['Longitude'] = bl_lon
tex_insert['Resources']['CustomTextureList']['CustomTexture']['BottomLeft']['Latitude'] = bl_lat
tex_insert['Resources']['CustomTextureList']['CustomTexture']['BottomRight']['Longitude'] = br_lon
tex_insert['Resources']['CustomTextureList']['CustomTexture']['BottomRight']['Latitude'] = br_lat
tex_insert['Resources']['CustomTextureList']['CustomTexture']['TopLeft']['Longitude'] = tl_lon
tex_insert['Resources']['CustomTextureList']['CustomTexture']['TopLeft']['Latitude'] = tl_lat
tex_insert['Resources']['CustomTextureList']['CustomTexture']['TopRight']['Longitude'] = tr_lon
tex_insert['Resources']['CustomTextureList']['CustomTexture']['TopRight']['Latitude'] = tr_lat


# TODO: check for existing .xml and append rather than overwrite

with open(path + '\CustomTextureList.xml', 'w') as fw:
    fw.write(unparse(tex_insert, pretty=True))

loguru.logger.debug(str("setting size for tacview scaling"))

if debug_mode:
    image.save('wt.jpg')

if os.path.exists(path):
    image.save(path + '\wt.jpg')

loguru.logger.debug(str("image saved to: " + path + '\wt.jpg'))

