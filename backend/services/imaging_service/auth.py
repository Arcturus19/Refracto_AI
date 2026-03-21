"""Authentication helpers for imaging service routes."""

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from config import settings


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()

    cookie_token = request.cookies.get(settings.ACCESS_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def _is_internal_request(request: Request) -> bool:
    expected = settings.INTERNAL_API_TOKEN
    provided = request.headers.get("X-Internal-Token")
    return bool(expected and provided and provided == expected)


async def require_authenticated_user(request: Request) -> dict:
    if _is_internal_request(request):
        return {"auth_type": "internal"}

    token = _extract_token(request)
    if not token:
        raise _credentials_exception()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise _credentials_exception() from exc

    if not payload.get("sub"):
        raise _credentials_exception()

    return payload