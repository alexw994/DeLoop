from fastapi import APIRouter, Response
from deloop.schema import UserModel, UserOrm
from . import Session

router = APIRouter(prefix='/api/v1/de')

_AuthUserPostAPIInputData = UserModel


@router.post('/auth/token')
def token(user: _AuthUserPostAPIInputData):
    # read
    try:
        with Session.begin() as sqlsession:
            users = sqlsession.query(UserOrm).filter_by(name=user.name).all()
        if len(users) == 1:
            return Response(status_code=200)
        else:
            return Response(status_code=409)
    except:
        return Response(status_code=500)


@router.post('/auth/user')
def user(user: _AuthUserPostAPIInputData):
    # write
    try:
        with Session.begin() as sqlsession:
            users = sqlsession.query(UserOrm).filter_by(name=user.name).all()
        if len(users) == 1:
            return Response(status_code=409)
        else:
            user_orm = UserOrm(**user.model_dump())

            with Session.begin() as sqlsession:
                sqlsession.add(user_orm)
                sqlsession.commit()
            return Response(status_code=200)
    except Exception as ex:
        raise ex
        return Response(status_code=500)
