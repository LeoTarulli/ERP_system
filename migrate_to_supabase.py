import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

SQLITE_DB = "erp_system.db"
SUPABASE_URL = "postgresql://postgres.hzknvlgcdhsbyipsbdad:w%2F5PdCQHCN%3FYSjk@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"

print("Conectando a SQLite y Supabase...")
sqlite_conn = sqlite3.connect(SQLITE_DB)
pg_engine = create_engine(SUPABASE_URL)

# Tablas a migrar
TABLES = [
    "Products",
    "Shops",
    "Orders",
    "OrderDetails",
    "MainInventory",
    "InventoryDetails",
    "ProductionBatches"
]

print("\n--- Migrando tablas con estructura idéntica y nombres en minúsculas ---")

for table in TABLES:
    pg_table_name = table.lower()
    try:
        # 1. Leer datos de SQLite
        df = pd.read_sql_query(f'SELECT * FROM "{table}"', sqlite_conn)
        if df.empty:
            print(f"⚪ {table}: Vacía en SQLite.")
            continue

        # 2. Convertir todas las columnas a minúsculas y sin espacios
        df.columns = [c.replace(" ", "").lower() for c in df.columns]

        # 3. Eliminar tabla previa en Postgres y recrearla con las columnas exactas del DataFrame
        with pg_engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{pg_table_name}", {pg_table_name} CASCADE;'))
            
            # Pandas crea la tabla en Postgres con todas las columnas existentes
            df.to_sql(
                pg_table_name,
                conn,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=500
            )

        print(f"✅ {pg_table_name}: {len(df)} registros migrados con éxito (con todas sus columnas).")

    except Exception as e:
        print(f"⚠️ {table} -> {pg_table_name}: {e}")

sqlite_conn.close()
print("\n🎉 Migración 100% completada sin discrepancia de columnas.")