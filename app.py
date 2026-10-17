import os
import openai
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title='Hardware PVM Variance Engine', page_icon='📊', layout='wide'
)

st.title('📊 Hardware SKU & Gross Margin PVM Variance Engine')
st.markdown(
    'Enterprise-grade Price-Volume-Mix (PVM) variance attribution with live'
    ' sensitivity modeling and AI commentary.'
)

# Sidebar Configuration
with st.sidebar:
  st.header('Configuration & Modeling')

  # 1. Preset Scenario Buttons
  st.subheader('1. Scenario Presets')
  col_p1, col_p2 = st.columns(2)
  load_standard = col_p1.button('Standard MBR')
  load_stress = col_p2.button('Cost Spike Stress')

  if 'scenario' not in st.session_state:
    st.session_state.scenario = 'Standard'

  if load_standard:
    st.session_state.scenario = 'Standard'
  if load_stress:
    st.session_state.scenario = 'Cost Spike Stress'

  st.markdown('---')

  # 2. Data Input
  st.subheader('2. Data Input')
  uploaded_file = st.file_uploader(
      'Upload Custom SKU CSV',
      type=['csv'],
      help='Upload a CSV with columns: SKU, Period, Units_Sold, Unit_Price, Unit_Cost',
  )

  st.markdown('---')

  # 3. Interactive Sensitivity Sliders
  st.subheader('3. Sensitivity Sliders')
  cost_inflation = st.slider(
      'COGS Inflation Adjustment (%)',
      min_value=-20,
      max_value=50,
      value=0,
      step=5,
      help='Simulate component cost increases or savings across all SKUs.',
  )
  price_adjustment = st.slider(
      'ASP Adjustment (%)',
      min_value=-10,
      max_value=20,
      value=0,
      step=1,
      help='Simulate enterprise pricing shifts or discounting.',
  )

  st.markdown('---')

  # 4. AI Configuration
  st.subheader('4. AI Configuration')
  groq_api_key = st.text_input(
      'Groq API Key (Optional)',
      type='password',
      help='Get a free key at console.groq.com',
  )


# 1. Dataset Generator
@st.cache_data
def get_default_data(scenario='Standard'):
  if scenario == 'Cost Spike Stress':
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
        'Units_Sold': [1200, 1300, 450, 380, 3000, 2600],
        'Unit_Price': [350000, 345000, 500000, 505000, 15000, 15200],
        'Unit_Cost': [210000, 245000, 300000, 330000, 9000, 10500],
    }
  else:
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


if uploaded_file is not None:
  try:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success('Custom CSV loaded successfully!')
  except Exception as e:
    st.sidebar.error(f'Error reading CSV: {e}')
    df = get_default_data(st.session_state.scenario)
else:
  df = get_default_data(st.session_state.scenario)

# Apply Sensitivity Sliders to Actuals
if cost_inflation != 0 or price_adjustment != 0:
  actual_mask = df['Period'] == 'Actual'
  df.loc[actual_mask, 'Unit_Cost'] = df.loc[
      actual_mask, 'Unit_Cost'
  ] * (1 + cost_inflation / 100.0)
  df.loc[actual_mask, 'Unit_Price'] = df.loc[
      actual_mask, 'Unit_Price'
  ] * (1 + price_adjustment / 100.0)

# 2. Calculation Engine
try:
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

except Exception as calc_error:
  st.error(
      f'Calculation Error: Please verify your CSV columns match SKU, Period,'
      f' Units_Sold, Unit_Price, Unit_Cost. Details: {calc_error}'
  )
  st.stop()

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
st.dataframe(display_df.style.format('{:,.2f}', subset=numeric_cols))

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

st.divider()


# 6. Hybrid Commentary Engine & Report Export
def generate_fallback_commentary(df_pivoted):
  total_var = df_pivoted['GP_Variance'].sum()
  total_vol = df_pivoted['Volume_Variance'].sum()
  total_price = df_pivoted['Price_Variance'].sum()
  total_cost = df_pivoted['Cost_Variance'].sum()
  top_sku = df_pivoted.loc[df_pivoted['GP_Variance'].idxmax()]['SKU']
  bottom_sku = df_pivoted.loc[df_pivoted['GP_Variance'].idxmin()]['SKU']
  direction = 'expanded' if total_var >= 0 else 'compressed'

  return f"""### 📋 Executive Summary (Automated Analysis)
* **Overall Performance:** Total gross profit {direction} by **${abs(total_var):,.0f}** relative to budget.
* **Driver Breakdown:** Volume impact contributed **${total_vol:,.0f}**, price realization yielded **${total_price:,.0f}**, and COGS variance impacted margins by **${total_cost:,.0f}**.
* **SKU Highlights:** **{top_sku}** led positive variances, while **{bottom_sku}** faced cost headwinds requiring close review.
"""


st.subheader('📝 Executive Board Commentary & Export')
st.markdown(
    'Generate professional narrative commentary and download the report for'
    ' leadership review.'
)

if 'commentary_text' not in st.session_state:
  st.session_state.commentary_text = ''

col_btn1, col_btn2 = st.columns([2, 2])

if col_btn1.button('Generate Executive Summary'):
  with st.spinner('Compiling executive board notes...'):
    if groks_key := groq_api_key:
      try:
        client = openai.OpenAI(
            api_key=groks_key, base_url='https://api.groq.com/openai/v1'
        )
        summary_text = display_df.to_string(index=False)
        prompt = f"""
                You are a senior Director of FP&A at a major tech company. 
                Review this SKU-level Price-Volume-Mix (PVM) gross profit variance data:
                
                {summary_text}
                
                Write a concise, professional executive board commentary highlighting overall performance, top/bottom SKU drivers, and Volume vs. Price vs. Cost impact. Keep it structured for C-level executives.
                """
        response = client.chat.completions.create(
            model='llama-3.1-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
        )
        st.session_state.commentary_text = (
            response.choices[0].message.content
        )
        st.success('Live AI Commentary Generated via Llama-3.1 (Groq)!')
      except Exception as e:
        st.warning(
            f'API call failed ({e}). Falling back to built-in smart summary:'
        )
        st.session_state.commentary_text = generate_fallback_commentary(
            pivoted.reset_index()
        )
    else:
      st.session_state.commentary_text = generate_fallback_commentary(
          pivoted.reset_index()
      )
      st.success('Executive commentary compiled successfully!')

if st.session_state.commentary_text:
  st.markdown(st.session_state.commentary_text)

  # Download Report Button
  st.download_button(
      label='📥 Download Executive Report (.md)',
      data=st.session_state.commentary_text,
      file_name='hardware_pvm_executive_report.md',
      mime='text/markdown',
  )
