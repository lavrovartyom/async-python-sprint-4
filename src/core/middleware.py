from ipaddress import ip_address, ip_network

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Запрещенные подсети
BLOCKED_SUBNETS = [
    ip_network("192.168.1.0/24"),
    ip_network("10.0.0.0/8"),
]


class BlockSubnetMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = ip_address(request.client.host)

        for subnet in BLOCKED_SUBNETS:
            if client_ip in subnet:
                return Response("Forbidden", status_code=403)

        response = await call_next(request)

        return response
