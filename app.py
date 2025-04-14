from flask import Flask, request, render_template, send_file, Response
import pyodbc
import openpyxl
from functools import wraps

app = Flask(__name__)

# ?? Basic Auth Credentials
USERNAME = 'admin'
PASSWORD = '123'  # Change this to a strong password!

# ?? Authentication Helpers
def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Could not verify your login.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ?? Azure SQL DB Connection Info
server = 'chatbot-server0505.database.windows.net'
database = 'chatbot-db'
username = 'abhinav'
password = 'admin@123456'
driver = '{ODBC Driver 18 for SQL Server}'

# ?? Database connection
def get_db_connection():
    conn = pyodbc.connect(
        f'Driver={driver};Server={server};Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    )
    return conn

# ??? DB Init
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            id INT PRIMARY KEY IDENTITY(1,1),
            name NVARCHAR(100),
            dob DATE,
            qualification NVARCHAR(100)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# ?? Main Chat Form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')  # Must be YYYY-MM-DD format
        qualification = request.form.get('qualification')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (name, dob, qualification) VALUES (?, ?, ?)',
                (name, dob, qualification)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return f"<h3>Thank you, {name}. Your response has been recorded.</h3><a href='/'>Back</a>"
        except Exception as e:
            return f"<h3>Error inserting data into database: {e}</h3><a href='/'>Back</a>"

    return render_template('index.html')

# ?? View All Entries (Protected)
@app.route('/entries')
@requires_auth
def view_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, dob, qualification FROM users")
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('entries.html', entries=entries)

# ?? Export Entries to Excel (Protected)
@app.route('/export')
@requires_auth
def export_to_excel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, dob, qualification FROM users")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Name', 'DOB', 'Qualification'])
    for row in data:
        ws.append(row)

    file_path = "user_data.xlsx"
    wb.save(file_path)
    return send_file(file_path, as_attachment=True)

# ?? Init the DB table
init_db()

# ?? Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
