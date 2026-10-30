
import pandas as pd
import mysql.connector

from config import RAW_DB_CONFIG, BATCH_SIZE, RAW_TABLE_NAME

# Step 1: Connect to MySQL raw database
connection = mysql.connector.connect(**RAW_DB_CONFIG)

cursor = connection.cursor()

print("Connected to food_orders_raw_db successfully!")

try:
    # Step 2: Get total number of records
    cursor.execute(
        f"SELECT COUNT(*) FROM `{RAW_TABLE_NAME}`"
    )

    total_records = cursor.fetchone()[0]

    print("Total records available:", total_records)

    # Step 3: Retrieve data in batches
    batch_number = 1
    offset = 0

    while offset < total_records:

        query = f"""
            SELECT *
            FROM `{RAW_TABLE_NAME}`
            ORDER BY row_id
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """

        cursor.execute(query)

        records = cursor.fetchall()

        # Step 4: Load retrieved records into Pandas DataFrame
        columns = [
            column[0] for column in cursor.description
        ]

        batch_df = pd.DataFrame(records, columns=columns)

        print(f"\nBatch Number: {batch_number}")
        print(f"Records Retrieved: {len(batch_df)}")

        # Display first 5 records
        print(batch_df.head())

        # Move to next batch
        offset += BATCH_SIZE
        batch_number += 1

    print("\nRaw data retrieval completed!")
    print("Total records retrieved:", total_records)

finally:
    # Step 5: Close connection
    cursor.close()
    connection.close()

    print("MySQL connection closed.")
