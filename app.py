import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root', 
        password='87973235', 
        database='sistema_emprestimo'
    )
    return connection

################################## ROTA SOLICITAR EMPRESTIMO ######################################################
@app.route('/solicitar_emprestimo', methods=['POST'])
def solicitar_emprestimo():
    cliente_id = request.form['cliente_id']
    valor = request.form['valor']
    prazo = request.form['prazo']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO emprestimos (cliente_id, valor, prazo) VALUES (%s, %s, %s)", (cliente_id, valor, prazo))
        conn.commit()
        flash('Empréstimo solicitado com sucesso!', 'success')
    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('solicitar_emprestimo'))



############ ROTA GERENCIAR CLIENTES ######################
@app.route('/gerenciar_clientes')
def gerenciar_clientes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('gerenciar_clientes.html', clientes=clientes)



################################ ROTA DE CADASTRO DE USUARIO ####################################################
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not email or not password or not confirm_password:
            flash("Todos os campos devem ser preenchidos", "error")
            return render_template('cadastro.html')

        if password != confirm_password:
            flash("Houve divergência na confirmação da senha", "error")
            return render_template('cadastro.html')

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute('SELECT * FROM usuarios WHERE username = %s OR email = %s', (username, email))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente[1] == username:
                    flash("Nome de usuário já existente!", "error")
                if usuario_existente[2] == email:
                    flash("E-mail já existente!", "error")
                return render_template('cadastro.html')

            cursor.execute('INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)', 
                           (username, email, password))
            connection.commit()

            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for('login'))
        
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar Usuário: {str(err)}", "error")
            return render_template('cadastro.html')
        
        finally:
            cursor.close()
            connection.close()

    return render_template('cadastro.html')

######################################################## ROTA DE LOGIN DE USUARIO #################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha incorretos!', "error")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/')
def home():
    if 'username' in session:
        print(f'Bem-vindo, {session["username"]}!')
        return render_template('index.html')  # Renderize o template `index.html`
    else:
        print('Usuário não autenticado. Redirecionando para Login.')
        return redirect(url_for('login'))


################################################# DESLOGAR ##########################################################################################
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado!', 'info')
    return redirect(url_for('login'))

######################################################## CADASTRO DE CLIENTES ######################################################

@app.route('/registrar_cliente', methods=['POST'])
def registrar_cliente():
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verifica se o cliente já existe
        cursor.execute("SELECT * FROM clientes WHERE nome = %s OR email = %s", (nome, email))
        cliente_existente = cursor.fetchone()
        
        if cliente_existente:
            flash('Cliente já cadastrado com este nome ou email!', 'danger')
            return redirect(url_for('gerenciar_clientes'))
        
        # Insere novo cliente
        cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s)", (nome, email, telefone))
        conn.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
    
    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'danger')
    
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('gerenciar_clientes'))



############################################# CONSULTAR CLIENTES #######################################################

@app.route('/consultar_clientes', methods=['GET'])
def consultar_clientes():
    consulta = request.args.get('consulta', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM clientes WHERE nome LIKE %s OR email LIKE %s"
    cursor.execute(query, (f'%{consulta}%', f'%{consulta}%'))
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('gerenciar_clientes.html', clientes=clientes)



################################################ EDITAR CLIENTE ##############################################
@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']

        try:
            # Atualiza cliente no banco de dados
            cursor.execute("""
                UPDATE clientes SET nome = %s, email = %s, telefone = %s WHERE id = %s
            """, (nome, email, telefone, id))
            conn.commit()
            flash('Cliente atualizado com sucesso!', 'success')
        except mysql.connector.Error as err:
            flash(f'Erro: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('gerenciar_clientes'))

    # Buscar o cliente específico para preencher o formulário de edição
    cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
    cliente = cursor.fetchone()

    cursor.close()
    conn.close()

    if cliente:
        return render_template('editar_cliente.html', cliente=cliente)
    else:
        flash('Cliente não encontrado!', 'danger')
        return redirect(url_for('index'))

################################## DELETAR CLIENTE #############################################
@app.route('/deletar_cliente/<int:id>', methods=['POST'])
def deletar_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        conn.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('gerenciar_clientes'))


if __name__ == '__main__':
    app.run(debug=True)