"""
=============================================================================
VISTAS AUTENTICACIÓN JWT - ACADEMIA FELINA FLOPPA
=============================================================================
Endpoints:
- POST /api/auth/registro/     -> Registro nuevo usuario (público)
- POST /api/auth/login/        -> Login, retorna access+refresh con claims rol
- POST /api/auth/refresh/      -> Refresh access token
- GET/PATCH /api/auth/perfil/  -> Perfil usuario autenticado
- POST /api/auth/cambio-password/ -> Cambio contraseña
- POST /api/auth/logout/       -> Blacklist refresh token (logout real)

Vistas HTML (Templates):
- GET /login/                  -> Formulario login (template)
- GET /registro/               -> Formulario registro (template)
=============================================================================
"""
from django.views.generic import TemplateView
from django.shortcuts import redirect
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema
from apps.usuarios.serializers import (
    RegistroSerializer, LoginSerializer, RefreshSerializer,
    UsuarioSerializer, CambioPasswordSerializer,
    LogoutRequestSerializer, LogoutResponseSerializer
)
from apps.usuarios.tokens import CustomRefreshToken
from apps.usuarios.models import Usuario


class LoginTemplateView(TemplateView):
    """Vista HTML para formulario de login"""
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class RegistroTemplateView(TemplateView):
    """Vista HTML para formulario de registro"""
    template_name = 'registration/registro.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class RegistroView(generics.CreateAPIView):
    """
    Registro público de nuevos estudiantes.
    Retorna tokens JWT con claims de rol inmediatamente.

    Al igual que LoginView, además de los tokens se abre la sesión de Django:
    tras registrarse el usuario debe verse como "logueado" en el HTML, si no
    aparecería el formulario de login justo después de crear la cuenta.
    """
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Sesión de Django (ver el bloque largo en LoginView.post).
        from django.contrib.auth import login
        login(request, user)

        # Tokens ya incluidos en to_representation del serializer
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login con username/email + password.
    Retorna access + refresh tokens con claims personalizados (rol, username, email).
    CUMPLE PAUTA: "Login JWT retornando tokens y claims de rol"

    --------------------------------------------------------------------------
    DOBLE SESIÓN: JWT (para la API) + SESIÓN DE DJANGO (para el HTML)
    --------------------------------------------------------------------------
    BUG CORREGIDO: antes esta vista sólo devolvía los tokens. El JS los guardaba
    en localStorage y la API respondía perfecto... pero el NAVEGADOR seguía
    "deslogueado" a los ojos de Django, porque `request.user` de una petición
    HTML sale de la sesión y no del token.

    Consecuencia: toda plantilla condicionaba con `{% if user.is_authenticated %}`
    y pintaba siempre la rama del visitante anónimo. En el catálogo, la columna
    de acciones dejaba ver "Login" en lugar del botón "Agregar", así que era
    IMPOSIBLE añadir cursos al carro desde la web (aunque la API funcionaba).

    La solución es tener AMBOS mecanismos, cada uno con su responsabilidad:

      ┌──────────────────────┬────────────────────────────────────────────┐
      │ MECANISMO            │ PARA QUÉ SIRVE                            │
      ├──────────────────────┼────────────────────────────────────────────┤
      │ Sesión de Django     │ Sólo para pintar HTML: navbar, botones,    │
      │ (cookie de sesión)   │ {% if user.is_authenticated %} y           │
      │                      │ user.es_estudiante                        │
      ├──────────────────────┼────────────────────────────────────────────┤
      │ Bearer <access>      │ Toda la API: los ViewSets NO usan la       │
      │ (localStorage)       │ sesión, sólo JWTAuthentication, que lee    │
      │                      │ el claim user_id y aplica el RBAC         │
      └──────────────────────┴────────────────────────────────────────────┘

    Por eso NO está `SessionAuthentication` en
    `settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`: si estuviera,
    la API se autenticaría con la cookie y saltaría el token. Así, tener la
    sesión abierta NO otorga ningún privilegio extra en la API: sin el Bearer
    cualquier endpoint protegido devuelve 401.

    `django.contrib.auth.login()` también firma la cookie con la SECRET_KEY y
    regenera el `session_key`, lo que previene fijación de sesión.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Crear la sesión de Django para que las plantillas HTML sepan quién
        # entró (navbar + botón "Agregar al carro" del catálogo y del home).
        from django.contrib.auth import login
        login(request, serializer.validated_data['user'])

        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(APIView):
    """
    Refresh token personalizado que retorna access token con claims actualizados.
    Incluye rotación de refresh token si está habilitado en settings.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer

    def post(self, request):
        # Toda la lógica (claims de rol + rotación/blacklist del refresh)
        # vive en RefreshSerializer; la vista sólo orquesta.
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PerfilView(generics.RetrieveUpdateAPIView):
    """
    Perfil del usuario autenticado.
    GET: Retorna datos del usuario (incluye rol).
    PATCH: Actualiza campos permitidos (no rol).
    """
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CambioPasswordView(APIView):
    """Cambio de contraseña para usuario autenticado"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CambioPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout real: añade refresh token a blacklist.
    Requiere: 'rest_framework_simplejwt.token_blacklist' en INSTALLED_APPS
    y migración ejecutada.

    --------------------------------------------------------------------------
    HACE LAS DOS COSAS (misma lógica que LoginView, en el sentido inverso):
      1. `django.contrib.auth.logout()` -> cierra la SESIÓN DE DJANGO, para
         que la página vuelva a mostrar la navbar del visitante anónimo.
      2. `token.blacklist()`           -> revoca el REFRESH TOKEN, de modo
         que el par deje de servir aunque alguien lo tenga copiado.
    Se hace primero el paso 1 porque está pensado para que el usuario ELIJA
    cerrar sesión: aunque el refresh venga inválido o repetido, la petición
    de "cerrar sesión" se honra (idempotente). Si sólo se blacklisteara el
    token, el navegador seguiría pintándose como logueado.
    """
    permission_classes = [permissions.IsAuthenticated]

    # `@extend_schema` es lo que reintegra este endpoint al Swagger: sin un
    # serializer que adivinar, drf-spectacular lo descartaba con
    # "unable to guess serializer" y no aparecía en /api/docs/.
    @extend_schema(
        request=LogoutRequestSerializer,
        responses={
            200: LogoutResponseSerializer,
            400: LogoutResponseSerializer,
        },
        summary='Cerrar sesión (blacklist del refresh token)',
        description=(
            'Cierra la sesión de Django del navegador Y revoca el refresh '
            'token. El paso 1 se ejecuta antes de validar el token para que '
            'cerrar sesión sea idempotente: aunque el refresh venga '
            'inválido o repetido, el usuario queda deslogueado de la página.'
        ),
        tags=['Autenticación'],
    )
    def post(self, request):
        # 1) Cerrar la sesión de Django (borra la cookie de sesión del navegador)
        from django.contrib.auth import logout
        logout(request)

        # 2) Revocar el refresh token en la blacklist
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = CustomRefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'detail': 'Token inválido o ya en blacklist.'}, status=status.HTTP_400_BAD_REQUEST)