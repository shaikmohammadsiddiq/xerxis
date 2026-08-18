import jpype

driver = jpype.JClass("com.sybase.jdbc4.jdbc.SybDriver")
print(driver)
driver_instance = driver()
print(driver_instance)
from java.sql import DriverManager

DriverManager.registerDriver(driver_instance)
conn = DriverManager.getConnection(
    "jdbc:sybase:Tds:HOST:5000/DATABASE",
    "USERNAME",
    "PASSWORD"
)
import jaydebeapi

conn = jaydebeapi.connect(
    "com.sybase.jdbc4.jdbc.SybDriver",
    "jdbc:sybase:Tds:HOST:5000/DATABASE",
    ["USERNAME", "PASSWORD"],
    r"C:\your_project\jconn4.jar"
)