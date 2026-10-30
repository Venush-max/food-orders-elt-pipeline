
import subprocess
import sys
import re
import math
import pandas as pd
import mysql.connector

from config import (
    BASE_DIR,
    SOURCE_CSV,
    TRANSFORMED_CSV,
    REJECTED_CSV,
    BATCH_SIZE,
    RAW_DB_CONFIG,
    ANALYTICS_DB_CONFIG,
    RAW_TABLE_NAME,
    ANALYTICS_TABLE_NAME
)

# ==========================================
# FOOD ORDERS ELT BATCH PIPELINE
# ==========================================

pipeline_steps = [
    ("Extract Source Data", "extract.py"),
    ("Load Raw Data into MySQL", "load_raw.py"),
    ("Retrieve Raw Data from MySQL", "retrieve_raw.py"),
    ("Transform Data Using Pandas", "transform.py"),
    ("Validate Transformed Data", "validate.py"),
    ("Load Transformed Data into MySQL", "load_transformed.py")
]

step_outputs = {}

successful_batches = 0
failed_batches = 0

print("=" * 60, flush=True)
print("          FOOD ORDERS ELT BATCH PIPELINE", flush=True)
print("=" * 60, flush=True)


# ==========================================
# DATABASE COUNT FUNCTION
# ==========================================

def get_database_record_count(database_config, table_name):

    connection = mysql.connector.connect(**database_config)
    cursor = connection.cursor()

    try:
        cursor.execute(
            f"SELECT COUNT(*) FROM `{table_name}`"
        )
        return cursor.fetchone()[0]

    finally:
        cursor.close()
        connection.close()


# ==========================================
# EXECUTE PIPELINE
# ==========================================

