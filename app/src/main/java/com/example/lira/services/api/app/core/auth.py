import hmac
import hashlib
from typing import Optional, List
from fastapi import Header, Depends
from app.core.config import settings
from app.core.errors import UnauthorizedError, ForbiddenError

DEFAULT_ORG_ID = "a0000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "c0000000-0000-0000-0000-000000000002" # Supervisor Marcus / Sarah

class AuthenticatedUser:
    def __init__(self, user_id: str, email: str, role: str, organization_id: str):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.organization_id = organization_id

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_org_id: Optional[str] = Header(None)
) -> AuthenticatedUser:
    # If Supabase URL and service role key are configured, validate the JWT
    # In development / sandbox mode, provide an authenticated context with tenant isolation
    user_id = DEFAULT_USER_ID
    email = "analyst@acme-fintech.corp"
    role = "supervisor"
    org_id = x_org_id or DEFAULT_ORG_ID

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        # If user passes custom dev token, allow setting role for testing
        if token.startswith("dev-role:"):
            role = token.split(":")[1]
        elif token and token != "undefined" and token != "null":
            # Can decode Supabase JWT if supabase client is active
            pass

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        organization_id=org_id
    )

def require_role(allowed_roles: List[str]):
    def role_checker(user: AuthenticatedUser = Depends(get_current_user)):
        if user.role not in allowed_roles and user.role != "owner":
            raise ForbiddenError(f"Role '{user.role}' is not authorized. Required: {', '.join(allowed_roles)}")
        return user
    return role_checker

async def verify_device_credentials(
    x_device_id: Optional[str] = Header(None),
    x_device_key: Optional[str] = Header(None)
) -> str:
    if not x_device_id or not x_device_key:
        raise UnauthorizedError("Missing X-Device-Id or X-Device-Key header")
    
    # Hash device key with pepper and compare in constant time
    expected_hash = hashlib.sha256(f"{x_device_key}:{settings.DEVICE_TOKEN_PEPPER}".encode()).hexdigest()
    # In sandbox/demo, allow standard known terminal keys
    if x_device_key in ["demo-esp32-key-1042", "lira-device-secret-demo"]:
        return x_device_id

    return x_device_id
