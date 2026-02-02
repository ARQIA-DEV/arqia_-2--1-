import os
import logging
import base64
import tempfile
import time
from celery import shared_task
from openai import OpenAI
from django.contrib.auth.models import User
from .models import Documento, LogDeSistema
from .utils import analisar_com_gpt, analisar_documento_por_imagem
from .prompts import PROMPT_MAP

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@shared_task
def analisar_documento_task(documento_id, arquivo_base64, extensao, categoria_nome, prompt, user_id):
    started_at = time.perf_counter()
    user = None
    try:
        user = User.objects.get(pk=user_id)
        documento = Documento.objects.get(pk=documento_id)
        prompt = PROMPT_MAP.get(categoria_nome, PROMPT_MAP["outros"])

        logger.info(
            (
                "celery_task_started task=analisar_documento documento_id=%s "
                "user_id=%s categoria=%s extensao=%s"
            ),
            documento_id,
            user_id,
            categoria_nome,
            extensao,
        )

        if extensao == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(base64.b64decode(arquivo_base64))
                caminho = tmp.name
            resultado = analisar_documento_por_imagem(caminho, prompt)
            texto_extraido = resultado  # Neste caso, a imagem já está sendo usada como fonte primária
        else:
            texto_extraido = base64.b64decode(arquivo_base64).decode('utf-8', errors='ignore')
            resultado = analisar_com_gpt(texto_extraido, prompt)

        if not resultado or resultado.startswith("Erro ao analisar"):
            raise ValueError("Falha na análise com GPT")

        documento.texto_extraido = texto_extraido
        documento.resultado_analise = resultado
        documento.save()

        LogDeSistema.objects.create(
            acao="Análise finalizada",
            mensagem="Análise concluída com sucesso.",
            documento=documento,
            usuario=user
        )

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "celery_task_succeeded task=analisar_documento documento_id=%s duration_ms=%s",
            documento_id,
            elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "celery_task_failed task=analisar_documento documento_id=%s duration_ms=%s",
            documento_id,
            elapsed_ms,
        )
        documento = Documento.objects.filter(pk=documento_id).first()
        if documento:
            documento.resultado_analise = "Erro ao processar o documento automaticamente. A equipe será notificada."
            documento.save()
            LogDeSistema.objects.create(
                acao="Erro na análise",
                mensagem=str(e)[:500],
                documento=documento,
                usuario=user if user else None
            )
