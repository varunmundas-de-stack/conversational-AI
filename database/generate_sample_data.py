"""
Generate sample BFSI data for the OLAP database
"""
import duckdb
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
NUM_CUSTOMERS = 1000
NUM_ACCOUNTS = 1500
NUM_PRODUCTS = 50
NUM_DAYS = 365  # Last 1 year
NUM_TRANSACTIONS = 50000

def generate_date_dimension(conn):
    """Generate date dimension for the last year"""
    print("Generating date dimension...")

    start_date = datetime.now() - timedelta(days=NUM_DAYS)
    dates = []

    for i in range(NUM_DAYS):
        current_date = start_date + timedelta(days=i)
        dates.append({
            'date_key': int(current_date.strftime('%Y%m%d')),
            'date': current_date.strftime('%Y-%m-%d'),
            'year': current_date.year,
            'quarter': (current_date.month - 1) // 3 + 1,
            'month': current_date.month,
            'month_name': current_date.strftime('%B'),
            'week': current_date.isocalendar()[1],
            'day': current_date.day,
            'day_of_week': current_date.weekday(),
            'day_name': current_date.strftime('%A'),
            'is_weekend': current_date.weekday() >= 5,
            'is_holiday': random.random() < 0.05
        })

    conn.execute("DELETE FROM dim_date")
    conn.executemany("""
        INSERT INTO dim_date VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(d['date_key'], d['date'], d['year'], d['quarter'], d['month'],
           d['month_name'], d['week'], d['day'], d['day_of_week'],
           d['day_name'], d['is_weekend'], d['is_holiday']) for d in dates])

    print(f"  Generated {len(dates)} date records")

def generate_customer_dimension(conn):
    """Generate customer dimension"""
    print("Generating customer dimension...")

    first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Emma',
                   'Robert', 'Olivia', 'William', 'Ava', 'Richard', 'Sophia', 'Joseph']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                  'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez']
    occupations = ['Engineer', 'Teacher', 'Doctor', 'Lawyer', 'Accountant', 'Manager',
                   'Sales', 'Consultant', 'Self-employed', 'Retired']
    income_brackets = ['<30K', '30K-50K', '50K-75K', '75K-100K', '100K-150K', '>150K']
    segments = ['Premium', 'Gold', 'Silver', 'Bronze']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
              'San Antonio', 'San Diego', 'Dallas', 'San Jose']
    states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA']

    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        city_idx = random.randint(0, len(cities) - 1)
        customers.append({
            'customer_key': i,
            'customer_id': f'CUST{i:06d}',
            'first_name': random.choice(first_names),
            'last_name': random.choice(last_names),
            'age': random.randint(18, 80),
            'gender': random.choice(['M', 'F']),
            'occupation': random.choice(occupations),
            'income_bracket': random.choice(income_brackets),
            'credit_score': random.randint(300, 850),
            'customer_segment': random.choice(segments),
            'city': cities[city_idx],
            'state': states[city_idx],
            'country': 'USA',
            'account_open_date': (datetime.now() - timedelta(days=random.randint(30, 3650))).strftime('%Y-%m-%d'),
            'customer_status': random.choice(['Active'] * 9 + ['Inactive'])
        })

    conn.execute("DELETE FROM dim_customer")
    conn.executemany("""
        INSERT INTO dim_customer VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(c['customer_key'], c['customer_id'], c['first_name'], c['last_name'],
           c['age'], c['gender'], c['occupation'], c['income_bracket'],
           c['credit_score'], c['customer_segment'], c['city'], c['state'],
           c['country'], c['account_open_date'], c['customer_status']) for c in customers])

    print(f"  Generated {len(customers)} customer records")

