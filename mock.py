import pandas as pd


def load_and_calculate_pvm():
  # 1. Create a mock dataset in memory (mimicking enterprise hardware SKUs)
  data = {
      'SKU': [
          'DGX-H100-Node',
          'DGX-H100-Node',
          'HGX-B200-Sys',
          'HGX-B200-Sys',
          'Quantum-2-Switch',
          'Quantum-2-Switch',
      ],
      'Period': ['Budget', 'Actual', 'Budget', 'Actual', 'Budget', 'Actual'],
      'Units_Sold': [1200, 1400, 450, 400, 3000, 2800],
      'Unit_Price': [350000, 345000, 500000, 510000, 15000, 15500],
      'Unit_Cost': [210000, 215000, 300000, 295000, 9000, 9200],
  }
  df = pd.DataFrame(data)

  # 2. Pivot to compare Budget vs Actual side-by-side per SKU
  pivoted = df.pivot(
      index='SKU',
      columns='Period',
      values=['Units_Sold', 'Unit_Price', 'Unit_Cost'],
  )

  # Flatten column names
  pivoted.columns = [f'{col}_{period}' for col, period in pivoted.columns]
  pivoted = pivoted.fillna(0)

  # 3. Calculate Revenues and Gross Profits
  pivoted['GP_Budget'] = pivoted['Units_Sold_Budget'] * (
      pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
  )
  pivoted['GP_Actual'] = pivoted['Units_Sold_Actual'] * (
      pivoted['Unit_Price_Actual'] - pivoted['Unit_Cost_Actual']
  )

  # Total Gross Profit Variance
  pivoted['GP_Variance'] = pivoted['GP_Actual'] - pivoted['GP_Budget']

  # 4. PVM Breakdown Logic
  budget_gm_per_unit = (
      pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
  )
  pivoted['Volume_Variance'] = (
      pivoted['Units_Sold_Actual'] - pivoted['Units_Sold_Budget']
  ) * budget_gm_per_unit

  pivoted['Price_Variance'] = (
      pivoted['Unit_Price_Actual'] - pivoted['Unit_Price_Budget']
  ) * pivoted['Units_Sold_Actual']

  pivoted['Cost_Variance'] = (
      pivoted['Unit_Cost_Budget'] - pivoted['Unit_Cost_Actual']
  ) * pivoted['Units_Sold_Actual']

  return pivoted


# Run the test
results = load_and_calculate_pvm()
print(
    results[
        ['GP_Budget', 'GP_Actual', 'GP_Variance', 'Volume_Variance', 'Price_Variance', 'Cost_Variance']
    ]
)
