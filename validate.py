
import pandas as pd
import numpy as np

from config import (
    TRANSFORMED_CSV,
    VALIDATION_REPORT,
    REJECTED_CSV,
    MISSING_REPORT,
    FINANCIAL_INCOMPLETE_CSV
)

# ==========================================
# STEP 1: LOAD TRANSFORMED DATA
# ==========================================

df = pd.read_csv(
    TRANSFORMED_CSV,
    keep_default_na=False,
    na_values=[""]
)

print("Transformed data loaded successfully!")
print("Total records:", len(df))

# Original source columns
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

# ==========================================
# STEP 2: CHECK MISSING VALUES
# ==========================================

print("\n========== MISSING VALUE CHECK ==========")

missing_values = df.isnull().sum()

print(missing_values)

missing_report = pd.DataFrame({
    "Column": missing_values.index,
    "Missing_Count": missing_values.values
})

missing_report.to_csv(
    MISSING_REPORT,
    index=False
)

# ==========================================
# STEP 3: CHECK DUPLICATE RECORDS
# ==========================================

print("\n========== DUPLICATE CHECK ==========")

duplicate_count = df[source_columns].duplicated().sum()

print("Duplicate records:", duplicate_count)

# ==========================================
# STEP 4: VERIFY DATA TYPES
# ==========================================

print("\n========== DATA TYPE VALIDATION ==========")

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
    "Platform_Net_Revenue"
]

# Convert datetime columns
for column in datetime_columns:
    df[column] = pd.to_datetime(
        df[column],
        errors="coerce"
    )

# Convert financial columns
for column in financial_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df["Delivery_Time_Minutes"] = pd.to_numeric(
    df["Delivery_Time_Minutes"],
    errors="coerce"
)

print(df.dtypes)

datetime_valid = all(
    pd.api.types.is_datetime64_any_dtype(df[col])
    for col in datetime_columns
)

financial_valid = all(
    pd.api.types.is_numeric_dtype(df[col])
    for col in financial_columns
)

delivery_type_valid = pd.api.types.is_numeric_dtype(
    df["Delivery_Time_Minutes"]
)

print("Datetime columns valid:", datetime_valid)
print("Financial columns valid:", financial_valid)
print("Delivery duration numeric:", delivery_type_valid)

# ==========================================
# STEP 5: VALIDATE DELIVERY DURATION
# ==========================================

print("\n========== DELIVERY DURATION VALIDATION ==========")

expected_delivery_time = (
    df["Delivery Date and Time"]
    - df["Order Date and Time"]
).dt.total_seconds() / 60

delivery_match = np.isclose(
    df["Delivery_Time_Minutes"],
    expected_delivery_time,
    equal_nan=True,
    atol=0.000001
)

delivery_mismatch_count = int(
    (~delivery_match).sum()
)

negative_delivery_count = int(
    (df["Delivery_Time_Minutes"] < 0).sum()
)

print(
    "Delivery calculation mismatches:",
    delivery_mismatch_count
)

print(
    "Negative delivery durations:",
    negative_delivery_count
)

# ==========================================
# STEP 6: VALIDATE PLATFORM NET REVENUE
# ==========================================

print("\n========== NET REVENUE VALIDATION ==========")

expected_revenue = (
    df["Commission Fee"]
    + df["Delivery Fee"]
    - df["Payment Processing Fee"]
    - df["Refunds/Chargebacks"]
)

revenue_match = np.isclose(
    df["Platform_Net_Revenue"],
    expected_revenue,
    equal_nan=True,
    atol=0.000001
)

revenue_mismatch_count = int(
    (~revenue_match).sum()
)

print(
    "Revenue calculation mismatches:",
    revenue_mismatch_count
)

# ==========================================
# STEP 7: IDENTIFY REJECTED RECORDS
# ==========================================

print("\n========== REJECTED RECORD CHECK ==========")

rejection_reasons = []

