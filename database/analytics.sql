-- 1. Total revenue
SELECT ROUND(SUM(total_amount), 2) AS total_revenue FROM fact_orders;
-- 2. Total orders
SELECT COUNT(*) AS total_orders FROM fact_orders;
-- 3. Total units sold
SELECT SUM(quantity) AS total_quantity FROM fact_orders;
-- 4. Revenue by customer
SELECT c.customer_id, c.customer_name, ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.customer_id ORDER BY revenue DESC;
-- 5. Revenue by city
SELECT c.city, ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.city ORDER BY revenue DESC;
-- 6. Top five customers
SELECT c.customer_id, c.customer_name, ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.customer_id ORDER BY revenue DESC LIMIT 5;
-- 7. Daily revenue
SELECT substr(event_timestamp,1,10) event_date, ROUND(SUM(total_amount),2) revenue FROM fact_orders GROUP BY event_date ORDER BY event_date;
-- 8. Orders by city
SELECT c.city, COUNT(*) orders FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.city ORDER BY orders DESC;
-- 9. Rejected by reason
SELECT rejection_reason, COUNT(*) rejected FROM rejected_records GROUP BY rejection_reason ORDER BY rejected DESC;
-- 10. Run history
SELECT run_id,start_time,end_time,duration_seconds,orders_input_count,valid_count,rejected_count,loaded_count,pipeline_status,error_message FROM pipeline_runs ORDER BY start_time DESC;
