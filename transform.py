
import pandas as pd
import mysql.connector

from config import (
    RAW_DB_CONFIG,
    BATCH_SIZE,
    RAW_TABLE_NAME,
    TRANSFORMED_CSV,
    INVALID_CSV
)

# ==========================================
# STEP 1: CONNECT TO RAW MYSQL DATABASE
# ==========================================

connection = mysql.connector.connect(**RAW_DB_CONFIG)
cursor = connection.cursor()

print("Connected to raw database successfully!")

try:

    # ==========================================
    # STEP 2: GET TOTAL RECORD COUNT
    # ==========================================

    cursor.execute(
        f"SELECT COUNT(*) FROM `{RAW_TABLE_NAME}`"
    )

    total_records = cursor.fetchone()[0]

    print("Total raw records:", total_records)

    offset = 0
    batch_number = 1

    # Original CSV columns (row_id is excluded)
    source_columns = [
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
        "Order Channel"
    ]

    # Global duplicate tracking across batches
    seen_fingerprints = set()

    transformed_batches = []

    total_duplicates_removed = 0

    # ==========================================
    # STEP 3: RETRIEVE AND TRANSFORM EACH BATCH
    # ==========================================

    while offset < total_records:

        query = f"""
            SELECT *
            FROM `{RAW_TABLE_NAME}`
            ORDER BY row_id
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """

        cursor.execute(query)

        records = cursor.fetchall()

        columns = [
            col[0] for col in cursor.description
        ]

        batch_df = pd.DataFrame(
            records,
            columns=columns
        )

        original_batch_count = len(batch_df)

        print(f"\nProcessing Batch: {batch_number}")
        print("Retrieved Records:", original_batch_count)

        # ======================================
        # STEP 4: REMOVE EXACT DUPLICATES
        # ======================================

        fingerprints = pd.util.hash_pandas_object(
            batch_df[source_columns],
            index=False
        )

        # Detect duplicates within current batch
        local_duplicates = batch_df[
            source_columns
        ].duplicated(keep="first")

        # Detect duplicates from previous batches
        global_duplicates = fingerprints.isin(
            seen_fingerprints
        )

        duplicate_mask = (
            local_duplicates | global_duplicates
        )

        # Keep unique records
        batch_df = batch_df.loc[
            ~duplicate_mask
        ].copy()

        # Update global duplicate tracking
        seen_fingerprints.update(
            fingerprints.loc[
                ~duplicate_mask
            ].tolist()
        )

        duplicates_removed = int(
            duplicate_mask.sum()
        )

        total_duplicates_removed += duplicates_removed

        print("Duplicates Removed:", duplicates_removed)

        # ======================================
        # STEP 5: HANDLE MISSING VALUES
        # ======================================

        batch_df["Payment Method"] = (
            batch_df["Payment Method"].fillna("Unknown")
        )

        batch_df["Discounts and Offers"] = (
            batch_df["Discounts and Offers"].fillna(
                "Not recorded"
            )
        )

        # ======================================
        # STEP 6: CONVERT DATETIME COLUMNS
        # ======================================

        batch_df["Order Date and Time"] = pd.to_datetime(
            batch_df["Order Date and Time"],
            errors="coerce"
        )

        batch_df["Delivery Date and Time"] = pd.to_datetime(
            batch_df["Delivery Date and Time"],
            errors="coerce"
        )

        # ======================================
        # STEP 7: CONVERT FINANCIAL COLUMNS
        # ======================================

        financial_columns = [
            "Order Value",
            "Delivery Fee",
            "Commission Fee",
            "Payment Processing Fee",
            "Refunds/Chargebacks"
        ]

        for column in financial_columns:

            batch_df[column] = pd.to_numeric(
                batch_df[column],
                errors="coerce"
            )

        # ======================================
        # STEP 8: CALCULATE DELIVERY TIME
        # ======================================

        batch_df["Delivery_Time_Minutes"] = (
            batch_df["Delivery Date and Time"]
            - batch_df["Order Date and Time"]
        ).dt.total_seconds() / 60

        # ======================================
        # STEP 9: CALCULATE PLATFORM NET REVENUE
        # ======================================

        batch_df["Platform_Net_Revenue"] = (
            batch_df["Commission Fee"]
            + batch_df["Delivery Fee"]
            - batch_df["Payment Processing Fee"]
            - batch_df["Refunds/Chargebacks"]
        )

        # ======================================
        # STEP 10: IDENTIFY INVALID RECORDS
        # ======================================

        invalid_reasons = []

        for _, row in batch_df.iterrows():

            reasons = []

            if pd.isna(row["Order Date and Time"]):
                reasons.append("Invalid Order Timestamp")

            if pd.isna(row["Delivery Date and Time"]):
                reasons.append("Invalid Delivery Timestamp")

            if (
                pd.notna(row["Delivery_Time_Minutes"])
                and row["Delivery_Time_Minutes"] < 0
            ):
                reasons.append("Negative Delivery Duration")

            invalid_reasons.append(
                "; ".join(reasons) if reasons else "None"
            )

        batch_df["invalid_reason"] = invalid_reasons

        batch_df["is_valid_record"] = (
            batch_df["invalid_reason"] == "None"
        )

        # Store transformed batch
        transformed_batches.append(batch_df)

        print("Unique Records Processed:", len(batch_df))

        print(
            "Invalid Records:",
            (~batch_df["is_valid_record"]).sum()
        )

        offset += BATCH_SIZE
        batch_number += 1

    # ==========================================
    # STEP 11: COMBINE TRANSFORMED BATCHES
    # ==========================================

    if transformed_batches:

        transformed_df = pd.concat(
            transformed_batches,
            ignore_index=True
        )

    else:
        transformed_df = pd.DataFrame()

    # Separate valid and invalid records
    if not transformed_df.empty:

        valid_df = transformed_df[
            transformed_df["is_valid_record"]
        ].copy()

        invalid_df = transformed_df[
            ~transformed_df["is_valid_record"]
        ].copy()

    else:
        valid_df = transformed_df.copy()
        invalid_df = transformed_df.copy()

    # ==========================================
    # STEP 12: SAVE TRANSFORMED DATA
    # ==========================================

    transformed_df.to_csv(
        TRANSFORMED_CSV,
        index=False
    )

    invalid_df.to_csv(
        INVALID_CSV,
        index=False
    )

    # ==========================================
    # STEP 13: FINAL SUMMARY
    # ==========================================

    print("\n========== TRANSFORMATION SUMMARY ==========")

    print("Original Records:", total_records)

    print("Duplicates Removed:", total_duplicates_removed)

    print("Unique Records:", len(transformed_df))

    print("Valid Records:", len(valid_df))

    print("Invalid Records:", len(invalid_df))

    if not transformed_df.empty:

        print(
            "Missing Financial Values:",
            transformed_df[financial_columns]
            .isna()
            .sum()
            .to_dict()
        )

        print(
            "Missing Platform Net Revenue:",
            transformed_df[
                "Platform_Net_Revenue"
            ].isna().sum()
        )

    print("\nTransformed data saved successfully!")

    print("Transformed file:", TRANSFORMED_CSV)
    print("Invalid records file:", INVALID_CSV)

    print("MySQL raw table remains unchanged.")

finally:

    # ==========================================
    # STEP 14: CLOSE CONNECTION
    # ==========================================

    cursor.close()
    connection.close()

    print("MySQL connection closed.")
