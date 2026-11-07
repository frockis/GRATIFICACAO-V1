from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from sggd.permissoes import perfil_da_requisicao, usuario_da_requisicao

from . import services
from .models import Avaliado, Distrito, Unidade
from .serializers import DistritoSerializer, UnidadeSerializer, UsuarioSerializer

# Erro do modelo → campo do front
CAMPO_FRONT = {"distrito": "distritoId", "unidade": "unidadeId", "perfil": "perfilId", "__all__": "detail"}


def _autor(request) -> services.Autor:
    return services.Autor(nome=usuario_da_requisicao(request), perfil=perfil_da_requisicao(request) or "")


def _erro(e: ValidationError) -> Response:
    if hasattr(e, "error_dict"):
        corpo = {CAMPO_FRONT.get(k, k): v for k, v in e.message_dict.items()}
    else:
        corpo = {"detail": e.messages}
    return Response(corpo, status=status.HTTP_400_BAD_REQUEST)


class CadastroViewSet(viewsets.ViewSet):
    """Base: listar, detalhar, criar (POST), alterar (PATCH) e inativar. Não existe DELETE."""

    modelo = None
    serializer = None
    filtros: dict = {}

    def preencher(self, obj, dados):
        raise NotImplementedError

    def get_queryset(self):
        qs = self.modelo.objects.all()
        for parametro, campo in self.filtros.items():
            if valor := self.request.query_params.get(parametro):
                qs = qs.filter(**{campo: valor})
        return qs

    def _obter(self, pk):
        try:
            return self.modelo.objects.get(pk=pk)
        except self.modelo.DoesNotExist:
            return None

    def list(self, request):
        return Response(self.serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        obj = self._obter(pk)
        if obj is None:
            return Response({"detail": "Não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer(obj).data)

    def _gravar(self, obj, dados, criado: bool):
        if not isinstance(dados, dict):
            return Response({"detail": "Envie um objeto JSON."}, status=status.HTTP_400_BAD_REQUEST)
        # status só muda pelas ações inativar/reativar (que têm regra própria)
        self.preencher(obj, dados)
        try:
            services.salvar(obj, _autor(self.request))
        except ValidationError as e:
            return _erro(e)
        return Response(self.serializer(obj).data, status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)

    def _mudar_status(self, pk, funcao):
        obj = self._obter(pk)
        if obj is None:
            return Response({"detail": "Não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        try:
            funcao(obj, _autor(self.request))
        except ValidationError as e:
            return _erro(e)
        return Response(self.serializer(obj).data)

    def create(self, request):
        return self._gravar(self.modelo(), request.data, criado=True)

    def partial_update(self, request, pk=None):
        obj = self._obter(pk)
        if obj is None:
            return Response({"detail": "Não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return self._gravar(obj, request.data, criado=False)


class DistritoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Distrito.objects.all()
    serializer_class = DistritoSerializer


class UnidadeViewSet(CadastroViewSet):
    """/api/unidades/?distritoId=d1&tipo=USF&status=Ativo"""

    modelo = Unidade
    serializer = UnidadeSerializer
    filtros = {"distritoId": "distrito_id", "tipo": "tipo", "status": "status"}

    def preencher(self, obj, dados):
        services.preencher_unidade(obj, dados, incluir_status=False)

    @action(detail=True, methods=["post"])
    def inativar(self, request, pk=None):
        return self._mudar_status(pk, services.inativar_unidade)

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        return self._mudar_status(pk, services.reativar)

    @action(detail=True, methods=["get"])
    def vinculos(self, request, pk=None):
        """Pessoas avaliadas vinculadas à unidade (para Apuração e Homologação)."""
        return Response(services.vinculos_unidade_pessoa(unidade_id=pk))


class UsuarioViewSet(CadastroViewSet):
    """/api/usuarios/?perfilId=gestor&status=Ativo&distritoId=d1&unidadeId=u1"""

    modelo = Avaliado
    serializer = UsuarioSerializer
    filtros = {"perfilId": "perfil", "status": "status", "distritoId": "distrito_id", "unidadeId": "unidade_id"}

    def preencher(self, obj, dados):
        services.preencher_usuario(obj, dados, incluir_status=False)

    def get_queryset(self):
        return super().get_queryset().select_related("unidade")

    @action(detail=True, methods=["post"])
    def inativar(self, request, pk=None):
        return self._mudar_status(pk, services.inativar_avaliado)

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        return self._mudar_status(pk, services.reativar)


@api_view(["GET"])
def vinculos(request):
    """GET /api/vinculos/?unidadeId=&distritoId= — vínculo unidade-pessoa dos avaliados ativos."""
    return Response(
        services.vinculos_unidade_pessoa(
            unidade_id=request.query_params.get("unidadeId"),
            distrito_id=request.query_params.get("distritoId"),
        )
    )


@api_view(["POST"])
def importar(request):
    """POST /api/cadastro/importar/ — {"distritos": [], "unidades": [], "usuarios": []} (tudo ou nada)."""
    try:
        resumo = services.importar(request.data, _autor(request))
    except services.ImportacaoInvalida as e:
        return Response({"detail": str(e), "erros": e.erros}, status=status.HTTP_400_BAD_REQUEST)
    return Response(resumo, status=status.HTTP_201_CREATED)
