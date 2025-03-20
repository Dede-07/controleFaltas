from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Criar banco de dados SQLite
def init_db():
    conn = sqlite3.connect("faltas.db")
    cursor = conn.cursor()

    # Criar tabela de matérias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        total_aulas INTEGER NOT NULL
    )
    """)

    # Criar tabela de faltas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faltas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        materia_id INTEGER NOT NULL,
        data_falta TEXT NOT NULL,
        motivo TEXT,
        FOREIGN KEY(materia_id) REFERENCES materias(id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

def contar_faltas():
    conn = sqlite3.connect("faltas.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT materias.id, materias.nome, COUNT(faltas.id) as total_faltas, materias.total_aulas
    FROM materias
    LEFT JOIN faltas ON materias.id = faltas.materia_id
    GROUP BY materias.id
    """)
    
    dados = cursor.fetchall()
    conn.close()

    estatisticas = []
    for id_materia, nome, total_faltas, total_aulas in dados:
        max_faltas = total_aulas * 0.25  # 25% do limite de faltas
        faltas_restantes = max_faltas - total_faltas
        estatisticas.append({
            "id": id_materia,
            "materia": nome,
            "total_faltas": total_faltas,
            "max_faltas": max_faltas,
            "faltas_restantes": faltas_restantes
        })

    return estatisticas

# Página inicial
@app.route("/")
def index():
    conn = sqlite3.connect("faltas.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT faltas.id, materias.nome, faltas.data_falta, faltas.motivo
    FROM faltas
    JOIN materias ON materias.id = faltas.materia_id
    """)
    faltas = cursor.fetchall()
    conn.close()

    estatisticas = contar_faltas()

    return render_template("index.html", faltas=faltas, estatisticas=estatisticas)

# Página - adicionar matéria
@app.route("/add_materia", methods=["GET", "POST"])
def add_materia():
    if request.method == "POST":
        nome = request.form["nome"]
        total_aulas = int(request.form["total_aulas"])

        conn = sqlite3.connect("faltas.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO materias (nome, total_aulas) VALUES (?, ?)", (nome, total_aulas))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_materia.html")

# Página - adicionar falta
@app.route("/add_falta", methods=["GET", "POST"])
def add_falta():
    conn = sqlite3.connect("faltas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM materias")
    materias = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        materia_id = request.form["materia_id"]
        data_falta = request.form["data_falta"]
        motivo = request.form["motivo"]
        num_aulas = int(request.form["num_aulas"])  # Pega o número de aulas que faltou

        if not materia_id:
            return "Erro: Matéria não selecionada."

        materia_id = int(materia_id)

        # Verificar se materia_id existe no banco de dados
        conn = sqlite3.connect("faltas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM materias WHERE id = ?", (materia_id,))
        materia = cursor.fetchone()
        if not materia:
            return "Erro: Matéria inválida."

        # Registrar as faltas para o número de aulas faltadas
        for _ in range(num_aulas): 
            cursor.execute("INSERT INTO faltas (materia_id, data_falta, motivo) VALUES (?, ?, ?)", 
                           (materia_id, data_falta, motivo))
        
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_falta.html", materias=materias)


# Remover falta
@app.route("/delete_falta/<int:id>")
def delete_falta(id):
    conn = sqlite3.connect("faltas.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faltas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# Remover matéria
@app.route("/delete_materia/<int:id>")
def delete_materia(id):
    try:
        conn = sqlite3.connect("faltas.db")
        cursor = conn.cursor()

        # Excluir faltas relacionadas à matéria
        cursor.execute("DELETE FROM faltas WHERE materia_id = ?", (id,))
        print("Faltas deletadas para a matéria:", id)

        # Excluir a matéria
        cursor.execute("DELETE FROM materias WHERE id = ?", (id,))
        print("Matéria deletada com id:", id)

        conn.commit()
    except Exception as e:
        print("Erro ao excluir matéria ou faltas:", e)
    finally:
        conn.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
