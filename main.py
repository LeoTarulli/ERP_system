import streamlit as st
import pandas as pd

# Conectar al archivo SQLite creado
conn = st.connection("erp_db", type="sql", url="sqlite:///erp_system.db")

st.title("Sistema ERP - Panel de Control")

# Selector dinámico de tablas para inspeccionar
tablas_disponibles = [
    "Products", "Orders", "OrderDetails", "sales", 
    "Shops", "Categories", "Contact", "PriceLogs", "CostLogs", "Regular"
]

tabla_seleccionada = st.selectbox("Selecciona una tabla para ver registros:", tablas_disponibles)

# Consultar y renderizar datos en tiempo real
df = conn.query(f'SELECT * FROM "{tabla_seleccionada}" LIMIT 100;', ttl=0)

st.write(f"Mostrando primeros registros de **{tabla_seleccionada}** ({len(df)} filas):")
st.dataframe(df, use_container_width=True)