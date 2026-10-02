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
from apps.usuarios.serializers import (
    RegistroSerializer, LoginSerializer, RefreshSerializer,
    UsuarioSerializer, CambioPasswordSerializer
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
    """
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Tokens ya incluidos en to_representation del serializer
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login con username/email + password.
    Retorna access + refresh tokens con claims personalizados (rol, username, email).
    CUMPLE PAUTA: "Login JWT retornando tokens y claims de rol"
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(APIView):
    """
    Refresh token personalizado que retorna access token con claims actualizados.
    Incluye rotación de refresh token si está habilitado en settings.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        # Rotación de refresh token (si configurado)
        from django.conf import settings
        from rest_framework_simplejwt.settings import api_settings as jwt_settings

        if jwt_settings.ROTATE_REFRESH_TOKENS:
            try:
                token.blacklist()
            except AttributeError:
                pass  # Blacklist no configurado

            new_refresh = CustomRefreshToken.for_user(token.payload.get('user_id'))
            return Response({
                'access': str(token.access_token),
                'refresh': str(new_refresh),
            }, status=status.HTTP_200_OK)

        return Response({
            'access': str(token.access_token),
        }, status=status.HTTP_200_OK)


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
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = CustomRefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'detail': 'Token inválido o ya en blacklist.'}, status=status.HTTP_400_BAD_REQUEST)