# Data Dictionary

## orders.csv

| Column | Type | Rule |
|---|---|---|
| order_id | String | Required unique order business key |
| customer_id | String | Required reference to customers source |
| product_id | String | Required product identifier |
| quantity | Integer | Greater than zero |
| unit_price | Decimal | Greater than zero, two decimal output precision |
| event_timestamp | ISO-8601 datetime | Required; late values are allowed |

## customers.csv

| Column | Type | Rule |
|---|---|---|
| customer_id | String | Required unique natural key |
| customer_name | String | Required nonblank value |
| city | String | Required nonblank value |
| registration_date | ISO-8601 date | Required valid calendar date |

## Analytics tables

`dim_customers`: `customer_key` surrogate PK; unique `customer_id`; current name, city, and registration date.

`fact_orders`: `order_id` PK; `customer_key` FK; product, quantity, numeric unit/total amount, event timestamp, source filename, and pipeline run ID.

`pipeline_runs`: run identifier, UTC timing, input/valid/rejected/loaded counts, status, and error.

`rejected_records`: run/source identifiers, rejection timestamp and reason, and serialized original source record.
