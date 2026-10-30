# Food Orders Batch-Based ELT Pipeline

## 1. Project Overview

This project implements a batch-based ELT (Extract, Load, Transform) pipeline using Python, Pandas, and MySQL for an online food delivery company.

The pipeline extracts food order data from a CSV file, loads the original data into a MySQL raw database, retrieves the data, transforms and validates it using Pandas, and loads the cleaned data into a separate analytics database.

The main objective is to preserve the original source data while creating a clean and reliable dataset for business analysis.

## 2. Technologies Used

- **Python:** Pipeline development and execution.
- **Pandas:** Data extraction, transformation, and validation.
- **MySQL:** Raw and analytics data storage.
- **MySQL Connector:** Python-to-MySQL connectivity.
- **CSV:** Source data and generated output files.

## 3. Project Structure

```text
Pipeline/
│
├── food_orders.csv
│
├── config.py
├── extract.py
├── load_raw.py
├── retrieve_raw.py
├── transform.py
├── validate.py
├── load_transformed.py
├── elt_batch_pipeline.py
│
├── transformed_food_orders.csv
├── invalid_food_orders.csv
├── rejected_records.csv
├── missing_values_report.csv
├── financial_incomplete_records.csv
│
├── validation_report.txt
├── requirements.txt
└── README.md
```

### Python Files

| File | Description |
|---|---|
| config.py | Stores project paths, batch size, and MySQL configuration. |
| extract.py | Extracts source CSV records in batches. |
| load_raw.py | Loads original records into the raw MySQL database. |
| retrieve_raw.py | Retrieves raw records from MySQL in batches. |
| transform.py | Cleans, transforms, and processes records using Pandas. |
| validate.py | Performs data-quality checks and generates validation reports. |
| load_transformed.py | Loads cleaned records into the analytics database. |
| elt_batch_pipeline.py | Executes all pipeline stages in sequence and displays the final execution report. |

## 4. Database Setup

The project uses two MySQL databases.

### Raw Database

Database name: `food_orders_raw_db`

Table name: `raw_food_orders`

Purpose:
- Stores the original source data.
- Preserves duplicate records.
- Preserves missing values.
- Maintains the original data before transformation.

### Analytics Database

Database name: `food_orders_analytics_db`

Table name: `cleaned_food_orders`

Purpose:
- Stores cleaned and transformed records.
- Contains appropriate data types.
- Includes calculated delivery duration.
- Includes platform net revenue.
- Supports business analysis using SQL.

The Python scripts automatically create the databases and tables if they do not already exist.

Make sure MySQL Server is installed and running before executing the pipeline.

## 5. Configuration

The `config.py` file contains the project configuration.

Important settings:

- Batch size: 100 records.
- MySQL host: localhost.
- MySQL user: root.
- MySQL port: 3306.
- Raw database: food_orders_raw_db.
- Analytics database: food_orders_analytics_db.

### MySQL Password Configuration

The project uses an environment variable named `MYSQL_PASSWORD` to protect database credentials.

In Windows PowerShell, set your MySQL password:

```powershell
$env:MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
```

Replace the placeholder with your own MySQL password.

The environment variable is used by `config.py` to establish the MySQL connection.

Do not upload your actual database password to GitHub or include it in this README.

## 6. Installation

### Step 1: Install Python

Install Python and verify the installation:

```powershell
python --version
```

### Step 2: Install MySQL

Install MySQL Server and ensure the MySQL service is running.

### Step 3: Open the Project Folder

```powershell
cd E:\Pipeline
```

### Step 4: Install Required Dependencies

```powershell
pip install -r requirements.txt
```

The required Python packages are:

- pandas
- mysql-connector-python

## 7. Pipeline Execution

Set the MySQL password in PowerShell:

```powershell
$env:MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
```

Execute the complete pipeline:

```powershell
python elt_batch_pipeline.py
```

The pipeline executes the following stages automatically:

1. Extract source data from the CSV file.
2. Load original records into the raw MySQL database.
3. Retrieve raw records from MySQL.
4. Transform data using Pandas.
5. Validate the transformed dataset.
6. Load cleaned records into the analytics database.
7. Display the final execution report.

## 8. Data Transformation

The transformation process performs the following operations:

- Removes exact duplicate records.
- Handles missing Payment Method values using `Unknown`.
- Handles missing Discounts and Offers using `Not recorded`.
- Preserves missing financial values as NULL/NaN.
- Converts date and time columns into datetime types.
- Converts financial columns into numeric types.
- Calculates delivery duration in minutes.
- Calculates platform net revenue.

### Platform Net Revenue Formula

```text
Platform Net Revenue =
Commission Fee
+ Delivery Fee
- Payment Processing Fee
- Refunds/Chargebacks
```

Invalid records are tracked separately rather than silently removed.

## 9. Data Validation

The validation process checks:

- Missing values.
- Duplicate records.
- Datetime data types.
- Financial data types.
- Delivery duration calculations.
- Negative delivery durations.
- Platform net revenue calculations.
- Rejected records.

Generated validation files:

- `validation_report.txt`
- `missing_values_report.csv`
- `rejected_records.csv`
- `financial_incomplete_records.csv`

The validation report records the results of the data-quality checks.

## 10. Business Analysis Using SQL

Business analysis is performed using the `cleaned_food_orders` table in `food_orders_analytics_db`.

The following questions are answered:

1. Total order value.
2. Average order value.
3. Payment method with the highest number of orders.
4. Order channel with the highest number of orders.
5. Average delivery time in minutes.
6. Total platform net revenue.

### Sample Business Analysis Results

| Business Metric | Result |
|---|---:|
| Total Order Value | 1,013,415.00 |
| Average Order Value | 1,055.64 |
| Most Used Payment Method | Cash on Delivery |
| Cash on Delivery Orders | 336 |
| Most Used Order Channel | Mobile App |
| Mobile App Orders | 686 |
| Average Delivery Time | 73.575 minutes |
| Total Platform Net Revenue | 80,877.00 |

Note: SQL aggregate functions such as SUM() and AVG() ignore NULL values. Financial metrics therefore use the available financial values.

## 11. Final Execution Results

The pipeline was executed successfully with the following results:

| Execution Metric | Result |
|---|---:|
| Total CSV records extracted | 1010 |
| Total batches processed | 11 |
| Raw records loaded into MySQL | 1010 |
| Raw records retrieved from MySQL | 1010 |
| Duplicate records removed | 10 |
| Valid transformed records | 1000 |
| Rejected records | 0 |
| Transformed records loaded into analytics DB | 1000 |
| Final validation status | PASS |

The final validation checks confirmed that all required pipeline stages and data-quality checks passed.

Successful and failed insertion batch counts depend on whether records are newly inserted during a particular execution. Existing records are not reinserted.

## 12. Expected Output

The completed pipeline preserves the original food order data in `food_orders_raw_db`, retrieves it from MySQL, transforms and validates it using Pandas, and loads the processed records into `food_orders_analytics_db`.

The final execution report confirms the number of extracted, loaded, retrieved, transformed, and rejected records, along with the final validation status.

## 13. Conclusion

This project demonstrates a complete batch-based ELT workflow using Python, Pandas, and MySQL.

It separates raw and analytics data, handles duplicate and missing values, performs data-quality validation, and supports business analysis using SQL.

The pipeline successfully processed 1010 source records, removed 10 duplicate records, and loaded 1000 valid transformed records into the analytics database.

**Final Status: PASS**