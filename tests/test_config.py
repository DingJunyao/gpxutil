from src.gpxutil.core.config import CONFIG_HANDLER


def test_indonesia_road_sign_config():
    cfg = CONFIG_HANDLER.config.traffic_sign.indonesia_road_sign
    assert cfg.template_path.endswith('id_sheild.svg')
    assert cfg.tol_keywords == ['收费', 'Tol']
    assert cfg.font.upper.endswith('ClearviewHwy1W.ttf')
    assert cfg.font.upper_height == 45
    assert cfg.font.lower.endswith('ClearviewHwy2W.ttf')
    assert cfg.font.lower_height == 135


def test_color_blue():
    assert CONFIG_HANDLER.config.traffic_sign.color.blue == '#003E86'


def test_area_lines_config():
    area = CONFIG_HANDLER.config.video_info_layer.frame.area
    assert len(area.lines) == 3
    assert area.lines[0].font_size == 64
    assert area.lines[1].font_size == 44
    assert area.lines[2].font_size == 44
    assert area.bottom_y == 1997
    assert area.line_gap == 8
