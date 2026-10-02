"""
=============================================================================
VISTAS MATRÍCULAS - ACADEMIA FELINA FLOPPA
=============================================================================
ViewSets para:
- CarroMatricula (persistente, 1:1 estudiante) - GET, POST agregar, DELETE quitar
- Checkout (carro -> orden PENDIENTE)
- OrdenMatricula (historial, pagar, cancelar - coordinador cambia estados)
=============================================================================
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.matriculas.models import CarroMatricula, ItemCarro, OrdenMatricula
from apps.matriculas.serializers import (
    CarroMatriculaSerializer, ItemCarroSerializer, AgregarAlCarroSerializer,
    OrdenMatriculaListSerializer, OrdenMatriculaDetailSerializer,
    CheckoutSerializer, PagarOrdenSerializer, CambioEstadoOrdenSerializer,
    MatriculaDetalleSerializer
)
from apps.matriculas.services import crear_orden_desde_carro, procesar_pago_orden
from apps.core.permissions import IsEstudiante, IsCoordinador, IsOwnerOrCoordinador
from apps.academico.models import Curso


class CarroMatriculaViewSet(viewsets.GenericViewSet):
    """
    ViewSet para Carro de Matrícula PERSISTENTE (1:1 Usuario).
    
    Endpoints:
    - GET /api/carro/           -> Ver carro actual (items, totales)
    - POST /api/carro/agregar/  -> Agregar curso al carro
    - DELETE /api/carro/quitar/{curso_id}/ -> Quitar curso del carro
    - DELETE /api/carro/limpiar/ -> Vaciar carro completo
    - POST /api/carro/checkout/ -> Procesar checkout (crea orden PENDIENTE)
    
    Permisos: Solo ESTUDIANTE autenticado.
    CUMPLE PAUTA: "Persistencia del Carro post-logout en PostgreSQL"
    """
    permission_classes = [IsEstudiante]
    serializer_class = CarroMatriculaSerializer

    def get_object(self):
        """Obtiene o crea carro del estudiante actual"""
        carro, _ = CarroMatricula.objects.get_or_create(
            estudiante=self.request.user,
            activo=True
        )
        return carro

    def retrieve(self, request, *args, **kwargs):
        """GET /api/carro/ - Ver carro con items y totales"""
        carro = self.get_object()
        serializer = self.get_serializer(carro)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='agregar')
    def agregar(self, request):
        """POST /api/carro/agregar/ - Agregar curso al carro"""
        serializer = AgregarAlCarroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        carro = self.get_object()
        curso_id = serializer.validated_data['curso_id']
        curso = get_object_or_404(Curso, id=curso_id, activo=True, is_deleted=False, estado=Curso.Estado.PUBLICADO)
        
        try:
            item = carro.agregar_curso(curso)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        item_serializer = ItemCarroSerializer(item, context={'request': request})
        return Response(item_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path='quitar/(?P<curso_id>[^/.]+)')
    def quitar(self, request, curso_id=None):
        """DELETE /api/carro/quitar/{curso_id}/ - Quitar curso del carro"""
        carro = self.get_object()
        carro.quitar_curso(curso_id)
        return Response({'detail': 'Curso quitado del carro.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='limpiar')
    def limpiar(self, request):
        """DELETE /api/carro/limpiar/ - Vaciar carro completo"""
        carro = self.get_object()
        carro.limpiar()
        return Response({'detail': 'Carro vaciado.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """POST /api/carro/checkout/ - Crear orden PENDIENTE desde carro"""
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            orden = crear_orden_desde_carro(
                carro=serializer.validated_data['carro'],
                metodo_pago=serializer.validated_data.get('metodo_pago', 'simulado'),
                observaciones=serializer.validated_data.get('observaciones', '')
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        orden_serializer = OrdenMatriculaDetailSerializer(orden, context={'request': request})
        return Response(orden_serializer.data, status=status.HTTP_201_CREATED)


class OrdenMatriculaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Órdenes de Matrícula (Historial del estudiante).
    
    Endpoints:
    - GET /api/matriculas/              -> Listar mis órdenes
    - GET /api/matriculas/{id}/         -> Detalle de orden
    - POST /api/matriculas/{id}/pagar/  -> Pagar orden (PENDIENTE -> PAGADO)
    - POST /api/matriculas/{id}/cancelar/ -> Cancelar orden (estudiante)
    
    Permisos: ESTUDIANTE ve solo sus órdenes (IsOwnerOrCoordinador)
    """
    permission_classes = [IsEstudiante, IsOwnerOrCoordinador]
    
    def get_queryset(self):
        return OrdenMatricula.objects.filter(estudiante=self.request.user).prefetch_related('matriculas__curso')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrdenMatriculaDetailSerializer
        return OrdenMatriculaListSerializer

    @action(detail=True, methods=['post'], url_path='pagar')
    def pagar(self, request, pk=None):
        """POST /api/matriculas/{id}/pagar/ - Confirmar pago (PENDIENTE -> PAGADO)"""
        orden = self.get_object()
        
        if not orden.puede_pagar:
            return Response(
                {'detail': f'Orden en estado {orden.get_estado_display()}, no se puede pagar.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PagarOrdenSerializer(data=request.data, context={'request': request, 'orden': orden})
        serializer.is_valid(raise_exception=True)
        
        try:
            orden = procesar_pago_orden(orden, serializer.validated_data.get('metodo_pago', 'simulado'))
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        orden_serializer = OrdenMatriculaDetailSerializer(orden, context={'request': request})
        return Response(orden_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """POST /api/matriculas/{id}/cancelar/ - Cancelar orden (estudiante)"""
        orden = self.get_object()
        
        if not orden.puede_cancelar:
            return Response(
                {'detail': f'Orden en estado {orden.get_estado_display()}, no se puede cancelar.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si estaba PAGADO, liberar cupos
        if orden.estado == OrdenMatricula.Estado.PAGADO:
            from apps.matriculas.services import liberar_cupos_orden
            liberar_cupos_orden(orden)

        orden.estado = OrdenMatricula.Estado.CANCELADO
        orden.fecha_cancelacion = timezone.now()
        orden.save(update_fields=['estado', 'fecha_cancelacion', 'updated_at'])
        
        return Response({'detail': 'Orden cancelada correctamente.'}, status=status.HTTP_200_OK)


class OrdenMatriculaCoordinadorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de órdenes por COORDINADOR.
    
    Endpoints:
    - GET /api/matriculas/gestion/           -> Listar todas las órdenes (filtros)
    - GET /api/matriculas/gestion/{id}/      -> Detalle orden
    - PATCH /api/matriculas/gestion/{id}/estado/ -> Cambiar estado (PAGADO->ENTREGADO|CANCELADO)
    
    Permisos: Solo COORDINADOR
    """
    permission_classes = [IsCoordinador]
    serializer_class = OrdenMatriculaDetailSerializer
    filter_backends = []  # Se pueden añadir filtros si se necesita
    
    def get_queryset(self):
        return OrdenMatricula.objects.all().prefetch_related('matriculas__curso').select_related('estudiante')

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return CambioEstadoOrdenSerializer
        return OrdenMatriculaDetailSerializer

    @action(detail=True, methods=['patch'], url_path='estado')
    def cambiar_estado(self, request, pk=None):
        """PATCH /api/matriculas/gestion/{id}/estado/ - Cambiar estado de orden"""
        orden = self.get_object()
        serializer = CambioEstadoOrdenSerializer(orden, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        orden = serializer.save()
        
        response_serializer = OrdenMatriculaDetailSerializer(orden, context={'request': request})
        return Response(response_serializer.data)


# Import timezone for views
from django.utils import timezone