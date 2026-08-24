from flask import Blueprint, render_template, request, redirect, url_for, session
from .services import carregar_dados, salvar_dados, gerar_plano, responder_pergunta, gerar_resumo_disciplina
from app import db
from app.models import Disciplina, Usuario
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import pdfplumber

main = Blueprint("main", __name__)
UPLOAD_FOLDER = "uploads/planos_ensino"

# DASHBOARD / MENU DO SISTEMA
@main.route("/")
def index():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    return render_template("index.html")


# LOGIN
@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        matricula = request.form["matricula"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(matricula=matricula).first()

        if not usuario or not check_password_hash(usuario.senha, senha):
            return render_template("login.html", erro="Matrícula ou senha inválidos.")

        session["usuario"] = usuario.matricula
        session["tipo"] = usuario.tipo
        session["nome"] = usuario.nome

        return redirect(url_for("main.index"))

    return render_template("login.html")


# LOGOUT
@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))


# CADASTRO
@main.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        nome = request.form["nome"]
        matricula = request.form["matricula"]
        senha = request.form["senha"]
        tipo = request.form["tipo"]

        if Usuario.query.filter_by(matricula=matricula).first():
            return render_template("cadastro.html", erro="Matrícula já cadastrada.")

        novo_usuario = Usuario(
            nome=nome,
            matricula=matricula,
            senha=generate_password_hash(senha),
            tipo=tipo
        )
        db.session.add(novo_usuario)
        db.session.commit()

        return redirect(url_for("main.login"))

    return render_template("cadastro.html")


# DISCIPLINAS (dados usados pela IA)
@main.route("/disciplinas", methods=["GET", "POST"])
def disciplinas():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    dados = carregar_dados()

    if request.method == "POST":
        nome = request.form["nome"]
        dificuldade = int(request.form["dificuldade"])
        prioridade = int(request.form["prioridade"])

        dados["disciplinas"].append({
            "nome": nome,
            "dificuldade": dificuldade,
            "prioridade": prioridade
        })

        salvar_dados(dados)

        return redirect(url_for("main.disciplinas"))

    return render_template("disciplinas.html", disciplinas=dados["disciplinas"])


# GERAR PLANO DE ESTUDO
@main.route("/plano")
def plano():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    dados = carregar_dados()
    plano_gerado = gerar_plano(dados["disciplinas"])

    return render_template("planos.html", plano=plano_gerado)


# CADASTRAR DISCIPLINA
@main.route("/cadastrar-disciplina", methods=["GET", "POST"])
def cadastrar_disciplina():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    if session.get("tipo") != "professor":
        return redirect(url_for("main.index"))

    if request.method == "POST":

        nome = request.form["nome"]
        carga_horaria = request.form["carga_horaria"]
        ementa = request.form["ementa"]

        arquivo_pdf = request.files.get("plano_pdf")

        texto_plano = ""
        nome_seguro = None

        if arquivo_pdf and arquivo_pdf.filename != "":

            nome_seguro = secure_filename(arquivo_pdf.filename)
            caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_seguro)

            arquivo_pdf.save(caminho_arquivo)

            with pdfplumber.open(caminho_arquivo) as pdf:
                for pagina in pdf.pages:
                    texto_plano += pagina.extract_text() or ""

        nova_disciplina = Disciplina(
            nome=nome,
            carga_horaria=carga_horaria,
            ementa=ementa,
            plano_texto=texto_plano,
            arquivo_pdf=nome_seguro
        )

        db.session.add(nova_disciplina)
        db.session.commit()

        return redirect(url_for("main.cadastrar_disciplina"))

    disciplinas = Disciplina.query.order_by(Disciplina.id.desc()).all()
    return render_template("cadastrar_disciplina.html", disciplinas=disciplinas)


# LISTAR DISCIPLINAS
@main.route("/disciplinas-lista")
def listar_disciplinas():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    disciplinas = Disciplina.query.all()

    matriculadas_ids = set()
    if session.get("tipo") == "aluno":
        usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()
        if usuario:
            matriculadas_ids = {d.id for d in usuario.disciplinas_matriculadas}

    return render_template(
        "listar_disciplinas.html",
        disciplinas=disciplinas,
        matriculadas_ids=matriculadas_ids
    )


# MINHAS DISCIPLINAS
@main.route("/minhas-disciplinas")
def minhas_disciplinas():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    if session.get("tipo") != "aluno":
        return redirect(url_for("main.index"))

    usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()
    disciplinas = usuario.disciplinas_matriculadas if usuario else []

    return render_template("minhas_disciplinas.html", disciplinas=disciplinas)


# MATRICULAR EM DISCIPLINA
@main.route("/disciplina/<int:id>/matricular", methods=["POST"])
def matricular(id):

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    if session.get("tipo") != "aluno":
        return redirect(url_for("main.index"))

    disciplina = Disciplina.query.get_or_404(id)
    usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()

    if usuario and disciplina not in usuario.disciplinas_matriculadas:
        usuario.disciplinas_matriculadas.append(disciplina)
        db.session.commit()

    return redirect(url_for("main.listar_disciplinas"))


