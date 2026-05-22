import pandas as pd

# Products sheet
products_data = {
    'name': ['Rice', 'Sugar', 'Cooking Oil'],
    'category': ['Food', 'Food', 'Food'],
    'quantity': [100, 50, 75],
    'unit_price': [45.00, 40.00, 120.00],
    'reorder_level': [20, 15, 10]
}

# Transactions sheet
transactions_data = {
    'product_name': ['Rice', 'Sugar', 'Rice', 'Cooking Oil', 'Sugar'],
    'transaction_type': ['IN', 'IN', 'OUT', 'OUT', 'OUT'],
    'quantity': [50, 30, 10, 5, 8],
    'transaction_date': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
    'notes': ['New stock', 'New stock', 'Daily sale', 'Daily sale', 'Customer order']
}

df_products = pd.DataFrame(products_data)
df_transactions = pd.DataFrame(transactions_data)

with pd.ExcelWriter('stock_data.xlsx', engine='openpyxl') as writer:
    df_products.to_excel(writer, sheet_name='Products', index=False)
    df_transactions.to_excel(writer, sheet_name='Transactions', index=False)

print('Template created: stock_data.xlsx')
print('Fill in your data and run import_excel.py to import!')