# Convert is_valid_record correctly into Boolean values
if "is_valid_record" in df.columns:

    transformation_valid = (
        df["is_valid_record"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )

else:
    transformation_valid = pd.Series(
        True,
        index=df.index
    )

for position, (index, row) in enumerate(df.iterrows()):

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

    if not delivery_match[position]:
        reasons.append("Delivery Calculation Mismatch")

    if not revenue_match[position]:
        reasons.append("Revenue Calculation Mismatch")

    # Preserve existing transformation rejection reasons
    if not transformation_valid.loc[index]:

        existing_reason = row.get(
            "invalid_reason",
            ""
        )

        if (
            pd.notna(existing_reason)
            and str(existing_reason).strip()
            not in ["", "None", "nan"]
        ):
            for reason in str(existing_reason).split("; "):
                if reason not in reasons:
                    reasons.append(reason)

        elif not reasons:
            reasons.append("Marked invalid during transformation")

    rejection_reasons.append("; ".join(reasons))

df["Validation_Rejection_Reason"] = rejection_reasons

rejected_df = df[
    df["Validation_Rejection_Reason"] != ""
].copy()

rejected_df.to_csv(
    REJECTED_CSV,
    index=False
)

# ==========================================
# STEP 8: RECORD FINANCIALLY INCOMPLETE DATA
# ==========================================

financial_incomplete_df = df[
    df[
        [
            "Commission Fee",
            "Delivery Fee",
            "Payment Processing Fee",
            "Refunds/Chargebacks"
        ]
    ].isnull().any(axis=1)
].copy()

financial_incomplete_df.to_csv(
    FINANCIAL_INCOMPLETE_CSV,
    index=False
)

print("Rejected records:", len(rejected_df))

print(
    "Financially incomplete records:",
    len(financial_incomplete_df)
)

# ==========================================
# STEP 9: GENERATE VALIDATION REPORT
# ==========================================

total_records = len(df)

valid_records = total_records - len(rejected_df)

validation_results = {
    "Total Records": total_records,
    "Missing Values": int(df.isnull().sum().sum()),
    "Duplicate Records": int(duplicate_count),
    "Datetime Types Valid": datetime_valid,
    "Financial Types Valid": financial_valid,
    "Delivery Duration Type Valid": delivery_type_valid,
    "Delivery Calculation Mismatches": delivery_mismatch_count,
    "Negative Delivery Durations": negative_delivery_count,
    "Revenue Calculation Mismatches": revenue_mismatch_count,
    "Rejected Records": len(rejected_df),
    "Valid Records": valid_records,
    "Financially Incomplete Records": len(financial_incomplete_df)
}

report_lines = [
    "FOOD ORDERS DATA VALIDATION REPORT",
    "=" * 45,
    ""
]

for key, value in validation_results.items():
    report_lines.append(f"{key}: {value}")

report_lines.extend([
    "",
    "COLUMN-WISE MISSING VALUE REPORT",
    "=" * 45
])

for column, count in missing_values.items():
    report_lines.append(f"{column}: {count}")

report_lines.extend([
    "",
    "VALIDATION STATUS",
    "=" * 45
])

checks = {
    "Duplicate check": duplicate_count == 0,
    "Datetime type check": datetime_valid,
    "Financial type check": financial_valid,
    "Delivery duration type check": delivery_type_valid,
    "Delivery calculation check": delivery_mismatch_count == 0,
    "Negative duration check": negative_delivery_count == 0,
    "Revenue calculation check": revenue_mismatch_count == 0,
    "Rejected records check": len(rejected_df) == 0
}

for check, passed in checks.items():
    report_lines.append(
        f"{check}: {'PASS' if passed else 'CHECK REQUIRED'}"
    )

overall_status = (
    "PASS"
    if all(checks.values())
    else "CHECK REQUIRED"
)

report_lines.extend([
    "",
    f"OVERALL STATUS: {overall_status}"
])

with open(
    VALIDATION_REPORT,
    "w",
    encoding="utf-8"
) as file:
    file.write("\n".join(report_lines))

# ==========================================
# STEP 10: DISPLAY FINAL SUMMARY
# ==========================================

print("\n========== FINAL VALIDATION SUMMARY ==========")

for key, value in validation_results.items():
    print(f"{key}: {value}")

print("\nOverall Status:", overall_status)

print("\nValidation report generated successfully!")

print("Files created:")
print("1.", VALIDATION_REPORT)
print("2.", MISSING_REPORT)
print("3.", REJECTED_CSV)
print("4.", FINANCIAL_INCOMPLETE_CSV)