def generate_account_dimension(conn):
    """Generate account dimension"""
    print("Generating account dimension...")

    account_types = ['Savings', 'Checking', 'Credit Card', 'Investment']
    account_subtypes = {
        'Savings': ['Regular Savings', 'High Yield Savings', 'Money Market'],
        'Checking': ['Basic Checking', 'Premium Checking', 'Student Checking'],
        'Credit Card': ['Platinum', 'Gold', 'Standard'],
        'Investment': ['Brokerage', 'IRA', '401K']
    }
    statuses = ['Active', 'Active', 'Active', 'Active', 'Dormant', 'Closed']
    branches = ['Branch-001', 'Branch-002', 'Branch-003', 'Branch-004', 'Branch-005']
    branch_names = ['Downtown', 'Uptown', 'Westside', 'Eastside', 'Central']
    regions = ['North', 'South', 'East', 'West', 'Central']

    accounts = []
    for i in range(1, NUM_ACCOUNTS + 1):
        acc_type = random.choice(account_types)
        branch_idx = random.randint(0, len(branches) - 1)
        accounts.append({
            'account_key': i,
            'account_id': f'ACC{i:08d}',
            'account_type': acc_type,
            'account_subtype': random.choice(account_subtypes[acc_type]),
            'interest_rate': round(random.uniform(0.01, 5.0), 2),
            'account_status': random.choice(statuses),
            'branch_id': branches[branch_idx],
            'branch_name': branch_names[branch_idx],
            'region': regions[branch_idx]
        })

    conn.execute("DELETE FROM dim_account")
    conn.executemany("""
        INSERT INTO dim_account VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(a['account_key'], a['account_id'], a['account_type'], a['account_subtype'],
           a['interest_rate'], a['account_status'], a['branch_id'], a['branch_name'],
           a['region']) for a in accounts])

    print(f"  Generated {len(accounts)} account records")

def generate_product_dimension(conn):
    """Generate product dimension"""
    print("Generating product dimension...")

    products = [
        # Loan products
        ('LOAN001', 'Personal Loan', 'Loans', 'Personal', 'Medium', 1.5),
        ('LOAN002', 'Home Loan', 'Loans', 'Mortgage', 'Low', 2.0),
        ('LOAN003', 'Auto Loan', 'Loans', 'Vehicle', 'Medium', 1.8),
        ('LOAN004', 'Education Loan', 'Loans', 'Education', 'Low', 1.2),
        ('LOAN005', 'Business Loan', 'Loans', 'Business', 'High', 2.5),
        # Investment products
        ('INV001', 'Mutual Fund - Equity', 'Investments', 'Mutual Fund', 'High', 0.5),
        ('INV002', 'Mutual Fund - Debt', 'Investments', 'Mutual Fund', 'Low', 0.3),
        ('INV003', 'Fixed Deposit', 'Investments', 'Fixed Income', 'Low', 0.1),
        ('INV004', 'Stocks', 'Investments', 'Equity', 'High', 0.8),
        ('INV005', 'Bonds', 'Investments', 'Fixed Income', 'Low', 0.2),
        # Insurance products
        ('INS001', 'Life Insurance', 'Insurance', 'Life', 'Low', 3.0),
        ('INS002', 'Health Insurance', 'Insurance', 'Health', 'Medium', 2.5),
        ('INS003', 'Auto Insurance', 'Insurance', 'Vehicle', 'Medium', 2.0),
    ]

    product_records = []
    for i, (pid, name, cat, ptype, risk, comm) in enumerate(products, 1):
        product_records.append((i, pid, name, cat, ptype, risk, comm))

    conn.execute("DELETE FROM dim_product")
    conn.executemany("""
        INSERT INTO dim_product VALUES (?, ?, ?, ?, ?, ?, ?)
    """, product_records)

    print(f"  Generated {len(product_records)} product records")

def generate_transaction_type_dimension(conn):
    """Generate transaction type dimension"""
    print("Generating transaction type dimension...")

    transaction_types = [
        (1, 'Deposit', 'Credit', False, True),
        (2, 'Withdrawal', 'Debit', True, False),
        (3, 'Transfer Out', 'Debit', True, False),
        (4, 'Transfer In', 'Credit', False, True),
        (5, 'Interest Credit', 'Credit', False, True),
        (6, 'Fee Debit', 'Debit', True, False),
        (7, 'ATM Withdrawal', 'Debit', True, False),
        (8, 'Card Payment', 'Debit', True, False),
        (9, 'Salary Credit', 'Credit', False, True),
        (10, 'Bill Payment', 'Debit', True, False),
    ]

    conn.execute("DELETE FROM dim_transaction_type")
    conn.executemany("""
        INSERT INTO dim_transaction_type VALUES (?, ?, ?, ?, ?)
    """, transaction_types)

    print(f"  Generated {len(transaction_types)} transaction type records")

def generate_fact_transactions(conn):
    """Generate transaction facts"""
    print("Generating transaction facts...")

    # Get date keys
    date_keys = conn.execute("SELECT date_key FROM dim_date").fetchall()
    date_keys = [d[0] for d in date_keys]

    channels = ['ATM', 'Online', 'Mobile App', 'Branch', 'Phone']
    statuses = ['Completed', 'Completed', 'Completed', 'Completed', 'Pending', 'Failed']

    transactions = []
    for i in range(1, NUM_TRANSACTIONS + 1):
        transaction_amount = round(random.uniform(10, 10000), 2)
        is_debit = random.choice([True, False])

        transactions.append({
            'transaction_key': i,
            'date_key': random.choice(date_keys),
            'customer_key': random.randint(1, NUM_CUSTOMERS),
            'account_key': random.randint(1, NUM_ACCOUNTS),
            'transaction_type_key': random.randint(1, 10),
            'transaction_amount': transaction_amount,
            'balance_after_transaction': round(random.uniform(100, 50000), 2),
            'transaction_fee': round(random.uniform(0, 5), 2) if random.random() < 0.3 else 0,
            'transaction_status': random.choice(statuses),
            'channel': random.choice(channels)
        })

    conn.execute("DELETE FROM fact_transactions")
    conn.executemany("""
        INSERT INTO fact_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(t['transaction_key'], t['date_key'], t['customer_key'], t['account_key'],
           t['transaction_type_key'], t['transaction_amount'], t['balance_after_transaction'],
           t['transaction_fee'], t['transaction_status'], t['channel']) for t in transactions])

    print(f"  Generated {len(transactions)} transaction records")

