from app import db

matriculas = db.Table(
    "matriculas",
    db.Column("usuario_id", db.Integer, db.ForeignKey("usuarios.id"), primary_key=True),
    db.Column("disciplina_id", db.Integer, db.ForeignKey("disciplinas.id"), primary_key=True)
)


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="aluno")

    def __repr__(self):
        return f"<Usuario {self.matricula}>"


class Disciplina(db.Model):
    __tablename__ = "disciplinas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    carga_horaria = db.Column(db.String(50), nullable=False)
    ementa = db.Column(db.Text, nullable=False)
    plano_texto = db.Column(db.Text, nullable=True)
    arquivo_pdf = db.Column(db.String(255), nullable=True)
    alunos = db.relationship("Usuario", secondary=matriculas, backref="disciplinas_matriculadas")

    def __repr__(self):
        return f"<Disciplina {self.nome}>"