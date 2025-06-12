from enum import Enum, unique


@unique
class ChinaMainlandRoadLevel(Enum):
    NATIONAL_EXPWY = 1
    PROVINCIAL_EXPWY = 2
    NATIONAL_ROAD = 3
    PROVINCIAL_ROAD = 4
    COUNTY_ROAD = 5
    TOWN_ROAD = 6
    OTHER = 0

@unique
class ChinaProvinceSingleCharAbbr(Enum):
    BEIJING = '京'
    TIANJIN = '津'
    HEBEI = '冀'
    SHANXI = '晋'
    NEIMENGGU = '蒙'
    LIAONING = '辽'
    JILIN = '吉'
    HEILONGJIANG = '黑'
    SHANGHAI = '沪'
    JIANGSU = '苏'
    ZHEJIANG = '浙'
    ANHUI = '皖'
    FUJIAN = '闽'
    JIANGXI = '赣'
    SHANDONG = '鲁'
    HENAN = '豫'
    HUBEI = '鄂'
    HUNAN = '湘'
    GUANGDONG = '粤'
    GUANGXI = '桂'
    HAINAN = '琼'
    CHONGQING = '渝'
    SICHUAN = '川'
    GUIZHOU = '贵'
    YUNNAN = '云'
    XIZANG = '藏'
    SHAANXI = '陕'
    GANSU = '甘'
    QINGHAI = '青'
    NINGXIA = '宁'
    XINJIANG = '新'
    TAIWAN = '台'
    HONGKONG = '港'
    MACAO = '澳'


