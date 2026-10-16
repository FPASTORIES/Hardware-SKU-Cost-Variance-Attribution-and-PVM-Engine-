import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title='Hardware PVM Variance Engine', page_icon='📊', layout='wide'
)

st.title('📊 Hardware SKU & Gross Margin PVM Variance Engine')
st.markdown(
    'Automating Price-Volume-Mix (PVM) variance attribution for hardware product lines.'
)

# 1. Default sample data generator
@st.cache_data
def get_default_data():
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
  return pd.DataFrame(data)


df = get_default_data()

with st.sidebar:
  st.header('Configuration')
  st.info(
      'Using default hardware SKU dataset. You can extend this to accept live'
      ' CSV uploads in the next phase!'
  )

# 2. Calculation Engine
pivoted = df.pivot(
    index='SKU',
    columns='Period',
    values=['Units_Sold', 'Unit_Price', 'Unit_Cost'],
)
pivoted.columns = [f'{col}_{period}' for col, period in pivoted.columns]
pivoted = pivoted.fillna(0)

pivoted['GP_Budget'] = pivoted['Units_Sold_Budget'] * (
    pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
)
pivoted['GP_Actual'] = pivoted['Units_Sold_Actual'] * (
    pivoted['Unit_Price_Actual'] - pivoted['Unit_Cost_Actual']
)
pivoted['GP_Variance'] = pivoted['GP_Actual'] - pivoted['GP_Budget']

budget_gm_per_unit = pivoted['Unit_Price_Budget'] - pivoted['Unit_Cost_Budget']
pivoted['Volume_Variance'] = (
    pivoted['Units_Sold_Actual'] - pivoted['Units_Sold_Budget']
) * budget_gm_per_unit
pivoted['Price_Variance'] = (
    pivoted['Unit_Price_Actual'] - pivoted['Unit_Price_Budget']
) * pivoted['Units_Sold_Actual']
pivoted['Cost_Variance'] = (
    pivoted['Unit_Cost_Budget'] - pivoted['Unit_Cost_Actual']
) * pivoted['Units_Sold_Actual']

# 3. Display Metrics Summary
col1, col2, col3 = st.columns(3)
total_budget_gp = pivoted['GP_Budget'].sum()
total_actual_gp = pivoted['GP_Actual'].sum()
total_gp_var = pivoted['GP_Variance'].sum()

col1.metric('Total Budget GP', f'${total_budget_gp:,.0f}')
col2.metric('Total Actual GP', f'${total_actual_gp:,.0f}')
col3.metric(
    'Net GP Variance',
    f'${total_gp_var:,.0f}',
    delta=f'{(total_gp_var/total_budget_gp)*100:.1f}%',
)

st.divider()

# 4. Dataframe & Visuals
st.subheader('SKU-Level PVM Breakdown')
display_df = pivoted[
    [
        'GP_Budget',
        'GP_Actual',
        'GP_Variance',
        'Volume_Variance',
        'Price_Variance',
        'Cost_Variance',
    ]
].reset_index()
numeric_cols = display_df.select_dtypes(
    include=['float64', 'int64', 'float32', 'int32']
).columns
st.dataframe(display_df.style.format("{:,.2f}", subset=numeric_cols))

# 5. Chart Visualization
st.subheader('Variance Attribution by SKU')
chart_data = display_df.melt(
    id_vars='SKU',
    value_vars=['Volume_Variance', 'Price_Variance', 'Cost_Variance'],
    var_name='Variance_Type',
    value_name='Amount',
)
fig = px.bar(
    chart_data,
    x='SKU',
    y='Amount',
    color='Variance_Type',
    barmode='group',
    title='Gross Profit Variance Attribution (Volume vs Price vs Cost)',
)
st.plotly_chart(fig, use_container_width=True)
