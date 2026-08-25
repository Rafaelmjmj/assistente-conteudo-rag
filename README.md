# Assistente de Conteúdo Baseado em IA (RAG)

Aplicação web que ajuda estudantes do curso de **Análise e Desenvolvimento de Sistemas (IFG)** a entenderem melhor as disciplinas da grade curricular. O professor cadastra as disciplinas e envia o **plano de ensino em PDF**; a aplicação extrai o conteúdo e o utiliza como contexto para o modelo **Google Gemini**, que responde às dúvidas dos alunos e gera resumos de cada matéria via **RAG (Retrieval-Augmented Generation)**. Desenvolvida em **Python/Flask** com **PostgreSQL**.

> Trabalho de Conclusão de Curso (TCC) do Tecnólogo em Análise e Desenvolvimento de Sistemas, Instituto Federal de Goiás (IFG), Campus Formosa. Projeto entregue de ponta a ponta, apresentado e aprovado pela banca, com homologação concluída.

![Menu_Aluno](docs/Menu_Aluno.jpeg)
![Chat_Bot](docs/Area_Disciplina_ChatBot.jpeg)
![resposta_1°apergunta](docs/Resposta_1°aPergunta.jpeg)
---

## Sobre o projeto

Muitos alunos, novatos e veteranos, têm dificuldade de entender o que realmente cai em cada disciplina da grade: às vezes o nome da matéria não tem relação óbvia com o conteúdo, e às vezes o estudante simplesmente não consegue imaginar o que vai ser abordado ao longo do semestre.

Este projeto ataca esse problema com um site que dá **acesso separado para professores e alunos**:

- O **professor** cadastra as disciplinas e envia o plano de ensino (PDF) de cada uma.
- O **aluno** acessa a página de uma disciplina e interage com uma IA (API do Google Gemini) que responde às suas dúvidas sobre aquela matéria especificamente.
- Uma aba de **"Resumo por IA"** gera um panorama da disciplina, explicando o conteúdo e destacando o que é mais útil e importante para o andamento do semestre.

A IA responde **ancorada no plano de ensino daquela matéria**, e não apenas no conhecimento genérico do modelo, mantendo as respostas dentro do escopo real da disciplina.

## Como a IA foi implementada

O projeto usa **RAG por context stuffing**. O fluxo é:

1. O professor faz upload do plano de ensino em PDF.
2. A aplicação extrai o texto do PDF (via `pdfplumber`) e o associa à disciplina.
3. Ao responder uma dúvida ou gerar um resumo, esse texto é inserido diretamente no prompt enviado ao Gemini, junto com instruções de sistema que definem o comportamento do assistente para aquela matéria.

Decisões técnicas importantes (e conscientes):

- **Sem fine-tuning.** O comportamento é obtido por engenharia de prompt e pela injeção de contexto, não por treino do modelo.
- **Sem embeddings / busca vetorial.** A recuperação de contexto é feita por context stuffing, adequado ao escopo do projeto (o contexto relevante é o plano de ensino da própria disciplina). Fica registrado como evolução natural a migração para busca semântica com embeddings caso o volume de conteúdo por matéria cresça.
- **Engenharia de prompt** para delimitar o papel do assistente, manter as respostas dentro do conteúdo da disciplina e padronizar o formato do resumo.

## Funcionalidades

- Autenticação com **perfis distintos** de professor e aluno
- **Cadastro de disciplinas** e **upload do plano de ensino em PDF** pelo professor
- **Extração automática do conteúdo** do PDF para uso como contexto da IA
- **Página por disciplina** com assistente de IA que responde dúvidas do aluno sobre aquela matéria
- Aba **"Resumo por IA"**: resumo do conteúdo da disciplina com dicas do que é mais relevante para o semestre

## Arquitetura

```
Professor  ──►  cadastra disciplina + upload do plano de ensino (PDF)
                          │
                          ▼
             Extração de texto (pdfplumber)  ──►  PostgreSQL
                                                      │
Aluno  ──►  página da disciplina  ──────────────►     │
                    │                                  │
                    ▼                                  ▼
        Montagem do prompt  ◄──  conteúdo do plano de ensino (contexto)
                    │            + instruções de sistema
                    ▼
        API do Google Gemini  ──►  resposta às dúvidas / resumo da matéria
```

## Tecnologias

- **Linguagem:** Python 3.14
- **Backend / Web:** Flask 3.1, Jinja2
- **ORM / Banco:** Flask-SQLAlchemy, SQLAlchemy 2.0, PostgreSQL (driver `psycopg2-binary`)
- **Migrations:** Flask-Migrate, Alembic
- **IA generativa:** Google Gemini (`google-genai` / `google-generativeai`)
- **Extração de PDF:** pdfplumber, pdfminer.six, pypdfium2
- **Configuração:** python-dotenv
- **Infraestrutura:** Docker, Docker Compose
- **Técnicas:** RAG (context stuffing), engenharia de prompt

## Como executar

### Opção 1: Docker Compose (recomendado)

Sobe a aplicação e um PostgreSQL 16 já configurado, e aplica as migrations automaticamente.

```bash
# 1. Clonar o repositório
git clone https://github.com/Rafaelmjmj/assistente-conteudo-rag.git
cd assistente-conteudo-rag

# 2. Configurar as variáveis de ambiente
cp .env.example .env
# edite o .env e informe sua GEMINI_API_KEY

# 3. Subir os containers
docker-compose up --build
```

A aplicação estará disponível em `http://localhost:5000`.

### Opção 2: Ambiente local (sem Docker)

Requer um PostgreSQL instalado e em execução.

```bash
# 1. Clonar e entrar no diretório
git clone https://github.com/Rafaelmjmj/assistente-conteudo-rag.git
cd assistente-conteudo-rag

# 2. Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Criar o banco de dados no PostgreSQL
#    (padrão esperado: banco 'tcc_db' em localhost:5433)

# 5. Configurar as variáveis de ambiente
cp .env.example .env
# edite o .env com a GEMINI_API_KEY e o DATABASE_URL

# 6. Aplicar as migrations
flask db upgrade

# 7. Executar a aplicação
python run.py
```

### Variáveis de ambiente (`.env`)

```
GEMINI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5433/tcc_db
```

## Estrutura do projeto

```
.
├── app/
│   ├── static/               # css, img, js
│   ├── templates/            # páginas (login, disciplinas, disciplinas_ia, resumo, etc.)
│   ├── __init__.py           # application factory
│   ├── models.py             # modelos SQLAlchemy
│   ├── routes.py             # rotas / controllers
│   └── services.py           # regras de negócio, integração com o Gemini e parsing de PDF
├── migrations/               # migrations do Alembic / Flask-Migrate
├── uploads/planos_ensino/    # PDFs de planos de ensino enviados pelos professores
├── config.py                 # configuração da aplicação
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── run.py                    # entrypoint
```

## Contexto acadêmico

Projeto desenvolvido como Trabalho de Conclusão de Curso do Tecnólogo em Análise e Desenvolvimento de Sistemas no IFG, Campus Formosa. Apresentado à banca examinadora e homologado. O foco foi aplicar IA generativa de forma prática e útil, integrando um modelo de linguagem a uma base de conhecimento própria (os planos de ensino das disciplinas) para resolver um problema real dos estudantes do curso.

## Autor

**Rafael Machado Jeziorny**
[LinkedIn](https://www.linkedin.com/in/rafael-machado-62332b239) · [GitHub](https://github.com/Rafaelmjmj)
