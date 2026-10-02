"""
=============================================================================
VISTAS BASE - ACADEMIA FELINA FLOPPA
=============================================================================
Vistas HTML base (Home, Health Check, Catálogo, Carro, Matrículas, Coordinador)
con template liquid glass. Incluyen footer con datos del alumno (requerido por pauta).
=============================================================================
"""
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.academico.models import Curso, AreaConocimiento
from apps.usuarios.models import Usuario


class HomeView(TemplateView):
    """
    Vista principal (index.html) - Landing page con diseño Liquid Glass.
    Muestra catálogo público de cursos, navegación, footer con datos alumno.
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cursos destacados (PUBLICADO, activo, con cupos, ordenados por fecha)
        cursos_destacados = Curso.objects.filter(
            activo=True, 
            is_deleted=False, 
            estado=Curso.Estado.PUBLICADO,
            cupos_disponibles__gt=0,
            destacado=True
        ).select_related('area')[:6]
        
        # Si no hay destacados, tomar los primeros disponibles
        if not cursos_destacados:
            cursos_destacados = Curso.objects.filter(
                activo=True, 
                is_deleted=False, 
                estado=Curso.Estado.PUBLICADO,
                cupos_disponibles__gt=0
            ).select_related('area')[:6]
        
        # Estadísticas para home
        total_cursos = Curso.objects.filter(activo=True, is_deleted=False, estado=Curso.Estado.PUBLICADO).count()
        total_areas = AreaConocimiento.objects.filter(activa=True, is_deleted=False).count()
        total_estudiantes = Usuario.objects.filter(rol=Usuario.Rol.ESTUDIANTE, is_active=True).count()
        
        stats = {
            'total_cursos': total_cursos,
            'total_areas': total_areas,
            'total_estudiantes': total_estudiantes,
        }
        
        # Stats para display con animación.
        # 'icono_img' apunta a static/assets/iconos/... : si el archivo existe
        # se muestra la imagen que suba el usuario; si no, el emoji 'icon'.
        stats_display = [
            {
                'value': total_cursos,
                'label': 'Cursos Disponibles',
                'description': 'Diseñados por expertos caracales',
                'icon': '📚',
                'icono_img': 'assets/iconos/estadisticas/cursos.png',
            },
            {
                'value': total_areas,
                'label': 'Áreas de Conocimiento',
                'description': 'Caza, Sigilo, Ronroneo y más',
                'icon': '🎯',
                'icono_img': 'assets/iconos/estadisticas/areas.png',
            },
            {
                'value': total_estudiantes,
                'label': 'Estudiantes Inscritos',
                'description': 'Formando la próxima manada élite',
                'icon': '🐱',
                'icono_img': 'assets/iconos/estadisticas/estudiantes.png',
            },
        ]

        # Features para la sección de características (mismo criterio de iconos).
        # `dato` es el "dato curioso de caracales" que muestra la tarjeta al
        # hacer clic (ver `.fc-dato` / `activarFeature()` en home.html).
        features = [
            {
                'title': 'Instructores Legendarios',
                'description': 'Aprende de Floppa y los maestros del sigilo felino con décadas de experiencia.',
                'icon': '🏆',
                'icono_img': 'assets/iconos/caracteristicas/instructores.png',
                'dato': 'Los caracales saltan hasta 3 metros de altura y así alcanzan '
                        'a las aves en pleno vuelo, con un solo impulso de las patas traseras.',
            },
            {
                'title': 'Metodología Práctica',
                'description': 'Ejercicios reales de caza, sigilo y comunicación. No solo teoría, acción pura.',
                'icon': '⚔️',
                'icono_img': 'assets/iconos/caracteristicas/metodologia.png',
                'dato': 'Cazan de noche: su oído es tan fino que detecta a una presa '
                        'a más de 50 metros, incluso moviéndose sobre hojarasca.',
            },
            {
                'title': 'Certificación Oficial',
                'description': 'Recibe tu certificado UUID único verificable. Reconocido en todo el territorio felino.',
                'icon': '📜',
                'icono_img': 'assets/iconos/caracteristicas/certificacion.png',
                'dato': 'Su nombre viene del turco "karakulak", que significa literalmente '
                        '"oreja negra": las puntas de sus orejas son negras y con pincelada.',
            },
            {
                'title': 'Comunidad Activa',
                'description': 'Acceso a la manada privada. Comparte presas, tips y ruge con otros estudiantes.',
                'icon': '👥',
                'icono_img': 'assets/iconos/caracteristicas/comunidad.png',
                'dato': 'Tienen más de 20 vocalizaciones: ronronean, silban y maúllan '
                        'prácticamente igual que un gato de casa.',
            },
        ]
        
        context.update({
            'page_title': 'Academia Felina Floppa - Entrenamiento de élite para caracales',
            'page_description': 'Cursos y bootcamps especializados para caracales. Desarrolla tus habilidades de caza, sigilo y ronroneo.',
            'cursos_destacados': cursos_destacados,
            'stats': stats,
            'stats_display': stats_display,
            'features': features,
        })
        return context


class CatalogoView(TemplateView):
    """Vista del catálogo público de cursos con DataTables y filtros"""
    template_name = 'core/catalogo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        areas = AreaConocimiento.objects.filter(activa=True, is_deleted=False).order_by('orden', 'nombre')
        context.update({
            'page_title': 'Catálogo de Cursos',
            'areas': areas,
        })
        return context


class NuestraHistoriaView(TemplateView):
    """
    Página institucional "/nuestra-historia/".

    Es la subpágina a la que lleva la banda clicable del home ("Nuestra
    historia y nuestra lucha contra el plagio"). Muestra el manifiesto de
    origen de la academia y la denuncia de plagio, con la imagen entregada
    por el usuario. Es una vista pública de solo lectura.
    """
    template_name = 'core/nuestra_historia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Nuestra historia y la lucha contra el plagio',
            'page_description': (
                'Manifiesto de origen de la Academia Felina Floppa y denuncia '
                'pública del plagio de Ducommun Marcelo.'
            ),
        })
        return context


class MiCarroView(LoginRequiredMixin, TemplateView):
    """Vista del carro de matrícula persistente (solo estudiantes)"""
    template_name = 'core/mi_carro.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        """
        Control de acceso en dos etapas.

        IMPORTANTE: AnonymousUser NO tiene los atributos `es_estudiante` /
        `es_coordinador` (son propiedades del modelo Usuario). Si el chequeo de
        rol se ejecuta antes de pasar por LoginRequiredMixin, la vista revienta
        con AttributeError y Django devuelve un error 500. Por eso el orden es:
            1) autenticación  -> LoginRequiredMixin redirige a /login/
            2) rol            -> se evalúa solo si ya hay sesión
        """
        if request.user.is_authenticated and not request.user.es_estudiante:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class MisMatriculasView(LoginRequiredMixin, TemplateView):
    """Vista de mis matrículas/órdenes (solo estudiantes)"""
    template_name = 'core/mis_matriculas.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # Ver nota detallada en MiCarroView.dispatch: primero sesión, luego rol.
        if request.user.is_authenticated and not request.user.es_estudiante:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class CoordinadorDashboardView(LoginRequiredMixin, TemplateView):
    """Panel de coordinador para gestión de cursos, órdenes y áreas"""
    template_name = 'core/coordinador_dashboard.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # Ver nota detallada en MiCarroView.dispatch: primero sesión, luego rol.
        if request.user.is_authenticated and not request.user.es_coordinador:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class PerfilView(LoginRequiredMixin, TemplateView):
    """Perfil de usuario autenticado"""
    template_name = 'core/perfil.html'
    login_url = '/login/'


class HealthCheckView(TemplateView):
    """
    Health check endpoint para monitoreo / load balancers.
    Retorna JSON con estado de la DB y versión.
    """
    def get(self, request, *args, **kwargs):
        from django.db import connection
        from django.db.utils import OperationalError

        db_status = 'ok'
        try:
            connection.ensure_connection()
        except OperationalError:
            db_status = 'error'

        return JsonResponse({
            'status': 'healthy' if db_status == 'ok' else 'unhealthy',
            'database': db_status,
            'version': '1.0.0',
            'proyecto': 'Academia Felina Floppa - EVA 2 Backend',
        })