def generate_fact_loans(conn):
    """Generate loan facts"""
    print("Generating loan facts...")

    date_keys = conn.execute("SELECT date_key FROM dim_date").fetchall()
    date_keys = [d[0] for d in date_keys]

    loan_statuses = ['Active', 'Active', 'Active', 'Closed', 'Defaulted']

    loans = []
    for i in range(1, 500):
        loan_amount = round(random.uniform(5000, 500000), 2)
        interest_rate = round(random.uniform(3.5, 12.0), 2)
        loan_term = random.choice([12, 24, 36, 48, 60, 120, 240, 360])
        monthly_payment = round(loan_amount * (interest_rate/100/12) / (1 - (1 + interest_rate/100/12)**(-loan_term)), 2)
        principal_paid = round(random.uniform(0, loan_amount), 2)
        outstanding = loan_amount - principal_paid

        loans.append({
            'loan_key': i,
            'date_key': random.choice(date_keys),
            'customer_key': random.randint(1, NUM_CUSTOMERS),
            'product_key': random.randint(1, 5),  # Loan products
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'loan_term_months': loan_term,
            'monthly_payment': monthly_payment,
            'outstanding_balance': outstanding,
            'principal_paid': principal_paid,
            'interest_paid': round(random.uniform(0, loan_amount * 0.3), 2),
            'loan_status': random.choice(loan_statuses),
            'default_flag': random.random() < 0.05
        })

    conn.execute("DELETE FROM fact_loans")
    conn.executemany("""
        INSERT INTO fact_loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(l['loan_key'], l['date_key'], l['customer_key'], l['product_key'],
           l['loan_amount'], l['interest_rate'], l['loan_term_months'], l['monthly_payment'],
           l['outstanding_balance'], l['principal_paid'], l['interest_paid'],
           l['loan_status'], l['default_flag']) for l in loans])

    print(f"  Generated {len(loans)} loan records")

def main():
    """Main function to generate all sample data"""
    db_path = Path(__file__).parent / 'bfsi_olap.duckdb'
    schema_path = Path(__file__).parent / 'schema.sql'

    print(f"Creating database at: {db_path}")

    # Connect to DuckDB
    conn = duckdb.connect(str(db_path))

    # Create schema
    print("Creating schema...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        for statement in schema_sql.split(';'):
            if statement.strip():
                conn.execute(statement)

    # Generate dimensions
    generate_date_dimension(conn)
    generate_customer_dimension(conn)
    generate_account_dimension(conn)
    generate_product_dimension(conn)
    generate_transaction_type_dimension(conn)

    # Generate facts
    generate_fact_transactions(conn)
    generate_fact_loans(conn)

    # Show summary
    print("\n" + "="*50)
    print("Database created successfully!")
    print("="*50)
    print("\nTable counts:")
    tables = ['dim_date', 'dim_customer', 'dim_account', 'dim_product',
              'dim_transaction_type', 'fact_transactions', 'fact_loans']

    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} records")

    conn.close()
    print(f"\nDatabase saved to: {db_path}")

if __name__ == '__main__':
    main()
