from enum import Enum


class CoordinateType(str, Enum):
    WGS84 = 'wgs84'
    GCJ02 = 'gcj02'
    BD09 = 'bd09'