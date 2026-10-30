
import pandas as pd

from config import SOURCE_CSV, BATCH_SIZE

# Step 1: Read the source CSV file
df = pd.read_csv(SOURCE_CSV)

# Step 2: Display total records
print("Total records:", len(df))

# Step 3: Extract records in batches
for batch_number, start in enumerate(
    range(0, len(df), BATCH_SIZE),
    start=1
):
    batch = df.iloc[start:start + BATCH_SIZE]

    print(f"Batch Number: {batch_number}")
    print(f"Record Count: {len(batch)}")
    print("-" * 30)

print("Source data extraction completed successfully!")
