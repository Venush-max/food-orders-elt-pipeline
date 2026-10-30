
import pandas as pd
import mysql.connector

from config import (
    SOURCE_CSV,
    BATCH_SIZE,
    MYSQL_CONFIG,
    RAW_DB_NAME,
    RAW_TABLE_NAME
)

# ==========================================
# STEP 1: READ ORIGINAL CSV DATA
# ==========================================

df = pd.read_csv(SOURCE_CSV)

print("Total records:", len(df))

# ==========================================
# STEP 2: CONNECT TO MYSQL
# ==========================================

connection = mysql.connector.connect(**MYSQL_CONFIG)
cursor = connection.cursor()

try:

    # ==========================================
    # STEP 3: CREATE RAW DATABASE
    # ==========================================

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{RAW_DB_NAME}`"
    )

    cursor.execute(
        f"USE `{RAW_DB_NAME}`"
    )

    print("Database created successfully!")

    # ==========================================
    # STEP 4: CREATE RAW TABLE
    # ==========================================

    columns = df.columns.tolist()

    column_definitions = ", ".join(
        f"`{str(col).replace('`', '``')}` LONGTEXT NULL"
        for col in columns
    )

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{RAW_TABLE_NAME}` (
            row_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            {column_definitions}
        )
    """

    cursor.execute(create_table_query)

    print("Raw table created successfully!")

    # ==========================================
    # STEP 5: CHECK EXISTING RECORDS
    # ==========================================

    cursor.execute(
        f"SELECT COUNT(*) FROM `{RAW_TABLE_NAME}`"
    )

    existing_records = cursor.fetchone()[0]

    if existing_records == len(df):

        print("\nRaw data is already loaded.")
        print("Existing records:", existing_records)
        print("Skipping insertion to avoid duplicates.")

    elif existing_records > 0:

        raise RuntimeError(
            f"Raw table contains {existing_records} records, "
            f"but source CSV contains {len(df)} records. "
            "Check the existing data before loading."
        )

    else:

        # ==========================================
        # STEP 6: PREPARE INSERT QUERY
        # ==========================================

        column_names = ", ".join(
            f"`{str(col).replace('`', '``')}`"
            for col in columns
        )

        placeholders = ", ".join(
            ["%s"] * len(columns)
        )

        insert_query = f"""
            INSERT INTO `{RAW_TABLE_NAME}` ({column_names})
            VALUES ({placeholders})
        """

        # Finish initial database operations
        connection.commit()

        # ==========================================
        # STEP 7: INSERT DATA IN BATCHES
        # ==========================================

        for batch_number, start in enumerate(
            range(0, len(df), BATCH_SIZE),
            start=1
        ):

            batch = df.iloc[start:start + BATCH_SIZE]

            rows = []

            for row in batch.itertuples(
                index=False,
                name=None
            ):

                converted_row = tuple(
                    None if pd.isna(value)
                    else value.item()
                    if hasattr(value, "item")
                    else value
                    for value in row
                )

                rows.append(converted_row)

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

            except Exception as error:

                connection.rollback()

                print(
                    f"Batch {batch_number} failed:",
                    error
                )

                raise

    # ==========================================
    # STEP 8: VERIFY TOTAL RECORDS
    # ==========================================

    cursor.execute(
        f"SELECT COUNT(*) FROM `{RAW_TABLE_NAME}`"
    )

    total_records = cursor.fetchone()[0]

    print("\n========== RAW DATA LOAD SUMMARY ==========")

    print("Expected records:", len(df))
    print("Total records in MySQL:", total_records)

    if total_records == len(df):

        print("Verification PASSED!")

    else:

        raise RuntimeError(
            "Raw data count verification failed!"
        )

    print("\nRaw Data Loading Completed!")

finally:

    # ==========================================
    # STEP 9: CLOSE CONNECTION
    # ==========================================

    cursor.close()
    connection.close()

    print("MySQL connection closed.")
