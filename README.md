# EnergyPulse

**Electricity Consumption Forecasting, Anomaly Detection and Energy Monitoring System**

EnergyPulse is a final-year B.Tech Computer Science project that uses household electricity consumption data to explore usage patterns, forecast next-hour power consumption, detect unusual readings, and display the results in a Streamlit dashboard backed by MySQL.

## Features

- Data cleaning and hourly/daily aggregation
- Next-hour electricity consumption forecasting
- Linear Regression baseline
- Tuned XGBoost model with lag and rolling-average features
- Isolation Forest for unusual power readings
- MySQL storage for readings, forecasts, anomalies, and model metrics
- Streamlit dashboard for charts and model comparison

## Dataset

The project uses the **Individual Household Electric Power Consumption** dataset from the UCI Machine Learning Repository:

https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption

Download `household_power_consumption.txt` and place it in the `data/` folder. The raw dataset is not included in this repository because of its size.

## Project structure

```text
EnergyPulse/
├── data/
│   ├── daily_electricity.csv
│   ├── hourly_electricity.csv
│   └── model_ready_electricity.csv
├── database/
│   └── electricity_database.sql
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   └── 02_electricity_forecasting.ipynb
├── app.py
├── import_hourly_data.py
├── insert_model_results.py
├── load_model_outputs.py
├── requirements.txt
└── .gitignore
```

## Setup

1. Install Python and MySQL.
2. Open `database/electricity_database.sql` in MySQL Workbench or VS Code and run it. It creates the database and four tables, then provides the analysis queries used by the project. If your existing tables are already present, the `CREATE TABLE IF NOT EXISTS` statements leave them unchanged.
3. Install the Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the notebooks in order:
   - `01_data_exploration.ipynb`
   - `02_electricity_forecasting.ipynb`

5. Import hourly readings:

   ```bash
   python import_hourly_data.py
   ```

6. After running notebook 02, load its forecast and anomaly CSV outputs:

   ```bash
   python load_model_outputs.py
   ```

7. Add the model comparison results:

   ```bash
   python insert_model_results.py
   ```

8. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

Enter your local MySQL username and password when prompted. The dashboard also asks for database connection details in its sidebar.

## Model results

The final test-set results recorded during project development are:

| Model | MAE (kW) | RMSE (kW) | R² |
|---|---:|---:|---:|
| Linear Regression | 0.3990 | 0.5502 | 0.4599 |
| Tuned XGBoost | 0.3298 | 0.4753 | 0.5957 |

Lower MAE and RMSE indicate smaller prediction errors. A higher R² indicates that the model explains more variation in the target values.

## Notes

- The target is next-hour `Global_active_power`, measured in kW.
- Isolation Forest flags unusual power values; an anomaly is not, by itself, proof of a fault or electricity theft.
- Database passwords are entered locally and should never be committed to GitHub.
