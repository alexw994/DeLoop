import json

from typing import *
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import declarative_base
from typing_extensions import Annotated
from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, StringConstraints, Field, model_validator
from enum import Enum as _Enum


class Enum(_Enum):
    def __eq__(self, other):
        return self.value == other or self == other


class BaseModel(_BaseModel):
    model_config = ConfigDict(from_attributes=True,
                              use_enum_values=True)

    def encode(self, *args, **kwargs):
        return self.json()

    def dict(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().dict(*args, **kwargs)

    def model_dump(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().model_dump(*args, **kwargs)


Base = declarative_base()


class UserOrm(Base):
    __tablename__ = 'user'

    name = Column(String(50), primary_key=True, unique=True, nullable=False)
    password = Column(String(100), nullable=False)


class ProjectOrm(Base):
    __tablename__ = 'project'

    name = Column(String(100), primary_key=True, nullable=False, unique=True)
    infer_model = Column(Text, nullable=False)
    type = Column(Text, nullable=False)

    has_al_backend = Column(Boolean, nullable=False)
    al_backend_config = Column(JSON, nullable=True)
    batch = Column(Integer, nullable=True)
    describle = Column(Text, nullable=True)
    method = Column(String(20), nullable=True)
    time_interval = Column(Integer, nullable=True)


class StatusEnum(Enum):
    INVALID = "invalid"
    HUMAN = "human_annotation_completed"
    AUTO = "auto_annotation_completed"
    ORA = "pending_oracle_annotation"
    INIT = "initialization"


class ProjectTypeEnum(Enum):
    ObjectDetection = 'ObjectDetection'


class UserModel(BaseModel):
    name: Annotated[str, StringConstraints(max_length=50)]
    password: Annotated[str, StringConstraints(max_length=100)]


class ALBackendConfigModel(BaseModel):
    api: Annotated[str, StringConstraints(max_length=100)]
    headers: dict = {}

    @model_validator(mode='before')
    def parse_function(cls, data):
        headers = data.get('headers')
        if headers:
            data['headers'] = {}
        elif isinstance(headers, str):
            data['headers'] = json.loads(headers)
        return data


class ProjectModel(BaseModel):
    name: Annotated[str, StringConstraints(max_length=100)]
    infer_model: str
    type: Optional[ProjectTypeEnum] = ProjectTypeEnum.ObjectDetection

    has_al_backend: bool = False
    al_backend_config: Optional[ALBackendConfigModel] = Field(None)
    batch: int = 50
    describle: Optional[str] = ''
    method: Optional[Annotated[str, StringConstraints(max_length=20)]]
    time_interval: Optional[int] = 60  # minutes

    @model_validator(mode='before')
    def parse_function(cls, data):
        if isinstance(data, dict):
            time_interval = data.get('time_interval')
            if time_interval is None:
                data['time_interval'] = 60

            batch = data.get('batch')
            if batch is None:
                data['batch'] = 50

            method = data.get('method')
            if method is None:
                data['method'] = 'FN'

            type = data.get('type')
            if type is None:
                data['type'] = ProjectTypeEnum.ObjectDetection

        else:
            time_interval = data.time_interval
            if time_interval is None:
                data.time_interval = 60

            batch = data.batch
            if batch is None:
                data.batch = 50

            method = data.method
            if method is None:
                data.method = 'FN'

            type = data.type
            if type is None:
                data.type = ProjectTypeEnum.ObjectDetection

        return data


class BBoxModel(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ItemModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    class_field: Optional[int] = Field(-1, alias='class')
    confidence: float
    box: BBoxModel


class DeRecordModel(BaseModel):
    bboxes: List[ItemModel]
    project_name: str
    image_name: str
    timestamp: str
    state: StatusEnum
    record_id: str
    uncertainty: Optional[float]
    image_shared_url: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)


class LLMRecordType(Enum):
    CONVERSATION = 'conversation'
    INSTRUCTION = 'instruction'
    ORIGNALTEXT = 'orignal_text'


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMConversation(BaseModel):
    messages: List[LLMMessage]


class LLMInstruction(BaseModel):
    prompt: str
    completion: str


class LLMRecordModel(BaseModel):
    type: LLMRecordType
    conversation: Optional[LLMConversation]
    instruction: Optional[LLMInstruction]
    orignal_text: Optional[str]

    project_name: str
    timestamp: str
    state: StatusEnum
    record_id: str
    uncertainty: Optional[float]
    json_shared_url: str

    @model_validator(mode='before')
    def parse_function(cls, data):
        assert data.get('conversation') & data.get('instruction') & data.get('orignal_text')
        return data
