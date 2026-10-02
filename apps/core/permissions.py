"""
=============================================================================
PERMISOS PERSONALIZADOS - ACADEMIA FELINA FLOPPA
=============================================================================
Implementación de permisos basados en roles (RBAC) para DRF.
Roles: ESTUDIANTE (cliente) vs COORDINADOR (admin/gestor).
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