
import pandas as pd
import mysql.connector

from config import (
    TRANSFORMED_CSV,
    BATCH_SIZE,
    ANALYTICS_DB_CONFIG,
    ANALYTICS_DB_NAME,
    ANALYTICS_TABLE_NAME
)

# ==========================================
# STEP 1: LOAD VALIDATED TRANSFORMED DATA
# ==========================================

df = pd.read_csv(
    TRANSFORMED_CSV,
    keep_default_na=False,
    na_values=[""]
)

print("Transformed data loaded successfully!")
print("Total records:", len(df))

# ==========================================
# STEP 2: CONNECT TO MYSQL
# ==========================================

connection = mysql.connector.connect(**ANALYTICS_DB_CONFIG)
cursor = connection.cursor()

try:

    # ==========================================
    # STEP 3: CREATE ANALYTICS DATABASE
    # ==========================================

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{ANALYTICS_DB_NAME}`"
    )

    cursor.execute(
        f"USE `{ANALYTICS_DB_NAME}`"
    )

    print("Analytics database created successfully!")

    # ==========================================
    # STEP 4: CREATE CLEANED TABLE
    # ==========================================

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{ANALYTICS_TABLE_NAME}` (

        row_id BIGINT PRIMARY KEY,

        `Order ID` BIGINT,
        `Customer ID` VARCHAR(20),
        `Restaurant ID` VARCHAR(20),

        `Order Date and Time` DATETIME,
        `Delivery Date and Time` DATETIME,

        `Order Value` DECIMAL(12,2),
        `Delivery Fee` DECIMAL(12,2),

        `Payment Method` VARCHAR(100),
        `Discounts and Offers` VARCHAR(255),

        `Commission Fee` DECIMAL(12,2),
        `Payment Processing Fee` DECIMAL(12,2),
        `Refunds/Chargebacks` DECIMAL(12,2),

        `Weather Condition` VARCHAR(50),
        `Order Channel` VARCHAR(50),

        Delivery_Time_Minutes DECIMAL(10,2),
        Platform_Net_Revenue DECIMAL(12,2),

        invalid_reason TEXT,
        is_valid_record BOOLEAN

    )
    """

    cursor.execute(create_table_query)

    print("Cleaned table created successfully!")

    # ==========================================
    # STEP 5: PREPARE DATA TYPES
    # ==========================================

    datetime_columns = [
        "Order Date and Time",
        "Delivery Date and Time"
    ]

    financial_columns = [
        "Order Value",
        "Delivery Fee",
        "Commission Fee",
        "Payment Processing Fee",
        "Refunds/Chargebacks",
        "Delivery_Time_Minutes",
        "Platform_Net_Revenue"
    ]

    for column in datetime_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    for column in financial_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Normalize validation status
    df["is_valid_record"] = (
        df["is_valid_record"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    # ==========================================
    # STEP 6: PREPARE INSERT QUERY
    # ==========================================

    columns = [
        "row_id",
        "Order ID",
        "Customer ID",
        "Restaurant ID",
        "Order Date and Time",
        "Delivery Date and Time",
        "Order Value",
        "Delivery Fee",
        "Payment Method",
        "Discounts and Offers",
        "Commission Fee",
        "Payment Processing Fee",
        "Refunds/Chargebacks",
        "Weather Condition",
        "Order Channel",
        "Delivery_Time_Minutes",
        "Platform_Net_Revenue",
        "invalid_reason",
        "is_valid_record"
    ]

    column_names = ", ".join(
        f"`{column}`" for column in columns
    )

    placeholders = ", ".join(
        ["%s"] * len(columns)
    )

    insert_query = f"""
        INSERT INTO `{ANALYTICS_TABLE_NAME}`
        ({column_names})
        VALUES ({placeholders})
    """

    # ==========================================
    # STEP 7: CHECK EXISTING RECORDS
    # ==========================================

    cursor.execute(
        f"SELECT COUNT(*) FROM `{ANALYTICS_TABLE_NAME}`"
    )

    existing_records = cursor.fetchone()[0]

    connection.commit()

    if existing_records == len(df):

        print("\nAnalytics data is already loaded.")

        print("Existing records:", existing_records)

        print("Skipping insertion to avoid duplicates.")

    elif existing_records > 0:

        raise RuntimeError(
            f"Analytics table contains {existing_records} records, "
            f"but transformed CSV contains {len(df)} records. "
            "Please check the existing data before loading."
        )

    else:

        # ==========================================
        # STEP 8: LOAD DATA IN BATCHES
        # ==========================================

        total_records = len(df)

        for batch_number, start in enumerate(
            range(0, total_records, BATCH_SIZE),
            start=1
        ):

            batch = df.iloc[
                start:start + BATCH_SIZE
            ]

            rows = []

            for row in batch[columns].itertuples(
                index=False,
                name=None
            ):

                converted_row = []

                for value in row:

                    if pd.isna(value):
                        converted_row.append(None)

                    elif isinstance(value, pd.Timestamp):
                        converted_row.append(
                            value.to_pydatetime()
                        )

                    elif hasattr(value, "item"):
                        converted_row.append(value.item())

                    else:
                        converted_row.append(value)

                rows.append(tuple(converted_row))

            try:

                connection.start_transaction()

                cursor.executemany(
                    insert_query,
                    rows
                )

                connection.commit()

                print(
                    f"Batch {batch_number}: "
                    f"{len(rows)} records inserted successfully"
                )

            except mysql.connector.Error as error:

                connection.rollback()

                print(
                    f"ERROR: Batch {batch_number} insertion failed!"
                )

                print("Database error:", error)

                raise RuntimeError(
                    f"Batch {batch_number} rolled back."
                ) from error

    # ==========================================
    # STEP 9: VERIFY FINAL RECORD COUNT
    # ==========================================

    cursor.execute(
        f"SELECT COUNT(*) FROM `{ANALYTICS_TABLE_NAME}`"
    )

    loaded_records = cursor.fetchone()[0]

    print("\n========== LOAD VERIFICATION ==========")

    print("Expected records:", len(df))
    print("Loaded records:", loaded_records)

    if loaded_records == len(df):
        print("Verification PASSED!")

    else:
        raise RuntimeError(
            "Analytics table record count verification failed!"
        )

    # ==========================================
    # STEP 10: DISPLAY SAMPLE RECORDS
    # ==========================================

    cursor.execute(
        f"""
        SELECT *
        FROM `{ANALYTICS_TABLE_NAME}`
        LIMIT 5
        """
    )

    sample_records = cursor.fetchall()

    print("\nSample records:")

    for record in sample_records:
        print(record)

    print("\nProcessed data loading completed!")

finally:

    # ==========================================
    # STEP 11: CLOSE CONNECTION
    # ==========================================

    cursor.close()
    connection.close()

    print("MySQL connection closed.")
