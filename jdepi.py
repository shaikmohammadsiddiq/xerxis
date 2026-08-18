import jaydebeapi

conn = jaydebeapi.connect(
    "com.sybase.jdbc4.jdbc.SybDriver",
    "jdbc:sybase:Tds:HOST:5000/DATABASE",
    ["USERNAME", "PASSWORD"],
    "/path/to/jconn4.jar"
)

cursor = conn.cursor()

cursor.execute("SELECT @@version")

for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()