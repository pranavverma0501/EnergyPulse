"""Load the notebook's forecast and anomaly outputs into MySQL.

Run this after executing notebook 02. Existing table data is left untouched
to avoid duplicate inserts.
"""

from getpass import getpass

import mysql.connector
import pandas as pd


def main():
    forecasts = pd.read_csv("data/forecast_results.csv")
    anomalies = pd.read_csv("data/anomaly_results.csv")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user=input("MySQL username [root]: ") or "root",
        password=getpass("MySQL password: "),
        database="electricity_forecasting",
    )

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM forecasts")
        if cursor.fetchone()[0] == 0:
            forecast_rows = [
                (
                    pd.to_datetime(row.prediction_time).to_pydatetime(),
                    float(row.actual_power),
                    float(row.predicted_power),
                    "XGBoost Tuned",
                )
                for row in forecasts.itertuples(index=False)
            ]
            cursor.executemany(
                """
                INSERT INTO forecasts
                    (forecast_time, actual_power, predicted_power, model_name)
                VALUES (%s, %s, %s, %s)
                """,
                forecast_rows,
            )
            connection.commit()
            print(f"Inserted {len(forecast_rows):,} forecast rows.")
        else:
            print("Forecast table already contains data; skipping.")

        cursor.execute("SELECT COUNT(*) FROM anomalies")
        if cursor.fetchone()[0] == 0:
            anomaly_rows = [
                (
                    pd.to_datetime(row.Datetime).to_pydatetime(),
                    float(row.Global_active_power),
                    float(row.anomaly_score),
                    int(row.is_anomaly),
                )
                for row in anomalies.itertuples(index=False)
            ]
            batch_size = 500
            for start in range(0, len(anomaly_rows), batch_size):
                cursor.executemany(
                    """
                    INSERT INTO anomalies
                        (reading_time, observed_power, anomaly_score, is_anomaly)
                    VALUES (%s, %s, %s, %s)
                    """,
                    anomaly_rows[start:start + batch_size],
                )
                connection.commit()
            print(f"Inserted {len(anomaly_rows):,} anomaly-analysis rows.")
        else:
            print("Anomaly table already contains data; skipping.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
