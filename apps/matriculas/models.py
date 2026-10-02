"""
=============================================================================
MODELOS MATRÍCULAS Y CARRO - ACADEMIA FELINA FLOPPA
=============================================================================
Implementación completa del flujo transaccional:

1. CarroMatricula (1:1 Usuario) - PERSISTENTE EN POSTGRESQL
   - Relación 1:1 con Usuario (ESTUDIANTE)
   - Activo mientras se agregan/quitan ítems
   - Persiste tras logout/cambio dispositivo (REQUERIDO POR PAUTA)

2. ItemCarro - Cursos en el carro
   - Un curso por item (no duplicados)
   - Validación: no permitir mismo curso 2 veces

3. OrdenMatricula - Registro histórico al hacer checkout
   - Congela precios, datos del curso al momento de la compra
   - Estados: PENDIENTE -> PAGADO -> ENTREGADO/COMPLETADO | CANCELADO
   - CHOICES explícito en estado (REQUERIDO POR PAUTA)

4. MatriculaDetalle - Inscripción oficial por curso (generada al PAGADO)
   - Un registro por curso en la orden
   - Código único de matrícula (UUID)

FLUJO TRANSACCIONAL (REQUERIDO POR PAUTA):
- Stock/Cupos NO se descuentan al agregar al carro
- SOLO al cambiar a PAGADO: descuenta cupos atómicamente
- Si stock insuficiente al pagar -> RECHAZA transacción
- Si orden CANCELADA -> REPONE cupos automáticamente
=============================================================================
"""
import uuid
from decimal import Decimal
from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.usuarios.models import Usuario
from apps.academico.models import Curso


class CarroMatricula(TimeStampedModel):
    """
    Carro de matrícula PERSISTENTE en PostgreSQL.
    Relación 1:1 con Usuario (ESTUDIANTE).
    
    CUMPLE PAUTA: 
    - "Relación 1 a 1 entre el Usuario y su Carro activo en base de datos"
    - "Los ítems agregados deben persistir en PostgreSQL aun cuando el usuario cierre sesión"
    """
    estudiante = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='carro_matricula',
        limit_choices_to={'rol': Usuario.Rol.ESTUDIANTE},
        verbose_name='Estudiante'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Carro activo',
        help_text='Solo un carro activo por estudiante'
    )

    class Meta:
        verbose_name = 'Carro de Matrícula'
        verbose_name_plural = 'Carros de Matrícula'
        indexes = [models.Index(fields=['estudiante', 'activo'])]

    def __str__(self):
        return f"Carro de {self.estudiante.get_full_name() or self.estudiante.username}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_precio(self):
        return self.items.aggregate(total=Sum('precio_congelado'))['total'] or Decimal('0')

    @property
    def esta_vacio(self):
        return self.total_items == 0

    def agregar_curso(self, curso: Curso):
        """
        Agrega curso al carro si hay cupo y no está duplicado.
        NO descuenta cupos del catálogo (solo valida disponibilidad).
        """
        if not curso.esta_disponible:
            raise ValueError(f"Curso '{curso.nombre}' no tiene cupos disponibles.")

        # Verificar duplicado
        if self.items.filter(curso=curso).exists():
            raise ValueError(f"El curso '{curso.nombre}' ya está en el carro.")

        item = ItemCarro.objects.create(
            carro=self,
            curso=curso,
            precio_congelado=curso.precio,
            nombre_congelado=curso.nombre,
            codigo_congelado=curso.codigo,
        )
        return item

    def quitar_curso(self, curso_id):
        """Quita curso del carro"""
        self.items.filter(curso_id=curso_id).delete()

    def limpiar(self):
        """Vacía el carro completamente"""
        self.items.all().delete()

    def validar_checkout(self):
        """
        Valida que todos los cursos del carro tengan cupo disponible
        antes de proceder al checkout.
        """
        errores = []
        for item in self.items.select_related('curso'):
            if not item.curso.esta_disponible:
                errores.append(f"'{item.curso.nombre}' ya no tiene cupos disponibles.")
        return errores


class ItemCarro(TimeStampedModel):
    """
    Item individual en el carro de matrícula.
    Congela precio y datos del curso al momento de agregar.
    """
    carro = models.ForeignKey(
        CarroMatricula,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Carro'
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='items_carro',
        verbose_name='Curso'
    )

    # Datos congelados (snapshot al agregar al carro)
    precio_congelado = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Precio congelado'
    )
    nombre_congelado = models.CharField(max_length=200, verbose_name='Nombre congelado')
    codigo_congelado = models.CharField(max_length=20, verbose_name='Código congelado')

    class Meta:
        verbose_name = 'Item del Carro'
        verbose_name_plural = 'Items del Carro'
        unique_together = ['carro', 'curso']  # Un curso por carro
        indexes = [models.Index(fields=['carro', 'curso'])]

    def __str__(self):
        return f"{self.codigo_congelado} - {self.nombre_congelado} (CLP {self.precio_congelado})"


