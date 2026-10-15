import pandas as pd


def load_and_calculate_pvm(file_path):
  # Load dataset
  df = pd.read_csv(file_path)

  # Pivot to compare Budget vs Actual side-by-side per SKU
  pivoted = df.pivot(
      index='SKU',
      columns='Period',
      values=['Units_Sold', 'Unit_Price', 'Unit_Cost'],
  )

  # Flatten column names
  pivoted.columns = [f'{col}_{period}' for col, period in pivoted.columns]
  pivoted = pivoted.fillna(0)

  # Calculate Revenues and Gross Profits
  pivoted['Revenue_Budget'] = (
      pivoted['Units_Sold_Budget'] * pivoted['Unit_Price_Budget']
  )
  pivoted['Revenue_Actual'] = (
      pivoted['Units_Sold_Actual'] * pivoted['Unit_Price_Actual']
  )
  pivoted['GP_Budget'] = pivoted['Units_Sold_Budget'] * (
      pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
  )
  pivoted['GP_Actual'] = pivoted['Units_Sold_Actual'] * (
      pivoted['Unit_Price_Actual'] - pivoted['Unit_Cost_Actual']
  )

  # Total Gross Profit Variance
  pivoted['GP_Variance'] = pivoted['GP_Actual'] - pivoted['GP_Budget']

  # Simplified PVM breakdown logic (Volume, Price, Cost variances)
  # Volume Variance: (Actual Units - Budget Units) * Budget Unit Gross Margin
  budget_gm_per_unit = (
      pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
  )
  pivoted['Volume_Variance'] = (
      pivoted['Units_Sold_Actual'] - pivoted['Units_Sold_Budget']
  ) * budget_gm_per_unit

  # Price Variance: (Actual Price - Budget Price) * Actual Units Sold
  pivoted['Price_Variance'] = (
      pivoted['Unit_Price_Actual'] - pivoted['Unit_Price_Budget']
  ) * pivoted['Units_Sold_Actual']

  # Cost Variance: (Budget Unit Cost - Actual Unit Cost) * Actual Units Sold
  pivoted['Cost_Variance'] = (
      pivoted['Unit_Cost_Budget'] - pivoted['Unit_Cost_Actual']
  ) * pivoted['Units_Sold_Actual']

  return pivoted
