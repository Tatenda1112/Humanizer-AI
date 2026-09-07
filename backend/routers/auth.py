import os
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from services import postgres

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


@router.post('/login')
def login(req: LoginRequest, response: Response):
    if not postgres.enabled():
        raise HTTPException(404, 'PostgreSQL login is not enabled')
    token = postgres.login(req.email, req.password)
    if not token:
        raise HTTPException(401, 'Incorrect email or password')
    response.set_cookie(postgres.COOKIE, token, httponly=True, samesite='lax',
                        secure=os.getenv('SESSION_COOKIE_SECURE') == 'true', max_age=43200, path='/')
    return {'message': 'Signed in'}


@router.post('/logout')
def logout(request: Request, response: Response):
    if not postgres.enabled():
        raise HTTPException(404, 'PostgreSQL login is not enabled')
    postgres.logout(request.cookies.get(postgres.COOKIE))
    response.delete_cookie(postgres.COOKIE, path='/')
    return {'message': 'Signed out'}
