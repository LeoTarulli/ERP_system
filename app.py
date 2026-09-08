import pandas as pd
import numpy as np

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Connect to the SQLite database
conn = st.connection("erp_db", type="sql", url="sqlite:///erp_system.db")


# Page config
st.set_page_config(
    page_title="Standard ERP System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    vista_radio = st.radio(
        "Sección:",
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
    select * from sales_frame order by Date desc;""", ttl=0)
    df.rename(columns={"TotalIncome": "Total Income", "Totalcost": "Total Cost"}, inplace=True)
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

    df_totalorders = (df_orders.groupby('MonthName')['OrderID'].nunique())

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
                             line=dict(color="#29b5e8", width=5),
                             textposition="top right",
                             textfont=dict(size=15))

    st.plotly_chart(line_chart, use_container_width=True)

# --- ORDERS VIEW ---
elif vista_radio == "Orders":
    from sqlalchemy import text
    from datetime import date

    st.title("Orders Management")
    st.write("Register a new sale with multiple items in the ERP system.")
    st.markdown("-----")

    # 1. Initialize shopping cart in session state
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # 2. Fetch lookup data
    products_df = conn.query("SELECT ProductId, ProductName FROM Products;", ttl=0)
    contacts_df = conn.query("SELECT RedID, RedName FROM Contact;", ttl=0)
    categories_df = conn.query("SELECT CategoryID, Category FROM Categories;", ttl=0)
    shops_df = conn.query("SELECT ID, Name FROM Shops;", ttl=0)
    employees_df = conn.query("SELECT EmployeeID, Name FROM Employees;", ttl=0)

    # 3. Determine Next OrderID and OrderNumber
    orders_head = conn.query(
        "SELECT OrderID, OrderNumber FROM Orders ORDER BY OrderNumber DESC LIMIT 1;", 
        ttl=0
    )
    if not orders_head.empty and orders_head.iloc[0]["OrderID"]: 
        last_id = orders_head.iloc[0]["OrderID"]
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
            options=contacts_df["RedID"].tolist(),
            format_func=lambda x: contacts_df.loc[contacts_df["RedID"] == x, "RedName"].values[0]
        )
        category_id = st.selectbox(
            "Category",
            options=categories_df["CategoryID"].tolist(),
            format_func=lambda x: categories_df.loc[categories_df["CategoryID"] == x, "Category"].values[0]
        )
    with col3:
        shop_id = st.selectbox(
            "Shop",
            options=shops_df["ID"].tolist(),
            format_func=lambda x: shops_df.loc[shops_df["ID"] == x, "Name"].values[0]
        )
        employee_id = st.selectbox(
            "Employee",
            options=employees_df["EmployeeID"].tolist(),
            format_func=lambda x: employees_df.loc[employees_df["EmployeeID"] == x, "Name"].values[0]
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
            options=products_df["ProductId"].tolist(),
            format_func=lambda x: products_df.loc[products_df["ProductId"] == x, "ProductName"].values[0]
        )
    with p_col2:
        quantity = st.number_input("Qty", min_value=1, step=1, value=1)
    with p_col3:
        price_applied = st.number_input("Unit Price", min_value=0.0, value=1000.0, step=100.0)
    with p_col4:
        cost_applied = st.number_input("Unit Cost", min_value=0.0, value=500.0, step=100.0)

    c_btn1, c_btn2 = st.columns([1, 5])
    with c_btn1:
        if st.button("➕ Add Item", use_container_width=True):
            prod_name = products_df.loc[products_df["ProductId"] == selected_product_id, "ProductName"].values[0]
            st.session_state.cart.append({
                "ProductId": selected_product_id,
                "Product": prod_name,
                "Quantity": quantity,
                "PriceApplied": price_applied,
                "CostApplied": cost_applied,
                "Subtotal": quantity * price_applied
            })
            st.rerun()

    with c_btn2:
        if st.session_state.cart and st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

    # 6. Display Cart & Final Submission
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df[["Product", "Quantity", "PriceApplied", "CostApplied", "Subtotal"]], use_container_width=True, hide_index=True)

        order_total = cart_df["Subtotal"].sum() * ((100.0 - discount) / 100.0)
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
                                    "prod_id": item["ProductId"],
                                    "quantity": item["Quantity"],
                                    "date": formatted_date,
                                    "price": item["PriceApplied"],
                                    "cost": item["CostApplied"]
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
    st.title("Current Inventory Levels")
    st.write("Live stock tracking balancing production intake against sales deductions.")
    st.markdown("-----")

    # 1. Fetch shops for location-based filtering
    shops_df = conn.query("SELECT ID, Name FROM Shops;", ttl=0)
    shop_options = ["All Locations"] + shops_df["Name"].tolist()
    
    col_filter, col_metric1, col_metric2 = st.columns([2, 1, 1])
    with col_filter:
        selected_location = st.selectbox("Filter by Location/Shop:", shop_options)

    # 2. SQL calculation of net stock
    # Intake comes from InventoryDetails; outflow comes from OrderDetails
    stock_query = """
    WITH Intake AS (
        SELECT 
            d.ProductID,
            m.Address AS ShopID,
            SUM(d.Amount) AS TotalProduced
        FROM InventoryDetails d
        JOIN MainInventory m ON m."InventoryID" = d."InventoryID"
        WHERE d.OrderID IS NULL
        GROUP BY d.ProductID, m.Address
    ),
    Outflow AS (
        SELECT 
            od.ProductId,
            o.Address AS ShopID,
            SUM(od.Quantity) AS TotalSold
        FROM OrderDetails od
        JOIN Orders o ON o.OrderID = od.OrderID
        GROUP BY od.ProductId, o.Address
    )
    SELECT 
        p.ProductId,
        p.ProductName,
        s.Name AS Location,
        COALESCE(i.TotalProduced, 0) AS Produced,
        COALESCE(o.TotalSold, 0) AS Sold,
        COALESCE(i.TotalProduced, 0) - COALESCE(o.TotalSold, 0) AS AvailableStock
    FROM Products p
    CROSS JOIN Shops s
    LEFT JOIN Intake i ON i.ProductID = p.ProductId AND i.ShopID = s.ID
    LEFT JOIN Outflow o ON o.ProductId = p.ProductId AND o.ShopID = s.ID
    ORDER BY p.ProductId ASC, s.Name ASC;
    """

    df_stock = conn.query(stock_query, ttl=0)

    # 3. Apply location filter
    if selected_location != "All Locations":
        df_display = df_stock[df_stock["Location"] == selected_location].copy()
    else:
        # Aggregate across all shops if viewing overall stock
        df_display = (
            df_stock.groupby(["ProductId", "ProductName"], as_index=False)
            .agg({
                "Produced": "sum",
                "Sold": "sum",
                "AvailableStock": "sum"
            })
        )

    # 4. Overview KPI Cards
    total_skus = df_display["ProductId"].nunique()
    total_units_available = int(df_display["AvailableStock"].sum())
    low_stock_count = int((df_display["AvailableStock"] <= 5).sum())

    with col_metric1:
        st.metric("Total Units Available", f"{total_units_available:,}")
    with col_metric2:
        st.metric("Low Stock Alerts (≤ 5)", low_stock_count, delta_color="inverse")

    st.markdown("### Stock Breakdown")

    # Search bar
    search_prod = st.text_input("🔍 Search by product name or ID:", "")
    if search_prod:
        df_display = df_display[
            df_display["ProductName"].str.contains(search_prod, case=False, na=False) |
            df_display["ProductId"].astype(str).str.contains(search_prod, na=False)
        ]

    # Format and present data
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ProductId": "ID",
            "ProductName": "Product Name",
            "Produced": st.column_config.NumberColumn("Total Produced", format="%d units"),
            "Sold": st.column_config.NumberColumn("Total Sold", format="%d units"),
            "AvailableStock": st.column_config.NumberColumn("In Stock", format="%d units"),
        }
    )
    from sqlalchemy import text
    from datetime import date

    st.title("Inventory & Product Catalog")
    st.write("Manage your catalog, add new products, and track base pricing.")
    st.markdown("-----")

    # 1. Calcular el siguiente ProductId disponible
    last_prod = conn.query("SELECT ProductId FROM Products ORDER BY ProductId DESC LIMIT 1;", ttl=0)
    next_prod_id = int(last_prod.iloc[0]["ProductId"]) + 1 if not last_prod.empty else 1

    # 2. Formulario para dar de alta un producto
    with st.expander("➕ Register New Product", expanded=False):
        with st.form("new_product_form", clear_on_submit=True):
            st.subheader(f"New Product ID: `{next_prod_id}`")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                prod_name = st.text_input("Product Name", placeholder="e.g. Wireless Mouse X1")
                image_url = st.text_input("Image URL / Path", placeholder="e.g. https://... or local path")
            
            with f_col2:
                initial_price = st.number_input("Base Selling Price", min_value=0.0, value=1000.0, step=100.0)
                initial_cost = st.number_input("Base Cost", min_value=0.0, value=500.0, step=100.0)
                log_date = st.date_input("Effective Date", value=date.today())

            submit_product = st.form_submit_button("Save Product", use_container_width=True)

        if submit_product:
            if not prod_name.strip():
                st.error("Please enter a valid product name.")
            else:
                try:
                    formatted_log_date = log_date.strftime("%Y-%m-%d")
                    with conn.session as s:
                        # Insertar en Products
                        s.execute(
                            text("""
                                INSERT INTO Products (ProductId, ProductName, Image)
                                VALUES (:id, :name, :image)
                            """),
                            {"id": next_prod_id, "name": prod_name.strip(), "image": image_url.strip()}
                        )

                        # Insertar precio base en PriceLogs
                        s.execute(
                            text("""
                                INSERT INTO PriceLogs (ProductId, StartingDate, EndDate, Price)
                                VALUES (:id, :start, NULL, :price)
                            """),
                            {"id": next_prod_id, "start": formatted_log_date, "price": str(initial_price)}
                        )

                        # Insertar costo base en CostLogs
                        s.execute(
                            text("""
                                INSERT INTO CostLogs (ProductId, StartingDate, EndDate, Cost)
                                VALUES (:id, :start, NULL, :cost)
                            """),
                            {"id": next_prod_id, "start": formatted_log_date, "cost": str(initial_cost)}
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
        p.ProductId,
        p.ProductName,
        p.Image,
        pl.Price AS CurrentPrice,
        cl.Cost AS CurrentCost
    FROM Products p
    LEFT JOIN PriceLogs pl ON pl.ProductId = p.ProductId AND (pl.EndDate IS NULL OR pl.EndDate = '')
    LEFT JOIN CostLogs cl ON cl.ProductId = p.ProductId AND (cl.EndDate IS NULL OR cl.EndDate = '')
    ORDER BY p.ProductId DESC;
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
