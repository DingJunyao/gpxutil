import fontforge
import os


def font_to_svgs(font_path, output_dir):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 打开字体文件
    font = fontforge.open(font_path)

    # 遍历字体中的所有字形
    for glyph_item in font.glyphs():
        # 跳过非打印字符（可选）
        if glyph_item.glyphname.startswith('.') or glyph_item.glyphname == '.notdef':
            continue

        # 获取字形对象
        glyph = font[glyph_item.glyphname]
        if type(glyph.codepoint) == str:
            safe_glyph_name = ''.join(c for c in glyph.codepoint.replace('+', '').lower() if c.isalnum() or c in '_-')
            svg_file_path = os.path.join(output_dir, f'{safe_glyph_name}.svg')

            # 保存SVG文件
            glyph.export(svg_file_path)
            # with open(svg_file_path, 'w', encoding='utf-8') as svg_file:
            #     svg_file.write(svg_str)
            print(f'SVG saved to {svg_file_path}')


if __name__ == "__main__":
    font_path = r"asset/font/SourceHanSansCN-Bold.ttf"  # 替换为你的字体文件路径
    output_dir = r'.\asset\source_han_sans_cn_bold'  # 替换为你想要保存SVG文件的目录
    font_to_svgs(font_path, output_dir)