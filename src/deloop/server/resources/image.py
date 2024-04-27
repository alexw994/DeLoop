from fastapi import APIRouter
from typing import *
import base64
from io import BytesIO
from pydantic import Field

from . import storage, bucket_name
from deloop.schema import BaseModel

router = APIRouter(prefix='/api/v1/de', tags=['image'])


class _ImagePostAPIInputData(BaseModel):
    project_name: Optional[str] = Field(None)
    image_base64: str
    image_name: str


@router.post('/images')
def image_post(data: _ImagePostAPIInputData):
    image_bytes = base64.b64decode(data.image_base64.split('data:image/jpeg;base64,')[1])
    bytes_io = BytesIO(image_bytes)
    # minio storage
    bytes_io.seek(0)
    storage.put_object(bucket_name, data.image_name, bytes_io, len(bytes_io.getbuffer()))
    return 'ok'
