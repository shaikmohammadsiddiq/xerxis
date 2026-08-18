from pathlib import Path
import jpype
import jaydebeapi

jar_path = Path(__file__).parent / "jconn4.jar"

if not jpype.isJVMStarted():
    jpype.startJVM(
        classpath=[str(jar_path)]
    )

print("JVM started:", jpype.isJVMStarted())

conn = jaydebeapi.connect(
    "com.sybase.jdbc4.jdbc.SybDriver",
    "jdbc:sybase:Tds:HOST:5000/DATABASE",
    ["USERNAME", "PASSWORD"]
)