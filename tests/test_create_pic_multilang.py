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
    'road_num': '16-024', 'road_name': '图卢斯阿尤大街',
    'road_name_id': 'Jl. Raya Tulus Ayu', 'road_name_en': 'Tulus Ayu Main Rd.',
}

ID_AREA_TEXTS = [('zh', '东爪哇省 玛琅县 安佩尔加丁镇'),
                 ('id', 'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur'),
                 ('en', 'Ampelgading District, Malang Regency, Province of East Java')]
ID_ROAD_TEXTS = [('zh', '图卢斯阿尤大街'), ('id', 'Jl. Raya Tulus Ayu'), ('en', 'Tulus Ayu Main Rd.')]


def test_build_area_texts_cn():
    assert build_area_texts(CN_ROW, Region.CN) == [('zh', '河南省 三门峡市 渑池县'),
                                                   ('en', 'Mianchi County, Sanmenxia City, Henan Province')]


def test_build_area_texts_id():
    assert build_area_texts(ID_ROW, Region.ID) == ID_AREA_TEXTS


def test_build_road_texts_cn():
    assert build_road_texts(CN_ROW, Region.CN) == [('zh', '黄河路'), ('en', 'Huanghe Rd.')]


def test_build_road_texts_id():
    assert build_road_texts(ID_ROW, Region.ID) == ID_ROAD_TEXTS


def test_build_texts_skip_missing_language():
    """印尼语列为空值时该行剔除，英语上移但仍按 en 分派（正体）"""
    row = {'province': '东爪哇省', 'city': '玛琅县', 'area': '安佩尔加丁镇',
           'province_id': '', 'city_id': '', 'area_id': '',
           'province_en': 'Province of East Java', 'city_en': 'Malang Regency', 'area_en': 'Ampelgading District',
           'road_name': '图卢斯阿尤大街', 'road_name_id': '', 'road_name_en': 'Tulus Ayu Main Rd.'}
    assert build_area_texts(row, Region.ID) == [
        ('zh', '东爪哇省 玛琅县 安佩尔加丁镇'),
        ('en', 'Ampelgading District, Malang Regency, Province of East Java')]
    assert build_road_texts(row, Region.ID) == [('zh', '图卢斯阿尤大街'), ('en', 'Tulus Ayu Main Rd.')]


def test_build_texts_zh_suffix_columns():
    """主语言列兼容 _zh 后缀：CSV 仅有 province_zh 等列时仍能取到中文"""
    row = {'province_zh': '东爪哇省', 'city_zh': '玛琅县', 'area_zh': '安佩尔加丁镇',
           'province_id': 'Provinsi Jawa Timur', 'city_id': 'Kabupaten Malang', 'area_id': 'Kecamatan Ampelgading',
           'province_en': 'Province of East Java', 'city_en': 'Malang Regency', 'area_en': 'Ampelgading District',
           'road_name_zh': '图卢斯阿尤大街',
           'road_name_id': 'Jl. Raya Tulus Ayu', 'road_name_en': 'Tulus Ayu Main Rd.'}
    assert build_area_texts(row, Region.ID) == ID_AREA_TEXTS
    assert build_road_texts(row, Region.ID) == ID_ROAD_TEXTS


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


def _id_tol_row(road_name_id: str) -> dict:
    return {'province': '东爪哇省', 'city': '玛琅县', 'area': '安佩尔加丁镇',
            'province_id': 'Provinsi Jawa Timur', 'province_en': 'Province of East Java',
            'road_num': '1', 'road_name': '图卢斯阿尤大街',
            'road_name_id': road_name_id, 'road_name_en': 'Tulus Ayu Main Rd.'}


def test_parse_road_signs_tol_by_indonesian_name(monkeypatch):
    """主语言路名不含关键词、印尼语路名含 'Tol'：盾牌按 TOL 生成（多语言路名参与判断）"""
    import src.gpxutil.utils.create_pic as create_pic
    # 清空全局缓存，保证本测试生成新盾牌而非复用其他测试的产物
    monkeypatch.setattr(create_pic, 'road_num_svg_cache', {})
    tol_signs = parse_road_signs(_id_tol_row('Jalan Tol Tulus Ayu'), Region.ID)
    nasional_signs = parse_road_signs(_id_tol_row('Jalan Raya Tulus Ayu'), Region.ID)
    # 同编号不同等级：色带文字路径不同
    assert tol_signs[0].tostring() != nasional_signs[0].tostring()


def test_parse_road_signs_cache_separates_levels(monkeypatch):
    """同编号不同等级先后渲染：缓存 key 须区分等级，后者不被前者污染"""
    import src.gpxutil.utils.create_pic as create_pic
    monkeypatch.setattr(create_pic, 'road_num_svg_cache', {})
    first = parse_road_signs(_id_tol_row('Jalan Raya Tulus Ayu'), Region.ID)[0].tostring()
    second = parse_road_signs(_id_tol_row('Jalan Tol Tulus Ayu'), Region.ID)[0].tostring()
    assert first != second


