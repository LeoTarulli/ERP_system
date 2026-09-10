import sqlite3
import pandas as pd
from sqlalchemy import create_engine

sqlite_conn = sqlite3.connect("erp_system.db")
pg_engine = create_engine("postgresql://postgres.hzknvlgcdhsbyipsbdad:w%2F5PdCQHCN%3FYSjk@aws-1-eu-west-1.pooler.supabase.com:5432/postgres")

# Migrar tablas auxiliares que usa tu app
for table in ["PriceLogs", "CostLogs"]:
    try:
        df = pd.read_sql_query(f'SELECT * FROM "{table}"', sqlite_conn)
        df.columns = [c.replace(" ", "").lower() for c in df.columns]
        with pg_engine.begin() as conn:
            df.to_sql(table.lower(), conn, if_exists="replace", index=False)
        print(f"✅ {table} migrada.")
    except Exception as e:
        print(f"⚪ {table}: {e}")

sqlite_conn.close()