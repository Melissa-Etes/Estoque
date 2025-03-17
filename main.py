from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import pandas as pd
import os
import csv

# Configuração do banco de dados
DB_NAME = "banco_de_dados.db"
UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar a pasta de uploads, se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Função para inicializar o banco de dados
def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processar', methods=['POST'])
def processar():
    nome = request.form.get('nome')
    preco = request.form.get('preco')
    quantidade = request.form.get('quantidade')
    
    if not nome or not preco or not quantidade:
        return "Erro: Todos os campos são obrigatórios."
    
    try:
        preco = float(preco)
        quantidade = int(quantidade)
    except ValueError:
        return "Erro: Preço ou quantidade inválidos. Insira números válidos."
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)''', (nome, preco, quantidade))
    conn.commit()
    conn.close()
    
    mensagem = f"{quantidade} de {nome} foi adicionado ao estoque custando R${preco:.2f}."
    return render_template("popup_redireciona.html", mensagem=mensagem)

@app.route('/estoque')
def estoque():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    produtos = df.to_dict(orient='records')
    return render_template('estoque.html', produtos=produtos)

@app.route('/apagar', methods=['POST'])
def apagar():
    id_produto = request.form.get('id')
    if not id_produto:
        return "Erro: ID do produto não informado."
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/alterar-tabela', methods=['POST'])
def alterar_tabela():
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados inválidos"})
    
    id_produto = dados.get('id')
    nome = dados.get('nome')
    preco = dados.get('preco')
    quantidade = dados.get('quantidade')
    
    if not id_produto or not nome or not preco or not quantidade:
        return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios"})
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE produtos
        SET nome = ?, preco = ?, quantidade = ?
        WHERE id = ?
    """, (nome, preco, quantidade, id_produto))
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso"})

@app.route('/process_csv', methods=['POST'])
def process_csv():
    if 'csv_file' not in request.files:
        return "Erro: Nenhum arquivo foi enviado."
    
    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return "Erro: Por favor, envie um arquivo CSV válido."
    
    stream = file.stream.read().decode("utf-8").splitlines()
    reader = csv.reader(stream)
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for row in reader:
            if len(row) != 3:
                continue  # Ignora linhas inválidas
            nome, preco, quantidade = row
            try:
                cursor.execute("""
                    INSERT INTO produtos (nome, preco, quantidade)
                    VALUES (?, ?, ?)
                """, (nome, float(preco), int(quantidade)))
            except ValueError:
                continue  # Ignora linhas com dados inválidos
        conn.commit()
    
    return "Dados do CSV inseridos no banco com sucesso!"


if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True)