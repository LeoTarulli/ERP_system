import pandas as pd
import numpy as np

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Connect to the SQLite database
#conn = st.connection("erp_db", type="sql", url="sqlite:///erp_system.db")
conn = st.connection("supabase_db", type="sql")

# Page config
st.set_page_config(
    page_title="Standard ERP System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    vista_radio = st.radio(
        "Sales department:",
        ["Dashboard", "Orders", "Inventory", "Production"],
        index=0
    )

# --- DASHBOARD VIEW ---
if vista_radio == "Dashboard":
    # App Title and Description
    st.title("Standard ERP system for business")
    st.write("This is a ERP system designed to help businesses manage their operations efficiently. Use the sidebar to navigate through different sections and modules of the system.")
    st.write("➡️ You can filter data using the available options. The sidebar provides a user-friendly interface to access various functionalities of the ERP system.")
    st.markdown("-----")

    # Practicing with SQLite database connection and querying
    st.subheader("Database Table Viewer")

    df = conn.query("""
    select * from sales_frame order by "Date" desc;""", ttl=0)
    
    df.rename(columns={"TotalIncome": "Total Income", "TotalCost":"Total Cost"}, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    


    st.markdown("-----")
    st.subheader("Monthly Sales Overview")

    # Month filtering | "%B" gives the full month name and "%b" gives the abbreviated month name
    df["Date"] = pd.to_datetime(df["Date"])

    df["MonthName"] = df["Date"].dt.strftime("%b")
    df["Year"] = df["Date"].dt.year

    month_order_short = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
     ]
    df["MonthName"] = pd.Categorical(df["MonthName"], categories=month_order_short, ordered=True)
    
    month_options = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    foldable_options = ["All Months"] + month_options
    # Year filtering
    year_options = df["Year"].unique().tolist()

    # Filter columns
    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
        select_month = st.selectbox("Filter by Month:", foldable_options)

    with col_filter2:
        select_year = st.selectbox("Filter by Year:", year_options)

    # Applying filters to the dataframe
    df_filtered = df.copy()
    df_orders = df.copy()

    # Filtering dataframe before groupping by
    if select_month != "All Months":
        df_filtered = df_filtered[df_filtered["MonthName"] == select_month]
        df_orders = df_orders[df_orders["MonthName"] == select_month]

    if select_year:
        df_filtered = df_filtered[df_filtered["Year"] == select_year]
        df_orders = df_orders[df_orders["Year"] == select_year]

    # Aggregations
    
    df_monthly_sales = (
        df_filtered.groupby("MonthName")[["Total Income", "Total Cost", "Profit"]]
        .sum()
    )

    df_totalorders = (df_orders.groupby('MonthName')['orderid'].nunique())

    # Bar chart for monthly sales
    st.bar_chart(
        df_monthly_sales,
        y=["Total Income", "Total Cost", "Profit"],
        use_container_width=True,
        stack=False,
        height=400,
        color=["#29b5e8", "#ff4b4b", "#008000"]
    )

    # Line chart for total orders by month
    line_chart = px.line(
        df_totalorders,
        x=df_totalorders.index,
        y=df_totalorders.values,
        labels={"x": "Month", "y": "Total Orders"},
        title="Total Orders by Month",
        markers=True,
        text=df_totalorders.values)
    
    line_chart.update_traces(marker=dict(size=10), 
                             line=dict(color="#29b5e8", width=3),
                             textposition="top right",
                             textfont=dict(size=15))

    st.plotly_chart(line_chart, use_container_width=True)

