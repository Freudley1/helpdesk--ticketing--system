import sqlite3

conn = sqlite3.connect('helpdesk.db')
c = conn.cursor()

#drop existing tables to avoid conflicts.
c.execute('DROP TABLE IF EXISTS Status_Logs')
c.execute('DROP TABLE IF EXISTS New_Tickets')
c.execute('DROP TABLE IF EXISTS Priorities')
c.execute('DROP TABLE IF EXISTS Categories')
c.execute('DROP TABLE IF EXISTS Users')

#Users table
c.execute('''
    Create Table Users(
          id integer Primary Key AUTOINCREMENT,
          employee_id Text Unique,
          username Text Not Null,
          email Text Not Null,
          role Text Not Null --'admin' or 'user'
    )
''')
#categories for tickets
c.execute('''
          Create Table Categories(
          id Integer Primary Key AUTOINCREMENT,
          name Text Not Null
          )
     ''')

# Priorities for tickets (Low, Medium, High)
c.execute('''
    CREATE TABLE Priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL
    )
''')


#Create A ticket
c.execute('''
    Create Table New_Tickets (
        id integer Primary Key AUTOINCREMENT,
        title Text NOT Null,
        description Text Not Null,
        submitted_by Text Not Null,
          email Text Not Null,
        status Text Default 'Open'
    )
''')

#Update the New_tickets table
c.execute('''ALTER TABLE New_Tickets ADD COLUMN category_id INTEGER;''')
c.execute('ALTER TABLE New_Tickets ADD COLUMN priority_id INTEGER;')
c.execute('ALTER TABLE New_Tickets ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;')

# Status log: tracks changes made by admins only
c.execute('''
    CREATE TABLE Status_Logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        old_status TEXT NOT NULL,
        new_status TEXT NOT NULL,
        changed_by INTEGER,           -- references Users.id (admin who changed)
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES New_Tickets(id),
        FOREIGN KEY (changed_by) REFERENCES Users(id)
    )
''')

# Seed Categories (feel free to add more)
categories = [('IT',), ('Facilities',), ('HR',), ('Accounting',), ('Networking',)]
c.executemany('INSERT INTO Categories (name) VALUES (?)', categories)

# Seed Priorities
priorities = [('Low',), ('Medium',), ('High',)]
c.executemany('INSERT INTO Priorities (level) VALUES (?)', priorities)

import os
print(os.path.abspath('helpdesk.db'))

conn.commit()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables in DB:", tables)
conn.close()

print('Database and Table created succesfully')