def test_generate_pic_three_lines():
    img = generate_pic(
        area_texts=ID_AREA_TEXTS,
        road_texts=ID_ROAD_TEXTS,
        road_sign_list=None, compass_angle=90, used_route=1.0, used_time=60,
        remain_route=2.0, remain_time=120, altitude=500, speed=40
    )
    assert img.size == (3840, 2160)
    img.close()


def test_generate_pic_two_lines_cn_backcompat():
    img = generate_pic(
        area_texts=[('zh', '河南省 三门峡市 渑池县'), ('en', 'Mianchi County, Sanmenxia City, Henan Province')],
        road_texts=[('zh', '黄河路'), ('en', 'Huanghe Rd.')],
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
    texts = ID_AREA_TEXTS
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
    texts = [('zh', '河南省 三门峡市 渑池县'), ('en', 'Mianchi County, Sanmenxia City')]
    tops, fonts = calc_line_positions(texts, lines, bottom_y=1997, gap=8)
    assert tops[-1] == 1997
    ascent, descent = fonts[0].getmetrics()
    assert tops[0] + ascent + descent + 8 == tops[1]


def test_calc_line_positions_one_line():
    from src.gpxutil.models.config import VideoInfoLayerTextLineConfig
    from src.gpxutil.utils.create_pic import calc_line_positions
    lines = [VideoInfoLayerTextLineConfig(x=192, font_size=64)]
    tops, fonts = calc_line_positions([('zh', '河南省')], lines, bottom_y=1997, gap=8)
    assert tops == [1997]


def test_calc_line_positions_empty():
    from src.gpxutil.utils.create_pic import calc_line_positions
    tops, fonts = calc_line_positions([], [], bottom_y=1997, gap=8)
    assert tops == [] and fonts == []


def test_get_line_font_dispatch_by_language():
    """字体按语言分派：zh 中文字体、id 斜体字体（与正体不同文件）、其余英文正体"""
    import src.gpxutil.utils.create_pic as create_pic
    zh_font = create_pic._get_line_font('zh', 44)
    id_font = create_pic._get_line_font('id', 44)
    en_font = create_pic._get_line_font('en', 44)
    assert zh_font.path == create_pic.chinese_font_path
    assert id_font.path == create_pic.english_italic_font_path
    assert en_font.path == create_pic.english_font_path
    # 配置了斜体字体时，印尼语与英语必须来自不同字体文件
    assert create_pic.english_italic_font_path != create_pic.english_font_path


def test_generate_pic_line_font_dispatch(monkeypatch):
    """ID 三行布局按语言分派字体：zh/id/en 各行字号取配置行 64/44/44"""
    import src.gpxutil.utils.create_pic as create_pic
    calls = []

    def spy_font(lang, font_size):
        calls.append((lang, font_size))
        return create_pic._get_font(
            create_pic.chinese_font_path if lang == 'zh'
            else create_pic.english_italic_font_path if lang == 'id'
            else create_pic.english_font_path,
            font_size,
            create_pic.chinese_font_index if lang == 'zh' else 0)

    monkeypatch.setattr(create_pic, '_get_line_font', spy_font)
    img = generate_pic(
        area_texts=ID_AREA_TEXTS,
        road_texts=ID_ROAD_TEXTS,
        road_sign_list=None, compass_angle=90, used_route=1.0, used_time=60,
        remain_route=2.0, remain_time=120, altitude=500, speed=40
    )
    assert calls == [('zh', 64), ('id', 44), ('en', 44), ('zh', 64), ('id', 44), ('en', 44)]
    img.close()


def test_generate_pic_font_dispatch_no_id_line(monkeypatch):
    """印尼语缺失时两行布局仍按语言分派：zh/en，不出现 id 斜体"""
    import src.gpxutil.utils.create_pic as create_pic
    calls = []

    def spy_font(lang, font_size):
        calls.append((lang, font_size))
        return create_pic._get_font(create_pic.english_font_path, font_size)

    monkeypatch.setattr(create_pic, '_get_line_font', spy_font)
    img = generate_pic(
        area_texts=[('zh', '东爪哇省 玛琅县 安佩尔加丁镇'),
                    ('en', 'Ampelgading District, Malang Regency')],
        road_texts=[('zh', '图卢斯阿尤大街'), ('en', 'Tulus Ayu Main Rd.')],
        road_sign_list=None, compass_angle=None, used_route=None, used_time=None,
        remain_route=None, remain_time=None, altitude=None, speed=None
    )
    assert calls == [('zh', 64), ('en', 44), ('zh', 64), ('en', 44)]
    img.close()