# --- ORDERS VIEW ---
elif vista_radio == "Orders":
    from sqlalchemy import text
    from datetime import date
    import pandas as pd

    st.title("Orders Management")
    st.write("Register a new sale with multiple items in the ERP system.")
    st.markdown("-----")

    # 1. Initialize shopping cart in session state
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # 2. Fetch lookup data
    products_df = conn.query("SELECT * FROM products;", ttl=0)
    contacts_df = conn.query("SELECT redid, redname FROM contact;", ttl=0)
    categories_df = conn.query("SELECT CategoryID, Category FROM Categories;", ttl=0)
    shops_df = conn.query("SELECT ID, Name FROM Shops;", ttl=0)
    employees_df = conn.query("SELECT EmployeeID, Name FROM Employees;", ttl=0)

    # Precios y costos vigentes desde pricelogs y costlogs
    prices_df = conn.query("SELECT productid, price FROM pricelogs ORDER BY recordid DESC;", ttl=0)
    costs_df = conn.query("SELECT productid, cost FROM costlogs ORDER BY recordid DESC;", ttl=0)

    # 3. Determine Next OrderID and OrderNumber
    orders_head = conn.query(
        "SELECT orderid, ordernumber FROM Orders ORDER BY ordernumber DESC LIMIT 1;", 
        ttl=0
    )
    if not orders_head.empty and orders_head.iloc[0]["orderid"]: 
        last_id = orders_head.iloc[0]["orderid"]
        last_num = int(last_id.replace("Ord-", ""))
        next_order_num = last_num + 1
        next_order_id = f"Ord-{next_order_num}"
    else:
        next_order_num = 1001
        next_order_id = "Ord-1001"

    st.subheader(f"New Order Entry: `{next_order_id}`")

    # 4. Order Header Information (Top Row)
    col1, col2, col3 = st.columns(3)
    with col1:
        customer_name = st.text_input("Customer Name", placeholder="e.g. Maria Gonzalez")
        order_date = st.date_input("Order Date", value=date.today())
    with col2:
        contact_id = st.selectbox(
            "Contact Method",
            options=contacts_df["redid"].tolist(),
            format_func=lambda x: contacts_df.loc[contacts_df["redid"] == x, "redname"].values[0]
        )
        category_id = st.selectbox(
            "Category",
            options=categories_df["categoryid"].tolist(),
            format_func=lambda x: categories_df.loc[categories_df["categoryid"] == x, "category"].values[0]
        )
    with col3:
        shop_id = st.selectbox(
            "Shop",
            options=shops_df["id"].tolist(),
            format_func=lambda x: shops_df.loc[shops_df["id"] == x, "name"].values[0]
        )
        employee_id = st.selectbox(
            "Employee",
            options=employees_df["employeeid"].tolist(),
            format_func=lambda x: employees_df.loc[employees_df["employeeid"] == x, "name"].values[0]
        )

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        discount = st.number_input("Order Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
    with col_sub2:
        is_regular = st.checkbox("Is Regular Customer?")

    st.markdown("---")

    # 5. Add Items to Cart Section
    st.markdown("**Add Products to Order**")
    p_col1, p_col2, p_col3, p_col4 = st.columns([3, 1, 1, 1])

    with p_col1:
        selected_product_id = st.selectbox(
            "Select Product",
            options=products_df["productid"].tolist(),
            format_func=lambda x: products_df.loc[products_df["productid"] == x, "productname"].values[0]
        )

    # Lookups automáticos del precio y costo vigentes para el producto seleccionado
    default_price = 0.0
    matched_price = prices_df.loc[prices_df["productid"] == selected_product_id, "price"]
    if not matched_price.empty:
        default_price = float(matched_price.values[0])

    default_cost = 0.0
    matched_cost = costs_df.loc[costs_df["productid"] == selected_product_id, "cost"]
    if not matched_cost.empty:
        default_cost = float(matched_cost.values[0])

    with p_col2:
        quantity = st.number_input("Qty", min_value=1, value=1)
    with p_col3:
        price_applied = st.number_input(
            "Unit Price",  
            value=default_price, 
            key=f"price_{selected_product_id}"
        )
    with p_col4:
        cost_applied = st.number_input(
            "Unit Cost", 
            value=default_cost, 
            key=f"cost_{selected_product_id}"
        )

    c_btn1, c_btn2 = st.columns([1, 5])
    with c_btn1:
        if st.button("➕ Add Item", use_container_width=True):
            prod_name = products_df.loc[products_df["productid"] == selected_product_id, "productname"].values[0]
            st.session_state.cart.append({
                "productid": selected_product_id,
                "product": prod_name,
                "quantity": quantity,
                "priceapplied": price_applied,
                "costapplied": cost_applied,
                "subtotal": quantity * price_applied
            })
            st.rerun()

    with c_btn2:
        if st.session_state.cart and st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

    # 6. Display Cart & Final Submission
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df[["product", "quantity", "priceapplied", "costapplied", "subtotal"]], use_container_width=True, hide_index=True)

        order_total = cart_df["subtotal"].sum() * ((100.0 - discount) / 100.0)
        st.write(f"**Total Payable (after {discount}% discount):** `${order_total:,.2f}`")

        if st.button("✅ Confirm & Record Order", type="primary", use_container_width=True):
            if not customer_name.strip():
                st.error("Please enter a valid Customer Name before recording.")
            else:
                try:
                    formatted_date = order_date.strftime("%Y-%m-%d")
                    with conn.session as s:
                        # 1. Insert header into Orders table
                        s.execute(
                            text("""
                                INSERT INTO Orders (OrderID, OrderNumber, Date, CustomerName, Employee, Contacto, Address, Discount, Regular, Category)
                                VALUES (:order_id, :order_num, :date, :customer, :employee, :contact, :address, :discount, :regular, :category)
                            """),
                            {
                                "order_id": next_order_id,
                                "order_num": next_order_num,
                                "date": formatted_date,
                                "customer": customer_name.strip(),
                                "employee": employee_id,
                                "contact": contact_id,
                                "address": shop_id,
                                "discount": discount,
                                "regular": 0 if is_regular else 1,
                                "category": category_id
                            }
                        )

                        # 2. Loop through cart items and insert each into OrderDetails
                        for item in st.session_state.cart:
                            s.execute(
                                text("""
                                    INSERT INTO OrderDetails (OrderID, ProductId, Quantity, Date, PriceApplied, CostApplied)
                                    VALUES (:order_id, :prod_id, :quantity, :date, :price, :cost)
                                """),
                                {
                                    "order_id": next_order_id,
                                    "prod_id": item["productid"],
                                    "quantity": item["quantity"],
                                    "date": formatted_date,
                                    "price": item["priceapplied"],
                                    "cost": item["costapplied"]
                                }
                            )
                        
                        s.commit()

                    st.session_state.cart = []
                    st.success(f"Order {next_order_id} recorded successfully with {len(cart_df)} items!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to record sale: {e}")
    else:
        st.info("Your order is empty. Select a product and click 'Add Item' above.")

