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
=============================================================================
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
    """
    @classmethod
    def for_user(cls, user: Usuario):
        token = super().for_user(user)
        token['rol'] = user.rol
        token['username'] = user.username
        return token

    @property
    def access_token(self):
        """Retorna AccessToken personalizado al refrescar"""
        access = CustomAccessToken()
        access.set_exp(from_time=self.current_time + self.access_token_lifetime)
        access.set_jti()
        access['user_id'] = self['user_id']
        access['rol'] = self['rol']
        access['username'] = self['username']
        access['email'] = self.payload.get('email', '')
        access['nombre_completo'] = self.payload.get('nombre_completo', '')
        return access


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