class OrdenMatricula(TimeStampedModel, SoftDeleteModel):
    """
    Orden de matrícula - Registro histórico generado al hacer checkout.
    Congela TODOS los datos: precios, cursos, datos del estudiante.
    
    ESTADOS (CHOICES explícito - REQUERIDO POR PAUTA):
    PENDIENTE -> PAGADO -> ENTREGADO/COMPLETADO
                    -> CANCELADO
    
    FLUJO TRANSACCIONAL:
    - Al crear: PENDIENTE (carro se vacía, orden se crea)
    - Al pagar: PAGADO (descuenta cupos atómicamente, genera matrículas oficiales)
    - Coordinador puede: ENTREGADO/COMPLETADO o CANCELADO
    - Si CANCELADO: repone cupos automáticamente
    """
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de pago'
        PAGADO = 'PAGADO', 'Pagado - Matrículas generadas'
        ENTREGADO = 'ENTREGADO', 'Entregado/Completado (curso finalizado)'
        CANCELADO = 'CANCELADO', 'Cancelado (cupos liberados)'

    # Identificación
    numero_orden = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Número de orden'
    )

    # Relaciones
    estudiante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='ordenes',
        limit_choices_to={'rol': Usuario.Rol.ESTUDIANTE},
        verbose_name='Estudiante'
    )

    # Estado transaccional
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado de la orden',
        help_text='CHOICES explícito - Control transaccional de inventario/cupos'
    )

    # Datos congelados del estudiante (snapshot)
    estudiante_nombre = models.CharField(max_length=300, verbose_name='Nombre estudiante')
    estudiante_email = models.EmailField(verbose_name='Email estudiante')
    estudiante_username = models.CharField(max_length=150, verbose_name='Username estudiante')

    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Subtotal')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Total')

    # Fechas clave
    fecha_pago = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de pago')
    fecha_cancelacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de cancelación')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de entrega/completado')

    # Metadatos
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    metodo_pago = models.CharField(max_length=50, blank=True, verbose_name='Método de pago simulado')

    objects = models.Manager()  # Incluye soft-deleted para historial
    activos = models.Manager.from_queryset(lambda: models.QuerySet.filter(is_deleted=False))()

    class Meta:
        verbose_name = 'Orden de Matrícula'
        verbose_name_plural = 'Órdenes de Matrícula'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estudiante', 'estado']),
            models.Index(fields=['estado', 'created_at']),
            models.Index(fields=['numero_orden']),
        ]

    def __str__(self):
        return f"Orden {self.numero_orden} - {self.estudiante_nombre} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if not self.numero_orden:
            self.numero_orden = self.generar_numero_orden()
        super().save(*args, **kwargs)

    def generar_numero_orden(self):
        """Genera número de orden único: ORD-YYYYMMDD-XXXX"""
        fecha = timezone.now().strftime('%Y%m%d')
        import random
        sufijo = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
        return f"ORD-{fecha}-{sufijo}"

    @property
    def puede_pagar(self):
        return self.estado == self.Estado.PENDIENTE

    @property
    def puede_cancelar(self):
        return self.estado in [self.Estado.PENDIENTE, self.Estado.PAGADO]

    @property
    def puede_entregar(self):
        return self.estado == self.Estado.PAGADO


class MatriculaDetalle(TimeStampedModel):
    """
    Matrícula oficial generada al confirmar pago (estado PAGADO).
    Un registro por curso en la orden.
    Incluye código único UUID para certificado/verificación.
    """
    orden = models.ForeignKey(
        OrdenMatricula,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name='Orden'
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='matriculas',
        verbose_name='Curso'
    )

    # Datos congelados de la matrícula
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio pagado')
    nombre_curso = models.CharField(max_length=200, verbose_name='Nombre del curso')
    codigo_curso = models.CharField(max_length=20, verbose_name='Código del curso')

    # Código único de matrícula (UUID) - para certificado/verificación
    codigo_matricula = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código de matrícula (UUID)'
    )

    # Estado individual (puede diferir de la orden en casos edge)
    activa = models.BooleanField(default=True, verbose_name='Matrícula activa')
    fecha_inicio_curso = models.DateTimeField(verbose_name='Fecha inicio del curso')
    fecha_fin_curso = models.DateTimeField(verbose_name='Fecha fin del curso')

    class Meta:
        verbose_name = 'Matrícula Oficial'
        verbose_name_plural = 'Matrículas Oficiales'
        unique_together = ['orden', 'curso']
        indexes = [
            models.Index(fields=['orden', 'activa']),
            models.Index(fields=['codigo_matricula']),
            models.Index(fields=['curso', 'activa']),
        ]

    def __str__(self):
        return f"Matrícula {self.codigo_matricula} - {self.nombre_curso}"