# --- INVENTORY VIEW ---
elif vista_radio == "Inventory":

    from sqlalchemy import text
    from datetime import date
    import pandas as pd

    st.title("Inventory Management")
    st.write("Live stock tracking across all locations and product management.")
    st.markdown("-----")

    # 1. Query para calcular stock por producto y por sucursal
    stock_query = """
    WITH Intake AS (
        SELECT 
            d.productid,
            m.address AS shopid,
            SUM(d.amount) AS totalproduced
        FROM inventorydetails d
        JOIN maininventory m ON m.inventoryid = d.inventoryid
        WHERE d.orderid IS NULL
        GROUP BY d.productid, m.address
    ),
    Outflow AS (
        SELECT 
            od.productid,
            o.address AS shopid,
            SUM(od.quantity) AS totalsold
        FROM orderdetails od
        JOIN orders o ON o.orderid = od.orderid
        GROUP BY od.productid, o.address
    )
    SELECT 
        p.productid ,
        p.productname,
        s.name AS "location",
        COALESCE(i.totalproduced, 0) - COALESCE(o.totalsold, 0) AS "availablestock"
    FROM products p
    CROSS JOIN shops s
    LEFT JOIN Intake i ON i.productid = p.productid AND i.shopid = s.id
    LEFT JOIN Outflow o ON o.productid = p.productid AND o.shopid = s.id
    ORDER BY p.productid ASC, s.name ASC;
    """
    df_raw = conn.query(stock_query, ttl=0)

    # 2. Construcción de la Pivot Table
    if not df_raw.empty:
        # Pivotear las sucursales a columnas individuales
        df_pivot = df_raw.pivot_table(
            index=["productid", "productname"],
            columns="location",
            values="availablestock",
            fill_value=0
        ).reset_index()

        # Quitar el nombre del eje de columnas que deja el pivot
        df_pivot.columns.name = None

        # Identificar las columnas dinámicas de sucursales (todas excepto ID y Nombre)
        shop_columns = [col for col in df_pivot.columns if col not in ["productid", "productname"]]

        # Calcular el total global sumando las sucursales
        df_pivot["Total Available"] = df_pivot[shop_columns].sum(axis=1)

        # Reordenar columnas: ProductId, ProductName, Total Available, [Sucursales...]
        ordered_cols = ["productid", "productname", "Total Available"] + shop_columns
        df_display = df_pivot[ordered_cols].copy()

        # 3. Métricas generales
        col_m1, col_m2 = st.columns(2)
        total_units = int(df_display["Total Available"].sum())
        low_stock_count = int((df_display["Total Available"] <= 5).sum())

        with col_m1:
            st.metric("Total Units in All Shops", f"{total_units:,}")
        with col_m2:
            st.metric("Low Stock Items (≤ 5 units)", low_stock_count, delta_color="inverse")

        # Buscador por texto
        search_prod = st.text_input("🔍 Search by product name or ID:", "")
        if search_prod:
            df_display = df_display[
                df_display["productname"].str.contains(search_prod, case=False, na=False) |
                df_display["productid"].astype(str).str.contains(search_prod, na=False)
            ]

        # Configuración de columnas para formatear números como enteros
        col_configs = {
            "productid": "ID",
            "productname": "Product Name",
            "Total Available": st.column_config.NumberColumn("Total Available", format="%d units")
        }
        for shop in shop_columns:
            col_configs[shop] = st.column_config.NumberColumn(shop, format="%d units")

        df_display = df_display[["productname","Frias Silva","Las Quintas","Fabrica - Embolsado","Fabrica - Sin Embolsar"]]

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config=col_configs
        )
    else:
        st.info("No stock data found.")

    st.markdown("---")

    # 4. Formulario de Alta de Producto usando CurrentPrice y CurrentCost directamente
    with st.expander("➕ Register New Product", expanded=False):
        last_prod = conn.query("SELECT ProductId FROM Products ORDER BY ProductId DESC LIMIT 1;", ttl=0)
        next_prod_id = int(last_prod.iloc[0]["productid"]) + 1 if not last_prod.empty else 1

        with st.form("new_product_form", clear_on_submit=True):
            st.subheader(f"New Product Entry (ID: `{next_prod_id}`)")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                prod_name = st.text_input("Product Name", placeholder="e.g. Wireless Mouse X1")
                image_url = st.text_input("Image URL / Path", placeholder="e.g. https://... or local path")
            
            with f_col2:
                current_price = st.number_input("Selling Price (CurrentPrice)", min_value=0.0, value=1000.0, step=100.0)
                current_cost = st.number_input("Cost (CurrentCost)", min_value=0.0, value=500.0, step=100.0)

            submit_product = st.form_submit_button("Save Product", use_container_width=True)

        if submit_product:
            if not prod_name.strip():
                st.error("Please enter a valid product name.")
            else:
                try:
                    with conn.session as s:
                        s.execute(
                            text("""
                                INSERT INTO Products (ProductId, ProductName, Image, CurrentPrice, CurrentCost)
                                VALUES (:id, :name, :image, :price, :cost)
                            """),
                            {
                                "id": next_prod_id,
                                "name": prod_name.strip(),
                                "image": image_url.strip(),
                                "price": current_price,
                                "cost": current_cost
                            }
                        )
                        s.commit()

                    st.success(f"Product '{prod_name}' (ID: {next_prod_id}) added successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error registering product: {e}")

    # 3. Visualizar Catálogo Actual
    st.subheader("Current Products")
    
    # Query que trae los productos con su precio y costo vigente (EndDate IS NULL o el más reciente)
    catalog_query = """
    SELECT 
        p.productid,
        p.productname,
        pl.price,
        cl.cost
    FROM Products p
    inner join pricelogs pl on pl.productid = p.productid 
    inner join costlogs cl on cl.productid = p.productid
    ORDER BY ProductId asc;
    """
    catalog_df = conn.query(catalog_query, ttl=0)

    # Buscador de productos
    search_term = st.text_input("🔍 Search product by name or ID:", "")
    if search_term:
        catalog_df = catalog_df[
            catalog_df["ProductName"].str.contains(search_term, case=False, na=False) |
            catalog_df["ProductId"].astype(str).str.contains(search_term, na=False)
        ]

    st.dataframe(catalog_df, use_container_width=True, hide_index=True)

