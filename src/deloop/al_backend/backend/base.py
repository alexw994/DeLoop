from typing import (
    Any,
    Dict,
    Optional,
    Union,
    List,
    Callable,
)

from abc import ABC
import sys
from pathlib import Path
import requests
from PIL import Image
import numpy.typing as npt
from io import BytesIO
from pydantic import TypeAdapter, model_validator

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from deloop.schema import ItemModel, ALBackendConfigModel, BaseModel


class RequestsPostData(BaseModel):
    data: Optional[Any] = None
    json: Optional[Dict] = None
    headers: Optional[Dict] = None
    params: Optional[List[Any]] = None
    files: Optional[Dict] = None


class BaseDetecionALBackend(BaseModel, ABC):
    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True

    project_name: str
    config: ALBackendConfigModel

    # @model_validator(mode='before')
    # def parse_function(cls, data):
    #     script = data['config'].script
    #
    #     local_dict = {"ItemModel": ItemModel,
    #                   "npt": npt,
    #                   "Image": Image,
    #                   "RequestsPostData": RequestsPostData}
    #     exec("from typing import *", local_dict)
    #
    #     exec(script, local_dict)
    #     data['preprocess_callback'] = local_dict['preprocess_callback']
    #     data['postprocess_callback'] = local_dict['postprocess_callback']
    #     return data

    def infer(self, image: Union[npt.NDArray, Image.Image] = None) -> List[ItemModel]:
        bytes_io = BytesIO()
        image.save(bytes_io, format='jpeg')
        bytes_io.seek(0)
        byte_data = bytes_io.getvalue()
        infer_result = requests.post(self.config.api,
                                     files={"image": byte_data},
                                     headers=self.config.headers).json()
        return TypeAdapter(List[ItemModel]).validate_python(infer_result)
