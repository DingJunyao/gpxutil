from src.gpxutil.models.region import Region
from src.gpxutil.utils.create_pic import build_area_texts, build_road_texts, parse_road_signs
from src.gpxutil.utils.create_pic import generate_pic

CN_ROW = {
    'province': '河南省', 'city': '三门峡市', 'area': '渑池县',
    'province_en': 'Henan Province', 'city_en': 'Sanmenxia City', 'area_en': 'Mianchi County',
    'road_num': 'G310', 'road_name': '黄河路', 'road_name_en': 'Huanghe Rd.',
}
ID_ROW = {
    'province': '东爪哇省', 'city': '玛琅县', 'area': '安佩尔加丁镇',
    'province_id': 'Provinsi Jawa Timur', 'city_id': 'Kabupaten Malang', 'area_id': 'Kecamatan Ampelgading',
    'province_en': 'Province of East Java', 'city_en': 'Malang Regency', 'area_en': 'Ampelgading District',
    'road_num': '35-024', 'road_name': '图卢斯阿尤大街',
    'road_name_id': 'Jl. Raya Tulus Ayu', 'road_name_en': 'Tulus Ayu Main Rd.',
}


def test_build_area_texts_cn():
    assert build_area_texts(CN_ROW, Region.CN) == ['河南省 三门峡市 渑池县',
                                                    'Mianchi County, Sanmenxia City, Henan Province']


def test_build_area_texts_id():
    assert build_area_texts(ID_ROW, Region.ID) == ['东爪哇省 玛琅县 安佩尔加丁镇',
                                                    'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur',
                                                    'Ampelgading District, Malang Regency, Province of East Java']


def test_build_road_texts_cn():
    assert build_road_texts(CN_ROW, Region.CN) == ['黄河路', 'Huanghe Rd.']


def test_build_road_texts_id():
    assert build_road_texts(ID_ROW, Region.ID) == ['图卢斯阿尤大街', 'Jl. Raya Tulus Ayu', 'Tulus Ayu Main Rd.']


def test_parse_road_signs_cn():
    signs = parse_road_signs(CN_ROW, Region.CN)
    assert len(signs) == 1
    assert signs[0] is not None


def test_parse_road_signs_id():
    signs = parse_road_signs(ID_ROW, Region.ID)
    assert len(signs) == 1
    assert signs[0] is not None


def test_parse_road_signs_empty():
    assert parse_road_signs({'road_num': ''}, Region.CN) == []


def test_generate_pic_three_lines():
    img = generate_pic(
        area_texts=['东爪哇省 玛琅县 安佩尔加丁镇',
                    'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur',
                    'Ampelgading District, Malang Regency, Province of East Java'],
        road_texts=['图卢斯阿尤大街', 'Jl. Raya Tulus Ayu', 'Tulus Ayu Main Rd.'],
        road_sign_list=None, compass_angle=90, used_route=1.0, used_time=60,
        remain_route=2.0, remain_time=120, altitude=500, speed=40
    )
    assert img.size == (3840, 2160)
    img.close()


def test_generate_pic_two_lines_cn_backcompat():
    img = generate_pic(
        area_texts=['河南省 三门峡市 渑池县', 'Mianchi County, Sanmenxia City, Henan Province'],
        road_texts=['黄河路', 'Huanghe Rd.'],
        road_sign_list=None, compass_angle=None, used_route=None, used_time=None,
        remain_route=None, remain_time=None, altitude=None, speed=None
    )
    assert img.size == (3840, 2160)
    img.close()


def test_calc_line_positions_bottom_anchored():
    """最后一行锚定 bottom_y，其余行按各自渲染占位高度（ascent+descent）向上堆叠，行间留 gap 空隙"""
    from src.gpxutil.models.config import VideoInfoLayerTextLineConfig
    from src.gpxutil.utils.create_pic import calc_line_positions
    lines = [VideoInfoLayerTextLineConfig(x=192, font_size=64),
             VideoInfoLayerTextLineConfig(x=192, font_size=44),
             VideoInfoLayerTextLineConfig(x=192, font_size=44)]
    texts = ['东爪哇省 玛琅县 安佩尔加丁镇',
             'Kecamatan Ampelgading, Kabupaten Malang',
             'Ampelgading District, Malang Regency']
    tops, fonts = calc_line_positions(texts, lines, bottom_y=1997, gap=8)
    assert tops[-1] == 1997
    # 相邻行：上一行顶 + 上一行渲染占位高度 + gap == 下一行顶（中文占位高于副语言）
    for i in range(len(texts) - 1):
        ascent, descent = fonts[i].getmetrics()
        assert tops[i] + ascent + descent + 8 == tops[i + 1]
    assert tops[0] < tops[1] < tops[2]


def test_calc_line_positions_two_lines():
    """两行时最后一行同样锚定 bottom_y，中文行按渲染占位高度上移"""
    from src.gpxutil.models.config import VideoInfoLayerTextLineConfig
    from src.gpxutil.utils.create_pic import calc_line_positions
    lines = [VideoInfoLayerTextLineConfig(x=192, font_size=64),
             VideoInfoLayerTextLineConfig(x=192, font_size=44)]
    texts = ['河南省 三门峡市 渑池县', 'Mianchi County, Sanmenxia City']
    tops, fonts = calc_line_positions(texts, lines, bottom_y=1997, gap=8)
    assert tops[-1] == 1997
    ascent, descent = fonts[0].getmetrics()
    assert tops[0] + ascent + descent + 8 == tops[1]


def test_calc_line_positions_one_line():
    from src.gpxutil.models.config import VideoInfoLayerTextLineConfig
    from src.gpxutil.utils.create_pic import calc_line_positions
    lines = [VideoInfoLayerTextLineConfig(x=192, font_size=64)]
    tops, fonts = calc_line_positions(['河南省'], lines, bottom_y=1997, gap=8)
    assert tops == [1997]


def test_calc_line_positions_empty():
    from src.gpxutil.utils.create_pic import calc_line_positions
    tops, fonts = calc_line_positions([], [], bottom_y=1997, gap=8)
    assert tops == [] and fonts == []


def test_generate_pic_line_font_dispatch(monkeypatch):
    """ID 三行布局按行分派字体：行 0 中文、行 1/2 英文，字号取配置行 64/44/44"""
    import src.gpxutil.utils.create_pic as create_pic
    calls = []

    def spy_font(line_index, font_size):
        calls.append((line_index, font_size))
        if line_index == 0:
            return create_pic._get_font(create_pic.chinese_font_path, font_size, create_pic.chinese_font_index)
        return create_pic._get_font(create_pic.english_font_path, font_size)

    monkeypatch.setattr(create_pic, '_get_line_font', spy_font)
    img = generate_pic(
        area_texts=['东爪哇省 玛琅县 安佩尔加丁镇',
                    'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur',
                    'Ampelgading District, Malang Regency, Province of East Java'],
        road_texts=['图卢斯阿尤大街', 'Jl. Raya Tulus Ayu', 'Tulus Ayu Main Rd.'],
        road_sign_list=None, compass_angle=90, used_route=1.0, used_time=60,
        remain_route=2.0, remain_time=120, altitude=500, speed=40
    )
    assert calls == [(0, 64), (1, 44), (2, 44), (0, 64), (1, 44), (2, 44)]
    img.close()
