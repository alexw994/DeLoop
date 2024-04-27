import os.path
import urllib.parse
from typing import *
from . import Session, record_index_name, es
from deloop.schema import BaseModel
import socket


def sql_read_only(Orm, **kwargs):
    with Session.begin() as sqlsession:
        query = sqlsession.query(Orm).filter_by(**kwargs).all()
    return query


def sql_read_only_trans(Orm, Model, **kwargs) -> List[BaseModel]:
    with Session.begin() as sqlsession:
        query = sqlsession.query(Orm).filter_by(**kwargs).all()
        results = [Model.from_orm(i) for i in query]
    return results


def sql_read_only_dump(Orm, Model, **kwargs) -> List[Dict]:
    with Session.begin() as sqlsession:
        query = sqlsession.query(Orm).filter_by(**kwargs).all()
        results = [Model.from_orm(i).model_dump() for i in query]
    return results


def es_get_record(image_name=None,
                  size=None,
                  record_id=None,
                  index=record_index_name,
                  **kwargs) -> Dict:
    es.indices.refresh(index=index)
    size = size if size is not None else 10000

    if record_id is not None or image_name is not None or kwargs is not None:
        match_queries = []

        if record_id is not None:
            match_queries.append({"match": {"record_id.keyword": record_id}})
        elif image_name is not None:
            match_queries.append({"match": {"image_name.keyword": image_name}})

        # Add additional search condition
        match_queries.extend(
            {"match": {k + '.keyword' if not k.endswith('.keyword') else k: v}} for k, v in kwargs.items() if
            v is not None)

        query_body = {
            "query": {
                "bool": {
                    "must": match_queries
                }
            },
            "size": size,
            "version": True
        }
    else:
        query_body = {
            "query": {
                "match_all": {}
            },
            "size": size,
            "version": True
        }

    results = es.search(index=index, body=query_body)
    return results


def url_joint(*args):
    url = args[0]
    loc = os.path.join(*args[1:])
    return urllib.parse.urljoin(url, loc)
