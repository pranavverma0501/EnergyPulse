"""Store the final model evaluation metrics in MySQL."""

from getpass import getpass

import mysql.connector


MODELS = [
    ("Linear Regression", 0.3990, 0.5502, 0.4599),
    ("XGBoost Tuned", 0.3298, 0.4753, 0.5957),
]


def main():
    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user=input("MySQL username [root]: ") or "root",
        password=getpass("MySQL password: "),
        database="electricity_forecasting",
    )

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO model_results (model_name, mae, rmse, r2_score)
            SELECT %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM model_results WHERE model_name = %s
            )
        """

        for model_name, mae, rmse, r2_score in MODELS:
            cursor.execute(
                query,
                (model_name, mae, rmse, r2_score, model_name),
            )

        connection.commit()
        print("Model results are up to date.")

        cursor.execute(
            "SELECT model_name, mae, rmse, r2_score "
            "FROM model_results ORDER BY mae"
        )
        for row in cursor.fetchall():
            print(row)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
