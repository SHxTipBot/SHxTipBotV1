
import sqlite3
conn = sqlite3.connect('shx_tip.db')
c = conn.cursor()
c.execute('SELECT amount, id FROM internal_withdrawals ORDER BY created_at DESC LIMIT 5')
rows = c.fetchall()
for r in rows:
    print(repr(r[0]), type(r[0]))

