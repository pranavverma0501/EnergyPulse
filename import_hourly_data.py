"""Import the processed hourly electricity readings into MySQL."""

from getpass import getpass

import mysql.connector
import pandas as pd


def main():
    data = pd.read_csv("data/hourly_electricity.csv")
    data["Datetime"] = pd.to_datetime(data["Datetime"])

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user=input("MySQL username [root]: ") or "root",
        password=getpass("MySQL password: "),
        database="electricity_forecasting",
    )

    query = """
        INSERT IGNORE INTO electricity_readings (
            reading_time, global_active_power, global_reactive_power,
            voltage, global_intensity, sub_metering_1,
            sub_metering_2, sub_metering_3
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    columns = [
        "Global_active_power", "Global_reactive_power", "Voltage",
        "Global_intensity", "Sub_metering_1", "Sub_metering_2",
        "Sub_metering_3",
    ]

    try:
        cursor = connection.cursor()
        batch_size = 1000

        for start in range(0, len(data), batch_size):
            batch = data.iloc[start:start + batch_size]
            rows = []
            for row in batch.itertuples(index=False):
                values = [getattr(row, column) for column in columns]
                cleaned = tuple(
                    None if pd.isna(value) else float(value)
                    for value in values
                )
                rows.append((pd.Timestamp(row.Datetime).to_pydatetime(), *cleaned))

            cursor.executemany(query, rows)
            connection.commit()
            print(f"Imported {min(start + batch_size, len(data)):,} / {len(data):,}")

        print("Hourly reading import completed.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
