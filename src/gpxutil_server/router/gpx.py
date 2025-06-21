import asyncio
import codecs
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from src.gpxutil.utils.gpx_convert import convert_gpx

router = APIRouter(prefix="/gpx", tags=["gpx"])

@router.post('convert', name='转换 GPX 坐标', description='转换 GPX 坐标，返回文件')
async def convert(
        gpx_file: UploadFile = File(title='GPX 文件', description='要转换的 GPX 文件'),
        input_type: str = Form(default='wgs84', title='坐标类型', description='文件中的坐标类型'),
        output_type: str = Form(default='gcj02', title='转换后坐标类型', description='要转换的坐标类型')
):
    """
    Convert GPX coordinate type.
    :param gpx_file: GPX file
    :param input_type: Original coordinate type. Value: wgs84, gcj02, bd09
    :param output_type: Coordinate type of output file. Value: wgs84, gcj02, bd09
    :return: Converted GPX file.
    """
    if input_type == output_type:
        gpx_content = await gpx_file.read()  # 使用异步读取文件内容
        return StreamingResponse(iter([gpx_content]), media_type='application/gpx+xml', headers={
            'Content-Disposition': f'attachment;filename={gpx_file.filename}'
        })

    loop = asyncio.get_event_loop()  # 获取当前事件循环
    with ThreadPoolExecutor() as pool:
        dom_tree = await loop.run_in_executor(pool, convert_gpx, gpx_file.file, input_type, output_type)

    # 异步写入XML数据
    with BytesIO() as f_out:
        writer = codecs.getwriter('utf-8')(f_out)
        dom_tree.writexml(writer, encoding='utf-8')
        f_out.seek(0)
        return StreamingResponse(iter([f_out.getvalue()]), media_type='application/gpx+xml', headers={
            'Content-Disposition': f'attachment;filename={gpx_file.filename}'
        })