try:

    for step_number, (step_name, script_name) in enumerate(
        pipeline_steps,
        start=1
    ):

        print("\n" + "=" * 60, flush=True)
        print(f"STEP {step_number}: {step_name}", flush=True)
        print("=" * 60, flush=True)

        script_path = BASE_DIR / script_name

        if not script_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {script_name}"
            )

        result = subprocess.run(
            [sys.executable, "-u", str(script_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        # Display script output
        print(result.stdout, end="", flush=True)

        if result.stderr:
            print(result.stderr, end="", flush=True)

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args
            )

        step_outputs[script_name] = result.stdout

        print(
            f"\nSTEP {step_number} COMPLETED SUCCESSFULLY!",
            flush=True
        )

    # ==========================================
    # CALCULATE FINAL EXECUTION METRICS
    # ==========================================

    extract_output = step_outputs.get("extract.py", "")
    load_raw_output = step_outputs.get("load_raw.py", "")
    retrieve_output = step_outputs.get("retrieve_raw.py", "")
    transform_output = step_outputs.get("transform.py", "")
    validation_output = step_outputs.get("validate.py", "")
    load_analytics_output = step_outputs.get(
        "load_transformed.py", ""
    )

    # Total records extracted
    match = re.search(
        r"Total records:\s*(\d+)",
        extract_output
    )

    total_extracted = int(match.group(1)) if match else 0

    # Expected extraction batches
    expected_batches = (
        math.ceil(total_extracted / BATCH_SIZE)
        if total_extracted > 0 else 0
    )

    # Actual extraction batches
    total_batches = len(
        re.findall(r"Batch Number:", extract_output)
    )

    # Raw records stored in MySQL
    raw_loaded = get_database_record_count(
        RAW_DB_CONFIG,
        RAW_TABLE_NAME
    )

    # Raw records retrieved from MySQL
    match = re.search(
        r"Total records retrieved:\s*(\d+)",
        retrieve_output
    )

    raw_retrieved = (
        int(match.group(1)) if match else 0
    )

    # Valid transformed records
    transformed_df = pd.read_csv(TRANSFORMED_CSV)
    valid_records = len(transformed_df)

    # Rejected records
    rejected_df = pd.read_csv(REJECTED_CSV)
    rejected_records = len(rejected_df)

    # Duplicate records removed during transformation
    duplicate_matches = re.findall(
        r"Duplicates Removed:\s*(\d+)",
        transform_output
    )

    duplicates_removed = (
        int(duplicate_matches[-1])
        if duplicate_matches else 0
    )

    print(
        "\nTotal duplicates removed:",
        duplicates_removed,
        flush=True
    )

    # Transformed records stored in analytics database
    analytics_loaded = get_database_record_count(
        ANALYTICS_DB_CONFIG,
        ANALYTICS_TABLE_NAME
    )

    # Successful insertion batches in this run
    successful_batches = len(
        re.findall(
            r"Batch\s+\d+:\s+\d+\s+records inserted successfully",
            load_raw_output + load_analytics_output,
            re.IGNORECASE
        )
    )

    # Failed insertion batches in this run
    failed_batches = len(
        re.findall(
            r"Batch\s+\d+\s+failed:",
            load_raw_output + load_analytics_output,
            re.IGNORECASE
        )
    )

    # ==========================================
    # FINAL VALIDATION STATUS
    # ==========================================

    validation_passed = (
        re.search(
            r"Overall Status:\s*PASS",
            validation_output,
            re.IGNORECASE
        ) is not None
    )

    # Check each pipeline condition separately
    checks = {
        "CSV extraction": (
            total_extracted == len(pd.read_csv(SOURCE_CSV))
        ),

        "Extraction batches": (
            total_batches == expected_batches
        ),

        "Raw database count": (
            raw_loaded == total_extracted
        ),

        "Raw data retrieval": (
            raw_retrieved == raw_loaded
        ),

        "Transformation count": (
            valid_records
            + rejected_records
            + duplicates_removed
            == raw_retrieved
        ),

        "Analytics database count": (
            analytics_loaded == valid_records
        ),

        "Failed batches": (
            failed_batches == 0
        ),

        "Data validation": validation_passed
    }

    print("\n========== FINAL STATUS CHECKS ==========")

    for check_name, check_result in checks.items():

        print(
            f"{check_name}: "
            f"{'PASS' if check_result else 'FAIL'}",
            flush=True
        )

    if all(checks.values()):
        final_status = "PASS"
    else:
        final_status = "CHECK REQUIRED"

    # ==========================================
    # FINAL EXECUTION REPORT
    # ==========================================

    print("\n" + "=" * 60, flush=True)
    print("          FINAL EXECUTION REPORT", flush=True)
    print("=" * 60, flush=True)

    print(
        f"Total records extracted from CSV: {total_extracted}",
        flush=True
    )

    print(
        f"Total batches processed: {total_batches}",
        flush=True
    )

    print(
        f"Total raw records loaded into MySQL: {raw_loaded}",
        flush=True
    )

    print(
        f"Total raw records retrieved from MySQL: {raw_retrieved}",
        flush=True
    )

    print(
        f"Total valid records transformed: {valid_records}",
        flush=True
    )

    print(
        f"Total rejected records: {rejected_records}",
        flush=True
    )

    print(
        f"Total duplicates removed: {duplicates_removed}",
        flush=True
    )

    print(
        f"Transformed records loaded into analytics DB: "
        f"{analytics_loaded}",
        flush=True
    )

    print(
        f"Successful insertion batches (this run): "
        f"{successful_batches}",
        flush=True
    )

    print(
        f"Failed insertion batches (this run): "
        f"{failed_batches}",
        flush=True
    )

    print("-" * 60, flush=True)

    print(
        f"FINAL VALIDATION STATUS: {final_status}",
        flush=True
    )

    print("=" * 60, flush=True)

    if final_status != "PASS":
        sys.exit(1)

    print(
        "\nAll ELT pipeline steps completed successfully!",
        flush=True
    )

except subprocess.CalledProcessError as error:

    print("\n" + "=" * 60, flush=True)
    print("          ELT PIPELINE EXECUTION FAILED", flush=True)
    print("=" * 60, flush=True)

    print("Failed command:", error.cmd, flush=True)
    print("Exit code:", error.returncode, flush=True)

    sys.exit(error.returncode)

except Exception as error:

    print("\nUnexpected pipeline error:", error, flush=True)

    sys.exit(1)
