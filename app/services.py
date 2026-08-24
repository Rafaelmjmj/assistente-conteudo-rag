import json

ARQUIVO_DADOS = "dados.json"


def carregar_dados():
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"disciplinas": []}


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def gerar_plano(disciplinas):
    return sorted(
        disciplinas,
        key=lambda d: d["prioridade"] * d["dificuldade"],
        reverse=True
    )


from google import genai
from flask import current_app


def gerar_resumo_disciplina(plano_texto, nome_disciplina):
    if not plano_texto or plano_texto.strip() == "":
        return "Não foi encontrado conteúdo no plano de ensino desta disciplina para gerar um resumo."

    client = genai.Client(api_key=current_app.config["GEMINI_API_KEY"])

    prompt = f"""Você é um assistente acadêmico. Com base no plano de ensino da disciplina "{nome_disciplina}" abaixo, crie um resumo de estudos conciso e bem organizado para ajudar o aluno a se preparar para a matéria.

O resumo deve conter:
- Os principais tópicos da disciplina
- Pontos-chave de cada tópico
- O que priorizar nos estudos

Use uma linguagem clara e encorajadora. Formate com tópicos e subtópicos para facilitar a leitura.

PLANO DE ENSINO:
{plano_texto}

Gere o resumo de estudos:"""

    try:
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return resposta.text
    except Exception:
        return "Não foi possível gerar o resumo no momento. Tente novamente em instantes."


def responder_pergunta(pergunta, plano_texto):
    if not plano_texto or plano_texto.strip() == "":
        return "Não foi encontrado conteúdo no plano de ensino desta disciplina."

    client = genai.Client(api_key=current_app.config["GEMINI_API_KEY"])

    prompt = f"""Você é um assistente acadêmico inteligente e prestativo. Seu objetivo é ajudar o aluno a aprender melhor.

Você tem acesso ao plano de ensino da disciplina abaixo. Use-o como referência principal para contextualizar suas respostas.

Você deve ser capaz de:
- Responder perguntas sobre o conteúdo do plano de ensino
- Recomendar recursos externos de aprendizado (vídeos, sites, canais do YouTube, cursos online) relevantes aos tópicos da disciplina
- Sugerir o que priorizar nos estudos com base nos tópicos do plano de ensino
- Criar planos de estudo personalizados organizados por semanas ou dias, considerando os temas do plano de ensino
- Dar dicas gerais de estudo e aprendizado

Responda sempre em português, de forma clara, objetiva e encorajadora.

PLANO DE ENSINO DA DISCIPLINA:
{plano_texto}

PERGUNTA DO ALUNO:
{pergunta}
"""

    try:
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return resposta.text
    except Exception:
        return "Não foi possível processar sua pergunta no momento. Tente novamente em instantes."