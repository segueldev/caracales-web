"""
=============================================================================
PERMISOS PERSONALIZADOS (RBAC) - ACADEMIA FELINA FLOPPA
=============================================================================
Implementación de permisos basados en roles para DRF.
Roles: ESTUDIANTE (cliente) vs COORDINADOR (admin/gestor).

-----------------------------------------------------------------------------
QUÉ ES RBAC Y CÓMO AQUÍ
-----------------------------------------------------------------------------
RBAC = Role-Based Access Control: el permiso depende del ROL que trae el token,
no de la identidad concreta del usuario.

En DRF un permiso es una clase con dos métodos opcionales:

  has_permission(request, view)     -> ¿PUEDE hacer ESTA petición?  (nivel vista)
  has_object_permission(req, v, obj)-> ¿PUEDE hacerla con ESTE registro? (nivel objeto)

DRF llama a `has_permission` SIEMPRE y a `has_object_permission` sólo cuando
la vista llama a `self.get_object()`. Si devuelve False lanza 403.

¿QUIÉN LEE EL ROL?  La clase `JWTAuthentication` declarada en
`settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` recibe la cabecera
`Authorization: Bearer <token>`, verifica firma y `exp`, extrae el claim
`user_id` y carga el Usuario de la BD. Ese objeto queda en `request.user`,
de modo que `request.user.rol` está disponible dentro de cada permiso sin
hacer ninguna consulta extra.

-----------------------------------------------------------------------------
MATRIZ DE PERMISOS (paleta de la pauta, Proyecto 2)
-----------------------------------------------------------------------------
  PÚBLICO      -> GET /api/catalogo/cursos/    GET /api/catalogo/areas/
  ESTUDIANTE   -> GET/POST/DELETE /api/carro/  POST /api/matriculas/confirmar/
                  GET /api/mis-matriculas/     (IsEstudiante)
  COORDINADOR  -> POST/PUT/DELETE /api/catalogo/cursos/
                  PATCH /api/matriculas/{id}/estado/   (IsCoordinador)

La combinación `IsEstudiante` + `IsOwnerOrCoordinador` es AND: ambas deben
pasar. Así un estudiante sólo ve SU orden aunque adivine el id de otra.
=============================================================================
"""
from rest_framework import permissions
from apps.usuarios.models import Usuario


class IsEstudiante(permissions.BasePermission):
    """
    Permiso: Solo usuarios con rol ESTUDIANTE.
    Usado para: Carro de matrícula, checkout, mis matrículas.
    """
    message = 'Solo estudiantes pueden acceder a este recurso.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == Usuario.Rol.ESTUDIANTE
        )


class IsCoordinador(permissions.BasePermission):
    """
    Permiso: Solo usuarios con rol COORDINADOR.
    Usado para: Gestión de cursos (CRUD), cambio de estados de matrículas.
    """
    message = 'Solo coordinadores académicos pueden acceder a este recurso.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == Usuario.Rol.COORDINADOR
        )


class IsEstudianteOrCoordinador(permissions.BasePermission):
    """
    Permiso: Usuarios autenticados (ESTUDIANTE o COORDINADOR).
    Usado para: Endpoints que requieren login pero ambos roles pueden acceder.
    """
    message = 'Autenticación requerida.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol in [Usuario.Rol.ESTUDIANTE, Usuario.Rol.COORDINADOR]
        )


class IsOwnerOrCoordinador(permissions.BasePermission):
    """
    Permiso: El propietario del recurso (estudiante) O un coordinador.
    Usado para: Ver matrículas propias, detalles de órdenes propias.
    """
    message = 'No tienes permiso para acceder a este recurso.'

    def has_object_permission(self, request, view, obj):
        # Coordinador tiene acceso total
        if request.user.rol == Usuario.Rol.COORDINADOR:
            return True
        # Estudiante solo accede a sus propios recursos
        if hasattr(obj, 'estudiante'):
            return obj.estudiante == request.user
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        return False


class PublicReadOnly(permissions.BasePermission):
    """
    Permiso: Lectura pública (GET, HEAD, OPTIONS), escritura solo autenticados.
    Usado para: Catálogo de cursos y áreas (endpoints públicos).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated