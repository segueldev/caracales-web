"""
=============================================================================
COMANDO: poblar_demo
=============================================================================
Carga datos de demostración en PostgreSQL para poder recorrer el sistema
completo antes de la defensa del EVA 2:

    python manage.py poblar_demo

Crea (de forma idempotente, se puede ejecutar varias veces):
  * 5 áreas de conocimiento (Caza, Sigilo, Ronroneo, Trepar, Historia Felina)
  * 8 cursos PUBLICADOS con cupos, precios y fechas reales
  * 4 estudiantes de prueba (rol ESTUDIANTE) con su carro 1:1 vacío
  * 1 coordinador de prueba (rol COORDINADOR) si no existe

Cuentas generadas (password para todos: "floppa123"):
    estudiante1..4  /  coordinador  (ya existe)
=============================================================================
"""
from datetime import timedelta

from django.contrib.auth.hashers import identify_hasher
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.academico.models import AreaConocimiento, Curso
from apps.usuarios.models import Usuario


def _clave_definida(usuario):
    """
    Devuelve True sólo si el usuario tiene una contraseña con hash real.

    Motivo: `has_usable_password()` de Django 5 considera "utilizable" una
    cadena vacía (sólo descarta las claves inutilizables "!" + aleatorio),
    por lo que una cuenta creada con `password = ''` pasaría ese chequeo y
    quedaría con una clave con la que NADIE puede entrar. Aquí además se
    valida que el algoritmo del hash sea reconocible.
    """
    if not usuario.password:
        return False
    try:
        identify_hasher(usuario.password)
    except ValueError:          # algoritmo de hash desconocido
        return False
    return True


# Catálogo de demostración: (nombre, icono, orden, descripción)
AREAS_DEMO = [
    ('Caza', '🎯', 1, 'Técnicas de rastreo, emboscada y captura de presas.'),
    ('Sigilo', '🥷', 2, 'Moverse sin ser detectado: camuflaje y silencio.'),
    ('Ronroneo', '🎵', 3, 'Comunicación felina, lenguaje corporal y vocalizaciones.'),
    ('Trepar', '🧗', 4, 'Ascenso, equilibrio en alturas y aterrizajes seguros.'),
    ('Historia Felina', '📜', 5, 'Los caracales en la historia y la cultura.'),
]

# Cursos de demostración:
# (código, nombre, área, modalidad, precio, cupos, destacado, días_hasta_inicio)
CURSOS_DEMO = [
    ('FLF-001', 'Caza Nocturna Avanzada', 'Caza', 'PRESENCIAL', 149990, 30, True, 15),
    ('FLF-002', 'Sigilo Urbano para Principiantes', 'Sigilo', 'VIRTUAL', 79990, 60, True, 7),
    ('FLF-003', 'Ronroneo Terapéutico Nivel 1', 'Ronroneo', 'VIRTUAL', 49990, 80, False, 3),
    ('FLF-004', 'Bootcamp Caracal Elite (12 semanas)', 'Caza', 'HIBRIDO', 499990, 20, True, 30),
    ('FLF-005', 'Trepar y Salto de Precisión', 'Trepar', 'PRESENCIAL', 99990, 25, False, 21),
    ('FLF-006', 'Comunicación con Maullidos y Colas', 'Ronroneo', 'VIRTUAL', 59990, 100, False, 10),
    ('FLF-007', 'Emboscada en Terreno Rocoso', 'Caza', 'PRESENCIAL', 129990, 0, False, 45),
    ('FLF-008', 'Historia de los Caracales del Desierto', 'Historia Felina', 'VIRTUAL', 39990, 50, False, 5),
]

# Estudiantes de prueba: (username, email, first_name, last_name)
# Nota: estudiante1 lleva el nombre del profesor de la asignatura
# (Prof. Marcelo Patricio Alvarado Aravena) para que la demostración del
# perfil "Mi Perfil" muestre un nombre real en vez de un placeholder.
# Como Usuario.objects.get_or_create() sólo aplica `defaults` al CREAR, si se
# cambia un valor aquí conviene regenerar la cuenta o actualizar la fila.
ESTUDIANTES_DEMO = [
    ('estudiante1', 'marcelo.alvarado@floppa.cl', 'Marcelo Patricio', 'Alvarado Aravena'),
    ('estudiante2', 'nahuel@floppa.cl', 'Nahuel', 'Quintriqueo'),
    ('estudiante3', 'sara@floppa.cl', 'Sara', 'Fuenzalida'),
    ('estudiante4', 'diego@floppa.cl', 'Diego', 'Mallén'),
]


class Command(BaseCommand):
    """Puebla la base de datos con datos de demostración del proyecto."""

    help = 'Carga áreas, cursos, estudiantes y estadísticas de demostración.'

    def handle(self, *args, **options):
        now = timezone.now()

        # ------------------------------------------------------------------
        # 1. ÁREAS DE CONOCIMIENTO
        # ------------------------------------------------------------------
        for nombre, icono, orden, descripcion in AREAS_DEMO:
            AreaConocimiento.objects.get_or_create(
                slug=slugify(nombre),
                defaults={
                    'nombre': nombre,
                    'icono': icono,
                    'orden': orden,
                    'descripcion': descripcion,
                    'activa': True,
                },
            )

        coordinador = Usuario.objects.filter(
            rol=Usuario.Rol.COORDINADOR, is_superuser=False
        ).first() or Usuario.objects.filter(rol=Usuario.Rol.COORDINADOR).first()

        # ------------------------------------------------------------------
        # 2. CURSOS PUBLICADOS CON CUPOS Y FECHAS
        # ------------------------------------------------------------------
        for codigo, nombre, area_nombre, modalidad, precio, cupos, destacado, dias in CURSOS_DEMO:
            area = AreaConocimiento.objects.get(nombre=area_nombre)
            inicio = now + timedelta(days=dias)
            defaults = {
                'nombre': nombre,
                'slug': slugify(codigo + '-' + nombre),
                'area': area,
                'coordinador': coordinador,
                'descripcion': (
                    f'{nombre}. Programa completo de la academia, diseñado por instructores '
                    f'legendarios con metodología 100% práctica. Incluye material de estudio, '
                    f'evaluación y certificado verificable por UUID.'
                ),
                'resumen': f'Aprende {nombre.lower()} con la metodología probada de Floppa.',
                'estado': Curso.Estado.PUBLICADO,
                'modalidad': modalidad,
                'fecha_inicio': inicio,
                'fecha_fin': inicio + timedelta(days=60),
                'fecha_limite_inscripcion': inicio - timedelta(days=1),
                'cupos_maximos': cupos,
                'precio': precio,
                'destacado': destacado,
                'activo': True,
            }
            curso, created = Curso.objects.get_or_create(
                codigo=codigo,
                defaults=defaults,
            )
            if not created:
                # Si ya existe pero está en 0 cupos y tenía cupos configurados, lo respeta:
                # así se conserva el ejemplo de curso AGOTADO.
                continue
            # get_or_create sincroniza cupos_disponibles en save(); si se pedía 0
            # cupos (curso agotado) lo dejamos en 0 de forma explícita.
            if cupos == 0:
                Curso.objects.filter(pk=curso.pk).update(cupos_disponibles=0)

        # ------------------------------------------------------------------
        # 3. ESTUDIANTES DE PRUEBA (generan el conteo de estadísticas)
        # ------------------------------------------------------------------
        # IMPORTANTE: get_or_create no encripta claves por sí solo, así que
        # después de crear (o si la cuenta quedó sin clave utilizable) se
        # asigna la clave demo con set_password(), que aplica el hash de
        # Django (PBKDF2). Si la cuenta ya tenía clave propia no se toca.
        CLAVE_DEMO = 'floppa123'
        for username, email, first_name, last_name in ESTUDIANTES_DEMO:
            usuario, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'rol': Usuario.Rol.ESTUDIANTE,
                    'is_active': True,
                },
            )
            if creado or not _clave_definida(usuario):
                usuario.set_password(CLAVE_DEMO)
                usuario.save(update_fields=['password'])

        # ------------------------------------------------------------------
        # 4. RESUMEN
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS('Base de datos poblada correctamente.'))
        self.stdout.write(f'  Áreas:     {AreaConocimiento.objects.count()}')
        self.stdout.write(f'  Cursos:    {Curso.objects.count()}')
        self.stdout.write(f'  Estudiantes: {Usuario.objects.filter(rol=Usuario.Rol.ESTUDIANTE).count()}')
        self.stdout.write(self.style.WARNING(
            'Clave de los estudiantes de prueba: floppa123 (cámbialos antes de publicar).'
        ))
