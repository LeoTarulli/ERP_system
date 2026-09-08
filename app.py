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
        ["Dashboard", "Orders", "Inventory"],
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
    st.write("Register a new sale in the ERP system.")
    st.markdown("-----")

    # 1. Fetch lookup data using exact schema columns
    products_df = conn.query("SELECT ProductId, ProductName FROM Products;", ttl=0)
    contacts_df = conn.query("SELECT RedID, RedName FROM Contact;", ttl=0)
    categories_df = conn.query("SELECT CategoryID, Category FROM Categories;", ttl=0)

    # 2. Determine Next OrderID and OrderNumber
    orders_head = conn.query(
        "SELECT OrderID, OrderNumber FROM Orders ORDER BY length(OrderID) DESC, OrderID DESC LIMIT 1;", 
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

    # 3. Registration Form
    with st.form("sales_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            st.caption("Customer & Order Details")
            customer_name = st.text_input("Customer Name", placeholder="e.g. Maria Gonzalez")
            order_date = st.date_input("Order Date", value=date.today())
            
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

            is_regular = st.checkbox("Is Regular Customer?")

        with col2:
            st.caption("Product & Financial Details")
            selected_product_id = st.selectbox(
                "Product",
                options=products_df["ProductId"].tolist(),
                format_func=lambda x: products_df.loc[products_df["ProductId"] == x, "ProductName"].values[0]
            )

            quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            price_applied = st.number_input("Price Applied (Unit)", min_value=0.0, value=1000.0, step=100.0)
            cost_applied = st.number_input("Cost Applied (Unit)", min_value=0.0, value=500.0, step=100.0)
            discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0)

        submitted = st.form_submit_button("Record Sale", use_container_width=True)

    # 4. Insert into SQLite via conn.session
    if submitted:
        if not customer_name.strip():
            st.error("Please enter a valid Customer Name.")
        else:
            try:
                formatted_date = order_date.strftime("%Y-%m-%d")
                with conn.session as s:
                    # Insert into Orders table
                    s.execute(
                        text("""
                            INSERT INTO Orders (OrderID, OrderNumber, Date, CustomerName, Discount, Regular, Category)
                            VALUES (:order_id, :order_num, :date, :customer, :discount, :regular, :category)
                        """),
                        {
                            "order_id": next_order_id,
                            "order_num": next_order_num,
                            "date": formatted_date,
                            "customer": customer_name.strip(),
                            "discount": discount,
                            "regular": 0 if is_regular else 1,
                            "category": category_id
                        }
                    )

                    # Insert into OrderDetails table
                    s.execute(
                        text("""
                            INSERT INTO OrderDetails (OrderID, ProductId, Quantity, Date, PriceApplied, CostApplied)
                            VALUES (:order_id, :prod_id, :quantity, :date, :price, :cost)
                        """),
                        {
                            "order_id": next_order_id,
                            "prod_id": selected_product_id,
                            "quantity": quantity,
                            "date": formatted_date,
                            "price": price_applied,
                            "cost": cost_applied
                        }
                    )
                    s.commit()

                st.success(f"Order {next_order_id} recorded successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to record sale: {e}")

# --- INVENTORY VIEW ---
elif vista_radio == "Inventory":
    st.title("Inventory Tracking")
    st.write("Section under construction.")
