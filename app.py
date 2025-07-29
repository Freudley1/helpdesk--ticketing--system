from db_setup import initialize_database
initialize_database()
from flask import Flask, render_template, request, session, redirect, url_for, flash
import sqlite3
import os
from flask_mail import Mail, Message

from dotenv import load_dotenv
load_dotenv()


app = Flask (__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USENAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

def send_notification_email(to, subject, body):
    msg = Message(subject, 
                  sender=('Support Team',app.config['MAIL_USERNAME']), recipients=[to])
    msg.body = body
    mail.send(msg)


#Home page
@app.route('/')
def index():
    return render_template('index.html')


#Create Ticket
@app.route('/create_ticket', methods=['GET', 'POST'])
def create_ticket():
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        submitted_by = request.form['submitted_by']
        email = request.form['email']
        category_id = request.form.get('category_id') or None
        priority_id= request.form.get('priority_id') or None

        c.execute('''
                  Insert Into New_Tickets (title, description, submitted_by, email, status, category_id, priority_id) 
         Values(?,?,?,?,?,?,?)
         ''',(title,description,submitted_by,email,'open', category_id, priority_id))
        conn.commit()
        print("Ticket inserted successfully.")

        conn.close ()

        flash('Ticket submitted succesfully!')
        return redirect(url_for('view_tickets'))
    
    categories = c.execute('SELECT * FROM Categories').fetchall()
    priorities = c.execute('SELECT * FROM Priorities').fetchall()
    conn.close()

    
    return render_template('create_ticket.html', categories=categories, priorities=priorities)

#View Tickets
@app.route('/view_tickets')
def view_tickets():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(''' SELECT 
        nt.id, nt.title, nt.description, nt.submitted_by, nt.email, nt.status, 
        nt.created_at,
        c.name as category_name,
        p.level as priority_level,
        nt.status,
        nt.admin_notes,
        nt.created_at    
    FROM New_Tickets nt
    LEFT JOIN Categories c ON nt.category_id = c.id
    LEFT JOIN Priorities p ON nt.priority_id = p.id
        ORDER BY nt.created_at DESC      ''')
    tickets = c.fetchall()
    conn.close()
    return render_template('view_tickets.html', New_Tickets = tickets)


app.secret_key = 'mysecretkey'

ADMIN_USERNAME= 'freudleyl'
ADMIN_PASSWORD = 'helloworld'

def get_db_connection():
    conn = sqlite3.connect('helpdesk.db')
    conn.row_factory =sqlite3.Row
    return conn

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    ticket_id = request.args.get('ticket_id')
    new_status = request.args.get('new_status')
    error= None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True

            if ticket_id and new_status:
                return redirect(url_for('update_status', ticket_id=ticket_id, new_status=new_status))
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials. Try again."

    return render_template('admin_login.html', ticket_id=ticket_id, new_status=new_status)

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            nt.id, nt.title, nt.description, nt.submitted_by, nt.email, nt.status, 
            c.name AS category_name,
            p.level AS priority_level,
            nt.category_id,
            nt.priority_id,
            nt.created_at,
            nt.admin_notes
            FROM New_Tickets nt
            LEFT JOIN Categories c ON nt.category_id = c.id
            LEFT JOIN Priorities p ON nt.priority_id = p.id
            ORDER BY nt.created_at DESC
    '''  )
    tickets = c.fetchall()
    categories = conn.execute('Select * From Categories').fetchall()
    priorities = conn.execute('Select * From Priorities').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', tickets=tickets, categories=categories, priorities = priorities)

@app.route('/update_admin_ticket', methods=['POST'])
def update_admin_ticket():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    ticket_id = request.form.get('ticket_id')
    category_id= request.form.get('category_id')
    priority_id = request.form.get('priority_id')
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes')

    conn = get_db_connection()
    conn.execute('''
        UPDATE New_Tickets
        SET category_id = ?, priority_id = ?, status = ?, admin_notes = ?
        WHERE id = ?
    ''', (category_id, priority_id, status, admin_notes, ticket_id))

    conn.commit()

    #Get Ticket ID for email details
    ticket = conn.execute('''SELECT nt.*, 
           c.name AS category_name, 
           p.level AS priority_level
    FROM New_Tickets nt
    LEFT JOIN Categories c ON nt.category_id = c.id
    LEFT JOIN Priorities p ON nt.priority_id = p.id
    WHERE nt.id = ?''', (ticket_id)).fetchone()
    conn.close()

    #compose Email
    subject = f"Your ticket #{ticket_id} has been updated"
    body = f"""
    Hello {ticket['submitted_by']},

    Your support ticket titled '{ticket['title']}' has been updated.

    - Status: {status}
    - Priority: {ticket['priority_level']}
    - Category: {ticket['category_name']}
    - Admin Notes: {admin_notes}

    Thank you,
    Support Team
    """

    #Send email
    send_notification_email(ticket['email'], subject, body)

    flash('Ticket updated with priority, status and admin notes!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status_inline', methods=['POST'])
def update_status_inline():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    ticket_id = request.form.get('ticket_id')
    new_status = request.form.get('new_status').lower()
    print(f'ticket_id: {ticket_id}, new_status: {new_status}')

    conn = get_db_connection()
    conn.execute('UPDATE New_Tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
    conn.commit()
    conn.close()

    flash('Ticket status updated!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status/<int:ticket_id>/<new_status>')
def update_status(ticket_id, new_status):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login', ticket_id=ticket_id, new_status=new_status))

    conn = get_db_connection()
    conn.execute('UPDATE New_Tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/update_status_inline_ajax', methods=['POST'])
def update_status_inline_ajax():
    if not session.get('admin_logged_in'):
        return 'Unauthorized', 401

    ticket_id = request.form.get('ticket_id')
    new_status = request.form.get('new_status')

    if not ticket_id or not new_status:
        return 'Bad Request', 400

    conn = get_db_connection()
    conn.execute('UPDATE New_Tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
    conn.commit()
    conn.close()

    return 'Success', 200




if __name__ == '__main__':
    app.run(debug=True)