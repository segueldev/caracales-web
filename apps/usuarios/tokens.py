"""
=============================================================================
TOKENS JWT PERSONALIZADOS - ACADEMIA FELINA FLOPPA
=============================================================================
Extiende AccessToken y RefreshToken para incluir claims personalizados:
- rol: Rol del usuario (ESTUDIANTE/COORDINADOR)
- user_id: ID del usuario
- username: Nombre de usuario
- email: Email del usuario

CUMPLE REQUERIMIENTO PAUTA: "Payload personalizado (claims) que incluya el Rol del usuario"

-----------------------------------------------------------------------------
CÓMO FUNCIONA UN JWT (lo que hay que saber explicar)
-----------------------------------------------------------------------------
Un JWT son TRES CADENAS unidas por puntos:  <header>.<payload>.<firma>

  header  {"alg":"HS256","typ":"JWT"}                 -> algoritmo usado
  payload {"user_id":7,"rol":"ESTUDIANTE", "exp":...} -> DATOS (claims)
  firma   HMAC-SHA256(header + payload, SECRET_KEY)   -> sello

El payload va en base64: CUALQUIERA puede leerlo, pero NADIE puede modificarlo
sin conocer SECRET_KEY, porque al cambiar un byte la firma deja de coincidir y
el token se rechaza. Por eso NO se guardan contraseñas ni datos sensibles ahí.

CLAVE VERSUS TOKEN: SECRET_KEY es SIMÉTRICA (lo mismo firma que verifica) y
vive sólo en el servidor; JWT la firma y la verifica en el servidor, sin ir a
la BD. Ése es su gran ventaja: 100% stateless.

DÓNDE SE METE EL CLAIM `rol`: se sobrescribe `for_user()`, el método de clase
que SimpleJWT llama cuando emite un token. Así cada token que salga de este
proyecto ya trae el rol dentro, sin tocar la librería.
-----------------------------------------------------------------------------
"""

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from apps.usuarios.models import Usuario


class CustomAccessToken(AccessToken):
    """
    Access Token con claims personalizados.
    El claim 'rol' permite al frontend/backend verificar permisos sin consultar BD.
    """
    @classmethod
    def for_user(cls, user: Usuario):
        token = super().for_user(user)
        # Claims personalizados - INCLUYE ROL PARA RBAC
        token['rol'] = user.rol
        token['username'] = user.username
        token['email'] = user.email
        token['nombre_completo'] = user.get_full_name() or user.username
        return token


class CustomRefreshToken(RefreshToken):
    """
    Refresh Token con claims personalizados.

    `access_token_class` le indica a SimpleJWT qué clase debe usar SU property
    `access_token` (el heredado de la librería) para derivar el access token.
    Así se reutiliza el código probado de SimpleJWT: construye un
    CustomAccessToken, fija el 'exp' con ACCESS_TOKEN_LIFETIME y copia todos
    los claims del refresh descartando sólo `no_copy_claims`
    (token_type, exp, jti).

    NOTA DE CORRECCIÓN: existía un override manual de `access_token` que usaba
    `self.access_token_lifetime`, un atributo que NO existe en SimpleJWT (la
    vida útil real vive en `api_settings.ACCESS_TOKEN_LIFETIME` y la aplica
    `set_exp`). Eso lanzaba AttributeError y devolvía un error 500 en
    POST /api/auth/login/ y /api/auth/refresh/, dejando la autenticación JWT
    completamente inutilizable.
    """
    access_token_class = CustomAccessToken

    @classmethod
    def for_user(cls, user: Usuario):
        token = super().for_user(user)
        # Claims personalizados: al heredar el property de SimpleJWT, todos
        # estos claims viajan al access token al derivarlo.
        token['rol'] = user.rol
        token['username'] = user.username
        token['email'] = user.email
        token['nombre_completo'] = user.get_full_name() or user.username
        return token


def get_tokens_for_user(user: Usuario):
    """
    Función helper para generar par de tokens (access + refresh) con claims personalizados.
    Usada en views de login/registro.
    """
    refresh = CustomRefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nombre_completo': user.get_full_name() or user.username,
            'rol': user.rol,
            'es_estudiante': user.es_estudiante,
            'es_coordinador': user.es_coordinador,
        }
    }