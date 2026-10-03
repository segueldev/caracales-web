"""
=============================================================================
SERIALIZERS AUTENTICACIÓN - ACADEMIA FELINA FLOPPA
=============================================================================
Serializers para: Registro, Login, Refresh, Perfil, Cambio contraseña.
Incluyen validaciones y campos de rol para JWT claims.
=============================================================================
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from apps.usuarios.models import Usuario
from apps.usuarios.tokens import get_tokens_for_user, CustomRefreshToken


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios.
    Por defecto registra como ESTUDIANTE (rol por defecto del modelo).
    Coordinadores deben ser creados por admin o via django admin.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Contraseña segura (mín 8 chars, mayúscula, minúscula, número)'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmación de contraseña'
    )
    rol = serializers.ChoiceField(
        choices=Usuario.Rol.choices,
        default=Usuario.Rol.ESTUDIANTE,
        required=False,
        help_text='Rol del usuario (solo admins pueden crear coordinadores)'
    )

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'rol', 'telefono', 'biografia'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        rol = validated_data.pop('rol', Usuario.Rol.ESTUDIANTE)
        # Solo permitir crear coordinadores si el request.user es coordinador (en view)
        user = Usuario.objects.create_user(**validated_data, rol=rol)
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Incluir tokens en respuesta de registro
        tokens = get_tokens_for_user(instance)
        data['tokens'] = tokens
        return data


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login (username/email + password).
    Retorna access + refresh tokens con claims de rol.
    """
    username = serializers.CharField(required=False, help_text='Username o email')
    email = serializers.EmailField(required=False, help_text='Email del usuario')
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not username and not email:
            raise serializers.ValidationError('Debe proporcionar username o email.')

        # Autenticar con username o email
        if email:
            try:
                user = Usuario.objects.get(email=email)
                username = user.username
            except Usuario.DoesNotExist:
                raise serializers.ValidationError('Credenciales inválidas.')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Credenciales inválidas.')
        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo.')

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        user = instance['user']
        return get_tokens_for_user(user)


class RefreshSerializer(serializers.Serializer):
    """
    Serializer para refresh token.

    Acá vive TODA la lógica de rotación: la vista sólo valida y devuelve
    `serializer.data`, de modo que no hay dos caminos de código que se
    desincronicen entre la vista y el serializer.
    """
    refresh = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        try:
            token = CustomRefreshToken(attrs['refresh'])
            # Lanza TokenError si el token ya fue usado y está en blacklist.
            token.check_blacklist()
        except Exception:
            raise serializers.ValidationError('Token de refresco inválido o expirado.')
        attrs['token'] = token
        return attrs

    def to_representation(self, instance):
        token = instance['token']
        data = {'access': str(token.access_token)}

        if not jwt_settings.ROTATE_REFRESH_TOKENS:
            data['refresh'] = str(token)
            return data

        # --- Rotación de refresh token ---------------------------------
        # BUG CORREGIDO: antes se hacía `CustomRefreshToken.for_user(user_id)`
        # pasándole el ID (un entero) en vez del objeto usuario; `for_user`
        # hace `getattr(user, 'id')` y reventaba con AttributeError (500).
        user_id = token.payload.get(jwt_settings.USER_ID_CLAIM)
        user = Usuario.objects.filter(pk=user_id).first()
        if user is None:
            data['refresh'] = str(token)
            return data

        data['refresh'] = str(CustomRefreshToken.for_user(user))
        if jwt_settings.BLACKLIST_AFTER_ROTATION:
            token.blacklist()   # consume el refresh recién usado
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para perfil de usuario (lectura/actualización parcial)"""
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    es_estudiante = serializers.BooleanField(read_only=True)
    es_coordinador = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'rol_display', 'telefono', 'avatar', 'biografia',
            'fecha_nacimiento', 'email_notificaciones',
            'es_estudiante', 'es_coordinador',
            'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'rol']


class CambioPasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    password_actual = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    password_nuevo = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'}, validators=[validate_password])
    password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password_actual']):
            raise serializers.ValidationError({'password_actual': 'Contraseña actual incorrecta.'})
        if attrs['password_nuevo'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas nuevas no coinciden.'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['password_nuevo'])
        user.save()
        return user


# ===========================================================================
# SERIALIZERS DE LOGOUT
# ---------------------------------------------------------------------------
# ¿Por qué existen si LogoutView no hace `is_valid()` sobre ellos?
# Porque drf-spectacular genera el esquema OpenAPI a partir de los
# serializers de la vista; sin ellos la petición "unable to guess serializer"
# y ELIMINABA /api/auth/logout/ del Swagger, dejando un endpoint real fuera
# de la documentación.
#
# Se separan request/response porque no son simétricos: lo que se ENVÍA es el
# refresh token a revocar y lo que se RECIBE es un simple mensaje de estado.
# ===========================================================================
class LogoutRequestSerializer(serializers.Serializer):
    """Body de POST /api/auth/logout/: el refresh token que hay que blacklister."""
    refresh = serializers.CharField(
        required=True,
        write_only=True,
        help_text='Refresh token JWT a revocar (se añade a la blacklist).',
    )


class LogoutResponseSerializer(serializers.Serializer):
    """Respuesta del logout: sólo un mensaje legible, nunca el token."""
    detail = serializers.CharField(
        help_text='Estado de la operación (200 OK o 400 si el token no sirve).'
    )