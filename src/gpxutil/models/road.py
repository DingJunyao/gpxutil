from svgwrite import Drawing

from src.gpxutil.models.enum_class import ChinaMainlandRoadLevel, ChinaProvinceSingleCharAbbr
from src.gpxutil.utils.svg_gen import generate_expwy_pad, generate_way_num_pad


class Road:
    def __init__(self, name: str = None, english_name: str = None):
       self.name = name
       self.english_name = english_name
       self.have_sign: bool = False

    def to_svg(self):
        raise NotImplementedError("Not implemented in Road. Use its sub classes.")

    def  to_svg_file(self, path: str):
        self.to_svg()

class ChinaMainlandRoad(Road):
    def __init__(self, name: str = None, code: str = None, province: ChinaProvinceSingleCharAbbr = None, english_name: str = None):
        """

        :param name: 道路名称
        :param code: 道路编号，不用加省份简写
        :param province: 道路所属省份。仅当道路为省级高速公路时，需要填写。
        :param english_name: 英文名
        """
        self.name = name
        self.code = code
        self.province = province
        self.english_name = english_name
        self.have_sign = True

    @property
    def road_level(self) -> ChinaMainlandRoadLevel:
        """
        获取道路等级
        :return: str
        """
        if self.code is None:
            return ChinaMainlandRoadLevel.OTHER
        if self.code.startswith('X'):
            return ChinaMainlandRoadLevel.COUNTY_ROAD
        if self.code.startswith('Y'):
            return ChinaMainlandRoadLevel.TOWN_ROAD
        if self.code.startswith('G'):
            if len(self.code) == 4:
                return ChinaMainlandRoadLevel.NATIONAL_ROAD
            else:
                return ChinaMainlandRoadLevel.NATIONAL_EXPWY
        if self.code.startswith('S'):
            if len(self.code) == 4:
                return ChinaMainlandRoadLevel.PROVINCIAL_ROAD
            else:
                return ChinaMainlandRoadLevel.PROVINCIAL_EXPWY
        return ChinaMainlandRoadLevel.OTHER

    @property
    def code_num(self):
        """
        获取道路编号的数字部分
        :return:
        """
        if self.code is None:
            return None
        return int(self.code[1:])

    def to_svg(self) -> Drawing:
        if self.road_level in [ChinaMainlandRoadLevel.NATIONAL_EXPWY, ChinaMainlandRoadLevel.PROVINCIAL_EXPWY]:
            return generate_expwy_pad(self.code, self.province, self.name)
        return generate_way_num_pad(self.code)

    def to_svg_file(self, path: str):
        self.to_svg().saveas(path)

class ChinaMainlandExpwy(ChinaMainlandRoad):
    def to_svg(self, with_name: bool = False) -> Drawing:
        province = self.province.value if self.road_level == ChinaMainlandRoadLevel.PROVINCIAL_EXPWY else None
        name = self.name if with_name else None
        return generate_expwy_pad(self.code, province, name)

    def to_svg_file(self, path: str, with_name: bool = False):
        self.to_svg(with_name).saveas(path)

class RoadGroup:
    """路的集合"""
    def __init__(self, roads: list[Road], display_name_index: int = 0):
         self.roads = roads
         self.display_name_index = display_name_index

    @property
    def name(self)  -> str:
        return self.roads[self.display_name_index].name

    def gen_sign(self) -> list[Drawing]:
        """
        生成svg
        :return: list[Drawing]
        """
        if self.roads is None or len(self.roads) == 0:
            return None
        sign_list = []
        for road in self.roads:
            if road.have_sign:
                sign_list.append(road.to_svg())
        return sign_list


if __name__ == '__main__':
    # ChinaMainlandExpwy('连霍高速', 'G30').to_svg_file('./out/class_test_g30.svg', with_name=True)

    a = RoadGroup([
        ChinaMainlandExpwy('连霍高速', 'G30'),
        ChinaMainlandExpwy('侯平高速', 'S0111', ChinaProvinceSingleCharAbbr.SHANXI),
        ChinaMainlandRoad('黄河路', 'G310'),
        Road('西城街')
    ])
    i = 0
    for drawing in a.gen_sign():
        drawing.saveas(f'./out/class_test_{i}.svg')
        i += 1