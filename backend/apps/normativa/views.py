"""HTTP do componente. A regra de negócio fica em services e interface.

Escrita: só quem tem a permissão do configurador.
Leitura da apuração e da coleta: qualquer usuário autenticado do sistema.
O componente chamador continua responsável pela permissão do caso de uso dele
(homologar resultado, registrar resultado) quando chama a interface direto.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.acesso.interface import ExigePermissao

from . import services
from .interface import CompetenciaNaoCadastrada, indicadores_para_coleta, regras_para_apuracao
from .models import Competencia, Indicador, Normativa, RegraCalculo
from .serializers import (
    CompetenciaSerializer,
    IndicadorSerializer,
    NormativaSerializer,
    RegraCalculoSerializer,
)
from .services import PERMISSAO_INDICADOR, PERMISSAO_REGRA


def _erro(exc):
    if hasattr(exc, "error_dict"):
        detalhe = {campo: [str(item) for item in erros] for campo, erros in exc.error_dict.items()}
    else:
        detalhe = {"erros": [str(item) for item in exc.error_list]}
    return Response(detalhe, status=status.HTTP_400_BAD_REQUEST)


class Normativas(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [ExigePermissao()]
        return [IsAuthenticated()]

    permissoes_exigidas = (PERMISSAO_INDICADOR,)

    def get(self, request):
        return Response(NormativaSerializer(Normativa.objects.all(), many=True).data)

    def post(self, request):
        try:
            normativa = services.cadastrar_normativa(request.user, request.data)
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(NormativaSerializer(normativa).data, status=status.HTTP_201_CREATED)


class Competencias(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [ExigePermissao()]
        return [IsAuthenticated()]

    permissoes_exigidas = (PERMISSAO_INDICADOR,)

    def get(self, request):
        return Response(CompetenciaSerializer(Competencia.objects.select_related("normativa"), many=True).data)

    def post(self, request):
        try:
            competencia = services.cadastrar_competencia(request.user, request.data)
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(CompetenciaSerializer(competencia).data, status=status.HTTP_201_CREATED)


class Indicadores(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [ExigePermissao()]
        return [IsAuthenticated()]

    permissoes_exigidas = (PERMISSAO_INDICADOR,)

    def get(self, request):
        consulta = Indicador.objects.select_related("normativa", "pai")
        normativa = request.query_params.get("normativa")
        if normativa:
            consulta = consulta.filter(normativa_id=normativa)
        return Response(IndicadorSerializer(consulta, many=True).data)

    def post(self, request):
        try:
            indicador = services.cadastrar_indicador(request.user, request.data)
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(IndicadorSerializer(indicador).data, status=status.HTTP_201_CREATED)


class IndicadorDetalhe(APIView):
    permission_classes = [ExigePermissao]
    permissoes_exigidas = (PERMISSAO_INDICADOR,)

    def put(self, request, pk):
        try:
            indicador = services.atualizar_indicador(request.user, pk, request.data)
        except Indicador.DoesNotExist:
            return Response({"detail": "Indicador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(IndicadorSerializer(indicador).data)


class ImportarIndicadores(APIView):
    permission_classes = [ExigePermissao]
    permissoes_exigidas = (PERMISSAO_INDICADOR, PERMISSAO_REGRA)

    def post(self, request):
        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            return Response({"arquivo": ["Envie o arquivo no campo arquivo."]}, status=status.HTTP_400_BAD_REQUEST)
        if arquivo.size > 1_000_000:
            return Response(
                {"arquivo": ["O arquivo passa de 1 MB. Divida a importação."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            conteudo = arquivo.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"arquivo": ["Envie um CSV em UTF-8. No Excel, salve como CSV UTF-8."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            indicadores = services.importar_indicadores(
                request.user,
                request.data.get("normativa") or request.data.get("normativa_id"),
                conteudo,
            )
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "quantidade": len(indicadores),
                "codigos": [item.codigo for item in indicadores],
            },
            status=status.HTTP_201_CREATED,
        )


class Regras(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [ExigePermissao()]
        return [IsAuthenticated()]

    permissoes_exigidas = (PERMISSAO_REGRA,)

    def get(self, request):
        consulta = RegraCalculo.objects.select_related("indicador")
        indicador = request.query_params.get("indicador")
        if indicador:
            consulta = consulta.filter(indicador_id=indicador)
        return Response(RegraCalculoSerializer(consulta, many=True).data)

    def post(self, request):
        try:
            regra = services.configurar_regra(request.user, request.data)
        except ValidationError as exc:
            return _erro(exc)
        except PermissionDenied:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(RegraCalculoSerializer(regra).data, status=status.HTTP_201_CREATED)


class RegrasParaApuracao(APIView):
    """Leitura da apuração. Não exige a permissão de configurar regra."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            ano, mes = _ano_mes(request)
            regras = regras_para_apuracao(
                ano=ano,
                mes=mes,
                cargo=request.query_params.get("cargo", ""),
                tipo_unidade=request.query_params.get("tipo_unidade", ""),
            )
        except CompetenciaNaoCadastrada as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return _erro(exc)
        return Response([regra.para_dict() for regra in regras])


class IndicadoresParaColeta(APIView):
    """Leitura da coleta. Não exige a permissão de cadastrar indicador."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            ano, mes = _ano_mes(request)
            indicadores = indicadores_para_coleta(
                ano=ano,
                mes=mes,
                cargo=request.query_params.get("cargo", ""),
                tipo_unidade=request.query_params.get("tipo_unidade", ""),
            )
        except CompetenciaNaoCadastrada as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return _erro(exc)
        return Response([item.para_dict() for item in indicadores])


def _ano_mes(request):
    ano = request.query_params.get("ano")
    mes = request.query_params.get("mes")
    if not ano or not mes:
        raise ValidationError({"competencia": "Informe ano e mes."})
    try:
        return int(ano), int(mes)
    except ValueError:
        raise ValidationError({"competencia": "Ano e mês precisam ser números."}) from None
