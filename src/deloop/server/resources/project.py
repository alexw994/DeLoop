from fastapi import Request, APIRouter, Response
from .utils import sql_read_only_dump, sql_read_only, es_get_record, sql_read_only_trans
from pydantic import Field

from . import scheduler, Session, es, storage, record_index_name, bucket_name, aps
from deloop.schema import *
from deloop.al_backend.backend.base import BaseDetecionALBackend

router = APIRouter(prefix='/api/v1/de', tags=['project'])


@router.put('/projects')
def project_put(data: dict, request: Request):
    assert 'project_name' in data
    project_name = data.pop('project_name')

    with Session.begin() as sqlsession:
        project = sqlsession.query(ProjectOrm).filter_by(name=project_name).all()[0]
        for key, value in data.items():
            if key != 'al_backend_config':
                setattr(project, key, value)

        if 'al_backend_config' in data:
            project.al_backend_config = data['al_backend_config']
            project.has_al_backend = True

        sqlsession.commit()

    project = sql_read_only_trans(ProjectOrm, ProjectModel, name=project_name)[0]
    if project.has_al_backend:
        '''
        Add a job to the scheduler to run the aps.add_schedule_func_http_request_job function at intervals specified by the project's time_interval.
        And delete existed job.
        '''
        aps.add_schedule_func_http_request_job(project_name=project.name, time_interval=project.time_interval)

    return 'ok'


@router.post('/projects')
def project_post(data: ProjectModel, request: Request):
    project = ProjectModel.parse_obj(data)

    # The job has been added successfully. You can now begin adding projects.
    project_orm = ProjectOrm(**project.model_dump())

    with Session.begin() as sqlsession:
        sqlsession.add(project_orm)
        sqlsession.commit()

    project = sql_read_only_trans(ProjectOrm, ProjectModel, name=project.name)[0]
    if project.has_al_backend:
        aps.add_schedule_func_http_request_job(project_name=project.name, time_interval=project.time_interval)

    return 'ok'


@router.get('/projects', response_model=List[ProjectModel])
def project_getall():
    return sql_read_only_dump(ProjectOrm, ProjectModel)


@router.get('/projects/{name}', response_model=ProjectModel)
def project_get(name: str):
    results = sql_read_only_dump(ProjectOrm, ProjectModel, name=name)
    if len(results) == 0:
        return Response(f'找不到project{name}', status_code=404)
    else:
        return results[0]


@router.delete('/projects/{name}')
def project_delete(name: str):
    project_to_delete = sql_read_only(ProjectOrm, name=name)[0]

    with Session.begin() as sqlsession:
        sqlsession.delete(project_to_delete)
        sqlsession.commit()

    # delete job
    jobs = scheduler.get_jobs()
    jobs = [i for i in jobs if i.name == 'project:' + project_to_delete.name]
    for job in jobs:
        scheduler.remove_job(job.id)

    return 'ok'


class _ALCallPutAPIInputData(BaseModel):
    project_name: str
    record_id: Optional[str] = Field(None)


@router.put('/al/schedule')
def al_schedule_call(data: _ALCallPutAPIInputData):
    project_name = data.project_name

    project = sql_read_only_trans(ProjectOrm, ProjectModel, name=project_name)[0]
    al_backend_config = project.al_backend_config
    al_backend = BaseDetecionALBackend(project_name=project.name, config=al_backend_config)
    batch = project.batch
    aps.schedule_func(es, storage, record_index_name, bucket_name, batch, al_backend)
    return 'ok'


@router.put('/al/callback')
def al_callback_call(data: _ALCallPutAPIInputData):
    project_name = data.project_name
    record_id = data.record_id

    project = sql_read_only_trans(ProjectOrm, ProjectModel, name=project_name)[0]
    al_backend_config = project.al_backend_config
    al_backend = BaseDetecionALBackend(project_name=project.name, config=al_backend_config)

    aps.callback_func(es, storage, record_index_name, bucket_name, record_id, al_backend)
    return 'ok'
