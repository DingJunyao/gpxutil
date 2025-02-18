import io

import cairosvg
from PIL import Image, ImageDraw, ImageFont

chinese_font_path = "asset/font/SourceHanSans_static_super_otc.ttc"
english_font_path = "./asset/SourceSans3-Light.otf"
compass_img_path = "./asset/compass.svg"
big_font = ImageFont.truetype(chinese_font_path, 64, 12)
small_font = ImageFont.truetype(english_font_path, 48)
font_color = '#FFFFFF'
image_size = (3840, 2160)
area_chinese_xy = (191.8085, 1924)
area_english_xy = (192, 1997)
compass_xy = (2248, 1924)

def svg_to_img(svg_path):
    svg = cairosvg.svg2png(url=svg_path, dpi=72)
    return Image.open(io.BytesIO(svg))

image = Image.new(mode='RGBA', size=image_size)
# compass_image = Image.open(compass_img_path)
compass_image = svg_to_img(compass_img_path)
compass_image = compass_image.rotate(-60, expand=False)
draw_table = ImageDraw.Draw(im=image)
draw_table.text(xy=area_chinese_xy, text='河南省 三门峡市 湖滨区', fill=font_color, font=big_font)
draw_table.text(xy=area_english_xy, text='Hubin District, Sanmenxia City, Henan Province', fill=font_color, font=small_font)
image.paste(compass_image, compass_xy)

image.show()  # 直接显示图片
# image.save('满月.png', 'PNG')  # 保存在当前路径下，格式为PNG
image.close()