# --- PRODUCTION VIEW ---
elif vista_radio == "Production":
    from sqlalchemy import text
    from datetime import date
    import pandas as pd

    st.title("Production Lifecycle & Dispatch")
    st.write("Track manufacturing stages: Unbagged ➔ Bagged ➔ Shop Transfer.")
    st.markdown("-----")

    # Lookups
    products_df = conn.query("SELECT ProductId, ProductName FROM Products ORDER BY ProductName ASC;", ttl=0)
    shops_df = conn.query("SELECT ID, Name FROM Shops ORDER BY ID ASC;", ttl=0)

    tab1, tab2, tab3 = st.tabs([
        "🟡 1. Fábrica - Sin Embolsar", 
        "🔵 2. Fábrica - Embolsado (Listo)", 
        "🟢 3. Historial de Transferencias"
    ])

    # -------------------------------------------------------------
    # ETAPA 1: REGISTRO Y GESTIÓN DE LOTES SIN EMBOLSAR
    # -------------------------------------------------------------
    with tab1:
        st.subheader("Elaboración: Entrada de Producción")
        
        with st.expander("➕ Crear Nuevo Lote (Sin Embolsar)", expanded=True):
            with st.form("create_batch_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    prod_date = st.date_input("Fecha de Elaboración", value=date.today())
                    sel_prod_id = st.selectbox(
                        "Producto Elaborado",
                        options=sorted(products_df["productid"].tolist()),
                        format_func=lambda x: products_df.loc[products_df["productid"] == x, "productname"].values[0]
                    )
                with c2:
                    qty = st.number_input("Cantidad de Unidades", min_value=1, step=1, value=50)
                    batch_notes = st.text_input("Notas de Producción / Turno", placeholder="e.g. Turno Mañana - Horno 2")

                submit_batch = st.form_submit_button("Guardar en Fábrica (Sin Embolsar)", use_container_width=True)

            if submit_batch:
                try:
                    with conn.session as s:
                        s.execute(
                            text("""
                                INSERT INTO ProductionBatches (DateCreated, ProductID, Quantity, Status, Notes)
                                VALUES (:dt, :prod, :qty, 'Sin Embolsar', :notes)
                            """),
                            {
                                "dt": prod_date.strftime("%Y-%m-%d"),
                                "prod": sel_prod_id,
                                "qty": int(qty),
                                "notes": batch_notes.strip()
                            }
                        )
                        s.commit()
                    st.success("¡Lote registrado como 'Sin Embolsar' exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar lote: {e}")

        st.markdown("#### Lotes en Espera de Embolsado")
        unbagged_df = conn.query("""
            SELECT 
                b.batchid,
                b.datecreated AS Fecha,
                p.productname AS Producto,
                b.quantity AS Cantidad,
                b.notes AS Notas
            FROM ProductionBatches b
            JOIN Products p ON p.productid = b.productid
            WHERE b.Status = 'Sin Embolsar'
            ORDER BY b.BatchID ASC;
        """, ttl=0)

        if not unbagged_df.empty:
            for _, row in unbagged_df.iterrows():
                with st.container():
                    col_info, col_qty, col_btn = st.columns([3, 1.5, 1])
                    
                    with col_info:
                        st.write(f"**Lote #{row['batchid']}** | {row['producto']} | *Fecha:* {row['fecha']}")
                        st.caption(f"Notas: {row['notas'] or 'Sin notas'}")
                    
                    with col_qty:
                        # Campo editable con teclado para corregir unidades
                        new_qty = st.number_input(
                            "Unidades",
                            min_value=1,
                            step=1,
                            value=int(row['cantidad']),
                            key=f"qty_unbagged_{row['batchid']}"
                        )
                        # Si el usuario modificó el valor numérico, se muestra el botón para guardar el ajuste
                        if new_qty != int(row['cantidad']):
                            if st.button("💾 Guardar cant.", key=f"btn_save_qty_{row['batchid']}", use_container_width=True):
                                try:
                                    with conn.session as s:
                                        s.execute(
                                            text("UPDATE ProductionBatches SET Quantity = :q WHERE BatchID = :id"),
                                            {"q": int(new_qty), "id": row["batchid"]}
                                        )
                                        s.commit()
                                    st.success(f"Cantidad del Lote #{row['batchid']} actualizada a {new_qty}.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al actualizar: {e}")

                    with col_btn:
                        st.write("") # Espaciador vertical para alinear con el botón
                        if st.button(f"Embolsar ✅", key=f"btn_bag_{row['batchid']}", use_container_width=True):
                            with conn.session as s:
                                s.execute(
                                    text("""
                                        UPDATE ProductionBatches 
                                        SET Status = 'Embolsado', DateBagged = :dt, Quantity = :qty
                                        WHERE batchid = :id
                                    """),
                                    {
                                        "id": row["batchid"], 
                                        "dt": date.today().strftime("%Y-%m-%d"),
                                        "qty": int(new_qty)  # Asegura pasar la cantidad visible actualmente
                                    }
                                )
                                s.commit()
                            st.success(f"Lote #{row['batchid']} pasado a Embolsado.")
                            st.rerun()
                st.divider()
        else:
            st.info("No hay lotes pendientes de embolsar en fábrica.")

    # -------------------------------------------------------------
    # ETAPA 2: ASIGNACIÓN Y TRANSFERENCIA A SUCURSALES (EMBOLSADO)
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Stock Embolsado en Fábrica (Listo para Despacho)")
        
        bagged_df = conn.query("""
            SELECT 
                b.batchid,
                b.datecreated,
                b.datebagged,
                b.productid,
                p.productname AS Producto,
                b.quantity AS Cantidad
            FROM ProductionBatches b
            JOIN Products p ON p.productid = b.productid
            WHERE b.status = 'Embolsado'
            ORDER BY b.batchid ASC;
        """, ttl=0)

        if not bagged_df.empty:
            for _, row in bagged_df.iterrows():
                with st.container():
                    col_b_info, col_b_qty, col_b_shop, col_b_action = st.columns([2.5, 1.3, 2, 1.2])
                    with col_b_info:
                        st.markdown(f"**Lote #{row['batchid']}**: {row['producto']}")
                        st.caption(f"Embolsado el: {row['datebagged']}")
                    
                    with col_b_qty:
                        # Permite ajustar cantidad también en embolsado si hubo mermas/roturas de bolsas
                        new_bagged_qty = st.number_input(
                            "Unidades",
                            min_value=1,
                            step=1,
                            value=int(row['cantidad']),
                            key=f"qty_bagged_{row['batchid']}"
                        )
                        if new_bagged_qty != int(row['cantidad']):
                            if st.button("💾 Guardar", key=f"btn_save_bag_qty_{row['batchid']}", use_container_width=True):
                                try:
                                    with conn.session as s:
                                        s.execute(
                                            text("UPDATE ProductionBatches SET Quantity = :q WHERE BatchID = :id"),
                                            {"q": int(new_bagged_qty), "id": row["batchid"]}
                                        )
                                        s.commit()
                                    st.success(f"Lote #{row['batchid']} actualizado a {new_bagged_qty} u.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al actualizar: {e}")

                    with col_b_shop:
                        target_shop = st.selectbox(
                            "Destino",
                            options=shops_df["id"].tolist(),
                            format_func=lambda x: shops_df.loc[shops_df["id"] == x, "name"].values[0],
                            key=f"shop_sel_{row['batchid']}"
                        )
                    with col_b_action:
                        st.write("")
                        if st.button("Transferir 🚚", key=f"btn_trans_{row['batchid']}", use_container_width=True):
                            try:
                                transfer_date = date.today().strftime("%Y-%m-%d")
                                with conn.session as s:
                                    # 1. Obtener nuevo InventoryID para MainInventory
                                    max_inv = s.execute(text("SELECT MAX(InventoryID) FROM MainInventory;")).scalar()
                                    new_inv_id = (max_inv + 1) if max_inv is not None else 1

                                    # 2. Insertar en MainInventory vinculando a la tienda destino
                                    s.execute(
                                        text("""
                                            INSERT INTO MainInventory (InventoryID, DateTime, Address)
                                            VALUES (:inv_id, :dt, :address)
                                        """),
                                        {"inv_id": new_inv_id, "dt": transfer_date, "address": target_shop}
                                    )

                                    # 3. Insertar en InventoryDetails impactando el stock con la cantidad actual
                                    s.execute(
                                        text("""
                                            INSERT INTO InventoryDetails (InventoryID, OrderID, ProductID, DateTime, Amount)
                                            VALUES (:inv_id, NULL, :prod_id, :dt, :amount)
                                        """),
                                        {
                                            "inv_id": new_inv_id,
                                            "prod_id": row["productid"],
                                            "dt": transfer_date,
                                            "amount": int(new_bagged_qty)
                                        }
                                    )

                                    # 4. Actualizar estado del lote a Transferido
                                    s.execute(
                                        text("""
                                            UPDATE ProductionBatches
                                            SET Status = 'Transferido',
                                                DateTransferred = :dt,
                                                DestinationShopID = :shop,
                                                InventoryID = :inv_id,
                                                Quantity = :qty
                                            WHERE BatchID = :id
                                        """),
                                        {
                                            "dt": transfer_date,
                                            "shop": target_shop,
                                            "inv_id": new_inv_id,
                                            "qty": int(new_bagged_qty),
                                            "id": row["batchid"]
                                        }
                                    )
                                    s.commit()

                                st.success(f"Lote #{row['batchid']} ingresado al stock de la sucursal.")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error en transferencia: {e}")
                st.divider()
        else:
            st.info("No hay productos embolsados pendientes de despacho en fábrica.")

    # -------------------------------------------------------------
    # ETAPA 3: HISTORIAL DE LOTES TRANSFERIDOS
    # -------------------------------------------------------------
    with tab3:
        st.subheader("Historial de Lotes Transferidos a Tiendas")
        
        history_df = conn.query("""
            SELECT 
                b.batchid AS "Lote #",
                b.datetransferred AS "Fecha Transferencia",
                p.productname AS "Producto",
                b.quantity AS "Cantidad",
                s.name AS "Destino",
                b.inventoryid AS "Ref InventoryID"
            FROM ProductionBatches b
            JOIN Products p ON p.productid = b.productid
            JOIN Shops s ON s.id = b.destinationshopid
            WHERE b.status = 'Transferido'
            ORDER BY b.batchid DESC
            LIMIT 30;
        """, ttl=0)

        if not history_df.empty:
            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cantidad": st.column_config.NumberColumn(format="%d units")
                }
            )
        else:
            st.write("Aún no se han completado transferencias a sucursales.")