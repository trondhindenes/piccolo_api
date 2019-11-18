from abc import abstractmethod
import typing as t

from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.requests import Request
from piccolo.extensions.user.tables import BaseUser

from .tables import TokenAuth


class TokenProvider:
    """
    Subclass this to provide your own custom token provider.
    """

    @abstractmethod
    async def get_token(self, username: str, password: str) -> t.Optional[str]:
        pass


class PiccoloTokenProvider(TokenProvider):
    async def get_token(self, username: str, password: str) -> t.Optional[str]:
        user = await BaseUser.login(username=username, password=password)
        if user:
            return (
                await TokenAuth.select(TokenAuth.token)
                .first()
                .where(TokenAuth.user == user)
                .run()
            )
        return None


class TokenAuthLoginEndpoint(HTTPEndpoint):

    token_provider: TokenProvider = PiccoloTokenProvider()

    async def post(self, request: Request) -> JSONResponse:
        """
        Return a token if the credentials are correct.
        """
        json = await request.json()
        username = json.get("username")
        password = json.get("password")
        if username and password:
            token = await self.token_provider.get_token(
                username=username, password=password
            )
            if token:
                return JSONResponse({"token": token})
            else:
                raise HTTPException(
                    status_code=401, detail="The credentials were incorrect"
                )
        else:
            raise HTTPException(
                status_code=401, detail="No credentials were found."
            )
