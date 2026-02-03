-- BFSI OLAP Schema
-- Fact and Dimension tables for Banking and Financial Services

-- Dimension: Date
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR,
    week INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- Dimension: Customer
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    age INTEGER,
    gender VARCHAR,
    occupation VARCHAR,
    income_bracket VARCHAR,
    credit_score INTEGER,
    customer_segment VARCHAR,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR,
    account_open_date DATE,
    customer_status VARCHAR
);

-- Dimension: Account
CREATE TABLE dim_account (
    account_key INTEGER PRIMARY KEY,
    account_id VARCHAR,
    account_type VARCHAR,
    account_subtype VARCHAR,
    interest_rate DECIMAL(5,2),
    account_status VARCHAR,
    branch_id VARCHAR,
    branch_name VARCHAR,
    region VARCHAR
);

-- Dimension: Product
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id VARCHAR,
    product_name VARCHAR,
    product_category VARCHAR,
    product_type VARCHAR,
    risk_level VARCHAR,
    commission_rate DECIMAL(5,2)
);

-- Dimension: Transaction Type
CREATE TABLE dim_transaction_type (
    transaction_type_key INTEGER PRIMARY KEY,
    transaction_type VARCHAR,
    transaction_category VARCHAR,
    is_debit BOOLEAN,
    is_credit BOOLEAN
);

-- Fact: Transactions
CREATE TABLE fact_transactions (
    transaction_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    customer_key INTEGER,
    account_key INTEGER,
    transaction_type_key INTEGER,
    transaction_amount DECIMAL(15,2),
    balance_after_transaction DECIMAL(15,2),
    transaction_fee DECIMAL(10,2),
    transaction_status VARCHAR,
    channel VARCHAR,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (account_key) REFERENCES dim_account(account_key),
    FOREIGN KEY (transaction_type_key) REFERENCES dim_transaction_type(transaction_type_key)
);

-- Fact: Account Balances (Daily Snapshot)
CREATE TABLE fact_account_balances (
    balance_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    account_key INTEGER,
    customer_key INTEGER,
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    average_daily_balance DECIMAL(15,2),
    minimum_balance DECIMAL(15,2),
    maximum_balance DECIMAL(15,2),
    total_deposits DECIMAL(15,2),
    total_withdrawals DECIMAL(15,2),
    transaction_count INTEGER,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (account_key) REFERENCES dim_account(account_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key)
);

-- Fact: Loans
CREATE TABLE fact_loans (
    loan_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    customer_key INTEGER,
    product_key INTEGER,
    loan_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    loan_term_months INTEGER,
    monthly_payment DECIMAL(10,2),
    outstanding_balance DECIMAL(15,2),
    principal_paid DECIMAL(15,2),
    interest_paid DECIMAL(15,2),
    loan_status VARCHAR,
    default_flag BOOLEAN,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key)
);

-- Fact: Customer Investments
CREATE TABLE fact_investments (
    investment_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    customer_key INTEGER,
    product_key INTEGER,
    investment_amount DECIMAL(15,2),
    current_value DECIMAL(15,2),
    profit_loss DECIMAL(15,2),
    return_percentage DECIMAL(5,2),
    investment_status VARCHAR,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key)
);

-- Create indexes for performance
CREATE INDEX idx_transactions_date ON fact_transactions(date_key);
CREATE INDEX idx_transactions_customer ON fact_transactions(customer_key);
CREATE INDEX idx_transactions_account ON fact_transactions(account_key);
CREATE INDEX idx_balances_date ON fact_account_balances(date_key);
CREATE INDEX idx_loans_customer ON fact_loans(customer_key);
CREATE INDEX idx_investments_customer ON fact_investments(customer_key);
