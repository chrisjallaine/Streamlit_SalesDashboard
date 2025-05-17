import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import calendar
import numpy as np


# MUGOT, CHRIS JALLAINE
# Page configuration
st.set_page_config(
    page_title="Executive Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    /* Overall app styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .css-1avcm0n {
        background-color: #222222;
        border-radius: 10px;
    }
    
    /* Dashboard title */
    .dashboard-title {
        color: #1E3A8A;
        text-align: center;
        font-weight: 600;
        font-size: 2.5rem;
        margin-bottom: 20px;
        padding: 10px;
        background: linear-gradient(90deg, #ffffff, #f3f4f6, #ffffff);
        border-radius: 10px;
    }
    
    /* Metrics container */
    .metrics-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Chart container */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Section headers */
    .section-header {
        color: #1E3A8A;
        font-weight: 600;
        font-size: 1.5rem;
        margin-bottom: 15px;
    }
    
    /* Filter section */
    .filter-section {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* Data table */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    .dataframe th {
        background-color: #1E3A8A;
        color: white;
        padding: 12px;
        text-align: left;
    }
    .dataframe td {
        padding: 10px;
        border-bottom: 1px solid #e5e7eb;
    }
    .dataframe tr:hover {
        background-color: #f3f4f6;
    }
</style>
""", unsafe_allow_html=True)

# Connect to Database 
@st.cache_resource
def init_connection():
    """Create a connection to the PostgreSQL database"""
    try: #this is my database link sir.
        db_url = "postgresql://whiplash_user:6EoohkmGo5ziA3qJMhsBYHl5P6yS9UKL@dpg-d0amg66uk2gs73busq9g-a.oregon-postgres.render.com/whiplash"
        return create_engine(db_url, client_encoding='utf8')
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Query data 
@st.cache_data(ttl=600)
def get_data():
    """Fetch data from the database"""
    try:
        with engine.connect() as conn:
            query = text('SELECT * FROM "data_ETL";')
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Data fetching error: {e}")
        return pd.DataFrame()

# Connect to database
engine = init_connection()

st.markdown('<div class="dashboard-title">EXECUTIVE SALES DASHBOARD</div>', unsafe_allow_html=True)

# Fetch data
with st.spinner("Loading data from database..."):
    sales_data = get_data()

# Data preprocessing
if not sales_data.empty:
    # Convert data types
    sales_data['Order Date'] = pd.to_datetime(sales_data['Order Date'])
    sales_data['Price Each'] = pd.to_numeric(sales_data['Price Each'], errors='coerce')
    sales_data['Quantity Ordered'] = pd.to_numeric(sales_data['Quantity Ordered'], errors='coerce')
    
    # Calculate total sales
    sales_data['Total Sale'] = sales_data['Price Each'] * sales_data['Quantity Ordered']
    
    # Extract location information from addresses
    sales_data['City'] = sales_data['Purchase Address'].str.extract(r', ([^,]+),')
    
    # Extract month and hour
    sales_data['Month'] = sales_data['Order Date'].dt.month
    sales_data['Month Name'] = sales_data['Order Date'].dt.month_name()
    sales_data['Hour'] = sales_data['Order Date'].dt.hour
    sales_data['Day'] = sales_data['Order Date'].dt.day_name()
    
    # Initial date range for filtering
    min_date = sales_data['Order Date'].min().date()
    max_date = sales_data['Order Date'].max().date()
    
    # Sidebar for filters
    st.sidebar.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Filters</h2>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        # Date range filter
        date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Handle single date selection
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = date_range[0]
            end_date = date_range[0]
        
        # Convert to datetime for filtering
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        # Product filter
        all_products = sorted(sales_data['Product'].unique())
        selected_products = st.multiselect("Select Products", all_products, default=all_products[:5] if len(all_products) > 5 else all_products)
        
        # City filter
        all_cities = sorted(sales_data['City'].dropna().unique())
        selected_cities = st.multiselect("Select Cities", all_cities, default=all_cities[:3] if len(all_cities) > 3 else all_cities)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export options
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Export Options</h2>", unsafe_allow_html=True)
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        # Function to convert dataframe to CSV
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')
        
        if st.button("Export Filtered Data (CSV)"):
            filtered_csv = convert_df_to_csv(filtered_data)
            st.download_button(
                label="Download CSV",
                data=filtered_csv,
                file_name="sales_data_export.csv",
                mime="text/csv",
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter data based on selections
    filtered_data = sales_data[
        (sales_data['Order Date'] >= start_date) & 
        (sales_data['Order Date'] <= end_date)
    ]
    
    # Apply product and city filters if selected
    if selected_products:
        filtered_data = filtered_data[filtered_data['Product'].isin(selected_products)]
    
    if selected_cities:
        filtered_data = filtered_data[filtered_data['City'].isin(selected_cities)]
    
    # Check if filtered data is not empty
    if not filtered_data.empty:
        # Main dashboard content
        # Key metrics in the first row with 4 columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
            total_revenue = filtered_data['Total Sale'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
            total_orders = filtered_data['Order ID'].nunique()
            st.metric("Total Orders", f"{total_orders:,}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            st.metric("Average Order Value", f"${avg_order_value:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col4:
            st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
            total_units = filtered_data['Quantity Ordered'].sum()
            st.metric("Total Units Sold", f"{total_units:,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Second row - Sales trends and product performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Monthly Sales Trend</div>', unsafe_allow_html=True)
            
            # Monthly sales aggregation
            monthly_sales = filtered_data.groupby('Month Name')['Total Sale'].sum().reset_index()
            
            # Custom sort for months
            month_order = {month: i for i, month in enumerate(calendar.month_name[1:])}
            monthly_sales['Month Order'] = monthly_sales['Month Name'].map(month_order)
            monthly_sales = monthly_sales.sort_values('Month Order')
            
            # Create monthly trend chart
            fig = px.line(
                monthly_sales, 
                x='Month Name', 
                y='Total Sale',
                markers=True,
                line_shape='linear',
                labels={'Month Name': 'Month', 'Total Sale': 'Revenue ($)'}
            )
            
            fig.update_traces(line=dict(color='#1E3A8A', width=3))
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Revenue ($)",
                yaxis_tickformat="$,.0f",
                xaxis={'categoryorder': 'array', 'categoryarray': list(calendar.month_name)[1:]},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=True,
                yaxis_gridcolor='rgba(200,200,200,0.2)'
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Top Products by Revenue</div>', unsafe_allow_html=True)
            
            # Product sales aggregation
            product_sales = filtered_data.groupby('Product')['Total Sale'].sum().reset_index()
            top_products = product_sales.sort_values('Total Sale', ascending=False).head(10)
            
            # Create product bar chart
            fig = px.bar(
                top_products, 
                x='Total Sale', 
                y='Product',
                orientation='h',
                labels={'Total Sale': 'Revenue ($)', 'Product': ''},
                color_discrete_sequence=['#1E3A8A']
            )
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="Revenue ($)",
                yaxis_title="",
                xaxis_tickformat="$,.0f",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=True,
                xaxis_gridcolor='rgba(200,200,200,0.2)',
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Third row - City & Hour Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Sales by City</div>', unsafe_allow_html=True)
            
            # City sales aggregation
            city_sales = filtered_data.groupby('City')['Total Sale'].sum().reset_index()
            city_sales = city_sales.sort_values('Total Sale', ascending=False)
            
            # Create city pie chart
            fig = px.pie(
                city_sales, 
                values='Total Sale', 
                names='City',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                legend_title_text='',
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1.1),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Orders by Hour of Day</div>', unsafe_allow_html=True)
            
            # Hour analysis
            hourly_orders = filtered_data.groupby('Hour')['Order ID'].count().reset_index()
            
            # Create hourly orders line chart
            fig = px.line(
                hourly_orders, 
                x='Hour', 
                y='Order ID',
                markers=True,
                line_shape='spline',
                labels={'Hour': 'Hour of Day', 'Order ID': 'Number of Orders'}
            )
            
            fig.update_traces(line=dict(color='#1E3A8A', width=3))
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="Hour of Day",
                yaxis_title="Number of Orders",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=True,
                yaxis_gridcolor='rgba(200,200,200,0.2)',
                xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Fourth row - Day of Week analysis and data table
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Sales by Day of Week</div>', unsafe_allow_html=True)
            
            # Day of week analysis
            days_order = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}
            day_sales = filtered_data.groupby('Day')['Total Sale'].sum().reset_index()
            day_sales['Day Order'] = day_sales['Day'].map(days_order)
            day_sales = day_sales.sort_values('Day Order')
            
            # Create day of week bar chart
            fig = px.bar(
                day_sales, 
                x='Day', 
                y='Total Sale',
                labels={'Day': '', 'Total Sale': 'Revenue ($)'},
                color_discrete_sequence=['#1E3A8A']
            )
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Revenue ($)",
                yaxis_tickformat="$,.0f",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=True,
                yaxis_gridcolor='rgba(200,200,200,0.2)',
                xaxis={'categoryorder': 'array', 'categoryarray': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Average Order Value by Product</div>', unsafe_allow_html=True)
            
            # Average order value by product
            product_aov = filtered_data.groupby('Product').agg(
                Orders=('Order ID', 'nunique'),
                Revenue=('Total Sale', 'sum')
            ).reset_index()
            
            product_aov['AOV'] = product_aov['Revenue'] / product_aov['Orders']
            product_aov = product_aov.sort_values('AOV', ascending=False).head(10)
            
            # Create AOV chart
            fig = px.bar(
                product_aov, 
                x='Product', 
                y='AOV',
                labels={'Product': '', 'AOV': 'Average Order Value ($)'},
                color_discrete_sequence=['#1E3A8A']
            )
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Average Order Value ($)",
                yaxis_tickformat="$,.2f",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=True,
                yaxis_gridcolor='rgba(200,200,200,0.2)',
                xaxis={'tickangle': 45}
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Data table with latest orders
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Recent Orders</div>', unsafe_allow_html=True)
        
        # Get the latest orders
        latest_orders = filtered_data.sort_values('Order Date', ascending=False).head(10)
        display_cols = ['Order ID', 'Product', 'Quantity Ordered', 'Price Each', 'Total Sale', 'Order Date', 'City']
        formatted_orders = latest_orders[display_cols].copy()
        
        # Format the table data
        formatted_orders['Total Sale'] = formatted_orders['Total Sale'].map('${:,.2f}'.format)
        formatted_orders['Price Each'] = formatted_orders['Price Each'].map('${:,.2f}'.format)
        formatted_orders['Order Date'] = formatted_orders['Order Date'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Display the table with custom styling
        st.dataframe(formatted_orders, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.warning("No data available for the selected filters. Please adjust your selection.")
else:
    st.error("Failed to fetch data from the database. Please check your connection and try again.")

# Footer with dashboard information
st.markdown("""
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; font-size: 0.8rem; color: #666;'>
    <p>Executive Sales Dashboard | Last updated: {}</p>
    <p>Data source: PostgreSQL database "whiplash" | Table: data_ETL</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)