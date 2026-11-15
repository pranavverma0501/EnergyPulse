import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="EnergyPulse | Electricity Analytics",
    page_icon="⚡",
    layout="wide"
)

st.markdown(
    """
    <style>
        .stApp { background-color: #0b1220; }
        h1, h2, h3 { color: #e8f0fc; }
        [data-testid="stMetric"] {
            background-color: #17243a;
            border: 1px solid #263954;
            padding: 18px;
            border-radius: 12px;
        }
        [data-testid="stMetricLabel"] { color: #a9bdd8; }
        [data-testid="stMetricValue"] { color: #ffffff; }
        section[data-testid="stSidebar"] { background-color: #202633; }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar: database connection
st.sidebar.title("⚡ EnergyPulse")
st.sidebar.caption("Electricity Analytics System")
st.sidebar.divider()
st.sidebar.subheader("Database Connection")

db_host = st.sidebar.text_input("Host", value="localhost")
db_port = st.sidebar.number_input(
    "Port", min_value=1, max_value=65535, value=3306, step=1
)
db_user = st.sidebar.text_input("Username", value="root")
db_password = st.sidebar.text_input("Password", type="password")
st.sidebar.caption("Database: electricity_forecasting")


# Database helpers
@st.cache_resource
def get_connection(host, port, user, password):
    """Create a cached PyMySQL connection."""
    return pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database="electricity_forecasting",
        charset="utf8mb4",
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


@st.cache_data(ttl=60)
def load_data(query, host, port, user, password):
    """Execute a SELECT query and cache the returned rows for 60 seconds."""
    connection = get_connection(host, port, user, password)
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [item[0] for item in cursor.description]
    return pd.DataFrame(rows, columns=columns)


# Connect and load database tables
if not db_password:
    st.title("⚡ EnergyPulse")
    st.info("Enter your MySQL root password in the sidebar to connect.")
    st.stop()

try:
    connection = get_connection(db_host, db_port, db_user, db_password)
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE() AS database_name")
        active_database = cursor.fetchone()["database_name"]

    if active_database != "electricity_forecasting":
        st.error("Connected to the wrong database.")
        st.stop()

    readings = load_data(
        """
        SELECT reading_time, global_active_power
        FROM electricity_readings
        ORDER BY reading_time
        """,
        db_host, db_port, db_user, db_password
    )

    forecasts = load_data(
        """
        SELECT forecast_time, actual_power, predicted_power
        FROM forecasts
        ORDER BY forecast_time
        """,
        db_host, db_port, db_user, db_password
    )

    anomalies = load_data(
        """
        SELECT reading_time, observed_power, anomaly_score, is_anomaly
        FROM anomalies
        ORDER BY reading_time
        """,
        db_host, db_port, db_user, db_password
    )

    models = load_data(
        """
        SELECT model_name, mae, rmse, r2_score, evaluated_at
        FROM model_results
        ORDER BY mae ASC
        """,
        db_host, db_port, db_user, db_password
    )

except Exception as error:
    get_connection.clear()
    load_data.clear()
    st.error(f"Database connection or query failed: {error}")
    st.info(
        "Check that MySQL Server is running, the password is correct, "
        "and the electricity_forecasting database contains the required tables."
    )
    st.stop()


# Validate and prepare data
if readings.empty:
    st.warning("The electricity_readings table is empty. Import the hourly readings first.")
    st.stop()
if forecasts.empty:
    st.warning("The forecasts table is empty. Insert the forecast records first.")
    st.stop()
if anomalies.empty:
    st.warning("The anomalies table is empty. Insert the anomaly records first.")
    st.stop()
if models.empty:
    st.warning("The model_results table is empty. Insert the model results first.")
    st.stop()

readings["reading_time"] = pd.to_datetime(readings["reading_time"])
forecasts["forecast_time"] = pd.to_datetime(forecasts["forecast_time"])
anomalies["reading_time"] = pd.to_datetime(anomalies["reading_time"])

readings["global_active_power"] = pd.to_numeric(
    readings["global_active_power"], errors="coerce"
)
forecasts["actual_power"] = pd.to_numeric(
    forecasts["actual_power"], errors="coerce"
)
forecasts["predicted_power"] = pd.to_numeric(
    forecasts["predicted_power"], errors="coerce"
)
anomalies["is_anomaly"] = pd.to_numeric(
    anomalies["is_anomaly"], errors="coerce"
).fillna(0).astype(int)
models["mae"] = pd.to_numeric(models["mae"], errors="coerce")
models["rmse"] = pd.to_numeric(models["rmse"], errors="coerce")
models["r2_score"] = pd.to_numeric(models["r2_score"], errors="coerce")

readings = readings.dropna(subset=["reading_time", "global_active_power"])
forecasts = forecasts.dropna(
    subset=["forecast_time", "actual_power", "predicted_power"]
)
anomalies = anomalies.dropna(subset=["reading_time", "observed_power"])
models = models.dropna(subset=["model_name", "mae", "rmse", "r2_score"])

if readings.empty or forecasts.empty or anomalies.empty or models.empty:
    st.error("One or more tables have no usable records after data validation.")
    st.stop()

readings["date"] = readings["reading_time"].dt.date
readings["hour"] = readings["reading_time"].dt.hour
daily = readings.groupby("date", as_index=False)["global_active_power"].mean()
hourly = readings.groupby("hour", as_index=False)["global_active_power"].mean()

total_readings = len(readings)
total_forecasts = len(forecasts)
total_anomalies = int((anomalies["is_anomaly"] == 1).sum())
average_power = readings["global_active_power"].mean()
peak_power = readings["global_active_power"].max()


# Dashboard header and KPIs
st.title("⚡ EnergyPulse")
st.markdown(
    "### Electricity Consumption Forecasting, "
    "Anomaly Detection & Energy Monitoring System"
)
st.caption(
    f"Connected to: {active_database} | MySQL | "
    f"Readings: {total_readings:,} | Forecasts: {total_forecasts:,}"
)
st.divider()

st.subheader("System Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Readings", f"{total_readings:,}")
c2.metric("Average Power", f"{average_power:.3f} kW")
c3.metric("Peak Power", f"{peak_power:.3f} kW")
c4.metric("Anomalies Detected", f"{total_anomalies:,}")
st.divider()


# Dashboard tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Overview",
        "⚡ Energy Monitoring",
        "🔮 Forecasting",
        "🚨 Anomaly Detection",
        "🤖 Model Performance"
    ]
)

with tab1:
    st.subheader("Daily Electricity Consumption")
    fig = px.line(
        daily,
        x="date",
        y="global_active_power",
        title="Average Daily Power Consumption",
        labels={
            "date": "Date",
            "global_active_power": "Average Power (kW)"
        }
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Electricity Readings")
    st.dataframe(
        readings[["reading_time", "global_active_power"]]
        .sort_values("reading_time", ascending=False)
        .head(15),
        use_container_width=True
    )

with tab2:
    st.subheader("Hourly Consumption Pattern")
    fig = px.bar(
        hourly,
        x="hour",
        y="global_active_power",
        title="Average Electricity Consumption by Hour",
        labels={
            "hour": "Hour of Day",
            "global_active_power": "Average Power (kW)"
        }
    )
    fig.update_layout(template="plotly_dark", xaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daily Consumption Statistics")
    st.dataframe(
        daily.sort_values("date", ascending=False),
        use_container_width=True
    )

with tab3:
    st.subheader("Actual vs Predicted Electricity Consumption")
    fig = px.line(
        forecasts,
        x="forecast_time",
        y=["actual_power", "predicted_power"],
        labels={
            "forecast_time": "Time",
            "value": "Power (kW)",
            "variable": "Measurement"
        },
        title="XGBoost Tuned Forecast Results"
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    forecast_mae = (
        forecasts["actual_power"] - forecasts["predicted_power"]
    ).abs().mean()
    forecast_rmse = (
        (forecasts["actual_power"] - forecasts["predicted_power"]) ** 2
    ).mean() ** 0.5

    a, b = st.columns(2)
    a.metric("Forecast MAE", f"{forecast_mae:.4f} kW")
    b.metric("Forecast RMSE", f"{forecast_rmse:.4f} kW")

    st.subheader("Forecast Records")
    st.dataframe(
        forecasts.sort_values("forecast_time", ascending=False).head(50),
        use_container_width=True
    )

with tab4:
    st.subheader("Electricity Anomaly Analysis")
    normal_count = int((anomalies["is_anomaly"] == 0).sum())
    anomaly_count = int((anomalies["is_anomaly"] == 1).sum())

    a, b = st.columns(2)
    a.metric("Normal Readings", f"{normal_count:,}")
    b.metric("Anomalies", f"{anomaly_count:,}")

    anomaly_summary = pd.DataFrame(
        {
            "Reading Type": ["Normal", "Anomaly"],
            "Count": [normal_count, anomaly_count]
        }
    )
    fig = px.pie(
        anomaly_summary,
        names="Reading Type",
        values="Count",
        title="Normal vs Anomalous Readings",
        hole=0.45
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detected Anomalies")
    flagged = anomalies[anomalies["is_anomaly"] == 1]
    st.dataframe(
        flagged.sort_values("reading_time", ascending=False).head(100),
        use_container_width=True
    )

with tab5:
    st.subheader("Machine Learning Model Comparison")
    st.dataframe(models, use_container_width=True)

    fig = px.bar(
        models,
        x="model_name",
        y=["mae", "rmse"],
        barmode="group",
        title="Model Error Comparison",
        labels={
            "model_name": "Model",
            "value": "Error (kW)",
            "variable": "Metric"
        }
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        models,
        x="model_name",
        y="r2_score",
        title="R² Score Comparison",
        labels={
            "model_name": "Model",
            "r2_score": "R² Score"
        }
    )
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    best_model = models.sort_values("mae").iloc[0]
    st.success(
        f"Best performing model based on MAE: {best_model['model_name']}"
    )

st.divider()
st.caption("EnergyPulse | Final Year B.Tech Computer Science Project")
