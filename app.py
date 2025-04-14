import pyodbc
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

# Secret key for session management
app.secret_key = '123'

# Azure SQL DB connection details
server = 'chatbot-server0505.database.windows.net'
database = 'chatbot-db'
username = 'abhinav'
password = 'admin@123456'
driver = '{ODBC Driver 18 for SQL Server}'

def get_db_connection():
    conn = pyodbc.connect(
        f'Driver={driver};Server={server};Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    )
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            id INT PRIMARY KEY IDENTITY(1,1),
            name NVARCHAR(100),
            dob DATE,
            qualification NVARCHAR(100),
            CONSTRAINT unique_user UNIQUE (name, dob)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check hardcoded username/password (can be replaced with DB validation)
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('show_entries'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Authentication check for access to entries page
def is_logged_in():
    return 'logged_in' in session and session['logged_in']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        qualification = request.form.get('qualification')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check for duplicate
            cursor.execute('SELECT COUNT(*) FROM users WHERE name = ? AND dob = ?', (name, dob))
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.close()
                conn.close()
                return f"<h2 style='color: red;'>User with this name and DOB already exists!</h2><a href='/'>Go Back</a>"

            # Insert new entry
            cursor.execute('''
                INSERT INTO users (name, dob, qualification)
                VALUES (?, ?, ?)
            ''', (name, dob, qualification))

            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('show_entries'))
        except Exception as e:
            return f"<h2>Error inserting data: {e}</h2><a href='/'>Go Back</a>"

    return render_template('index.html')

@app.route('/entries')
def show_entries():
    if not is_logged_in():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, dob, qualification, id FROM users')
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('entries.html', entries=entries)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return f"Error deleting entry: {e}"
    return redirect(url_for('show_entries'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove the logged_in session
    return redirect(url_for('login'))

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