# DESMATRICULAR DE DISCIPLINA
@main.route("/disciplina/<int:id>/desmatricular", methods=["POST"])
def desmatricular(id):

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    disciplina = Disciplina.query.get_or_404(id)
    usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()

    if usuario and disciplina in usuario.disciplinas_matriculadas:
        usuario.disciplinas_matriculadas.remove(disciplina)
        db.session.commit()

    return redirect(url_for("main.listar_disciplinas"))


# VISUALIZAR DISCIPLINA
@main.route("/disciplina/<int:id>")
def visualizar_disciplina(id):

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    disciplina = Disciplina.query.get_or_404(id)
    chat = session.get(f"chat_{id}", [])

    matriculado = True
    if session.get("tipo") == "aluno":
        usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()
        matriculado = disciplina in usuario.disciplinas_matriculadas if usuario else False

    return render_template(
        "visualizar_disciplina.html",
        disciplina=disciplina,
        chat=chat,
        matriculado=matriculado
    )

@main.route("/disciplina/<int:id>/perguntar", methods=["POST"])
def perguntar_disciplina(id):

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    disciplina = Disciplina.query.get_or_404(id)

    if session.get("tipo") == "aluno":
        usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()
        if not usuario or disciplina not in usuario.disciplinas_matriculadas:
            return redirect(url_for("main.visualizar_disciplina", id=id))

    pergunta = request.form["pergunta"]

    resposta = responder_pergunta(pergunta, disciplina.plano_texto)

    # pega histórico atual
    chat = session.get(f"chat_{id}", [])

    # adiciona nova interação
    chat.append({
        "pergunta": pergunta,
        "resposta": resposta
    })

    # salva de volta na sessão
    session[f"chat_{id}"] = chat

    return redirect(url_for("main.visualizar_disciplina", id=id))

@main.route("/disciplina/<int:id>/limpar-chat")
def limpar_chat(id):

    session.pop(f"chat_{id}", None)

    return redirect(url_for("main.visualizar_disciplina", id=id))


# DISCIPLINAS IA - RESUMO COM IA
@main.route("/disciplinas-ia", methods=["GET", "POST"])
def disciplinas_ia():

    if "usuario" not in session:
        return redirect(url_for("main.login"))

    if session.get("tipo") != "aluno":
        return redirect(url_for("main.index"))

    usuario = Usuario.query.filter_by(matricula=session["usuario"]).first()
    disciplinas = usuario.disciplinas_matriculadas if usuario else []

    resumo = None
    disciplina_selecionada = None

    if request.method == "POST":
        disciplina_id = int(request.form["disciplina_id"])
        disciplina_selecionada = Disciplina.query.get_or_404(disciplina_id)

        if usuario and disciplina_selecionada in usuario.disciplinas_matriculadas:
            resumo = gerar_resumo_disciplina(disciplina_selecionada.plano_texto, disciplina_selecionada.nome)

    return render_template(
        "disciplinas_ia.html",
        disciplinas=disciplinas,
        resumo=resumo,
        disciplina_selecionada=disciplina_selecionada
    )


# EDITAR DISCIPLINA
@main.route("/disciplina/<int:id>/editar", methods=["GET", "POST"])
def editar_disciplina(id):

    if "usuario" not in session or session.get("tipo") != "professor":
        return redirect(url_for("main.index"))

    disciplina = Disciplina.query.get_or_404(id)

    if request.method == "POST":
        disciplina.nome = request.form["nome"]
        disciplina.carga_horaria = request.form["carga_horaria"]
        disciplina.ementa = request.form["ementa"]

        arquivo_pdf = request.files.get("plano_pdf")
        if arquivo_pdf and arquivo_pdf.filename != "":
            nome_seguro = secure_filename(arquivo_pdf.filename)
            caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_seguro)
            arquivo_pdf.save(caminho_arquivo)

            texto_plano = ""
            with pdfplumber.open(caminho_arquivo) as pdf:
                for pagina in pdf.pages:
                    texto_plano += pagina.extract_text() or ""

            disciplina.arquivo_pdf = nome_seguro
            disciplina.plano_texto = texto_plano

        db.session.commit()
        return redirect(url_for("main.cadastrar_disciplina"))

    return render_template("editar_disciplina.html", disciplina=disciplina)


# EXCLUIR DISCIPLINA
@main.route("/disciplina/<int:id>/excluir", methods=["POST"])
def excluir_disciplina(id):

    if "usuario" not in session or session.get("tipo") != "professor":
        return redirect(url_for("main.index"))

    disciplina = Disciplina.query.get_or_404(id)
    db.session.delete(disciplina)
    db.session.commit()

    next_page = request.referrer
    if next_page and "cadastrar-disciplina" in next_page:
        return redirect(url_for("main.cadastrar_disciplina"))
    return redirect(url_for("main.listar_disciplinas"))