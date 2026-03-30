import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# --- 1. SECRETS NA GOOGLE SHEETS CONNECTION ---
# Hii inatumia 'secrets' zilizopo kwenye Streamlit Cloud (sio faili la json moja kwa moja kwa usalama)

def get_connection():
    # Tunajaribu kupata connection kutoka kwenye Streamlit Secrets
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # HAPA WEKE URL YA GOOGLE SHEETS YAKO (ILE ULICOPY KATIKA HATUA YA 1)
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1jEUgdLm8QcfsqRnLWfW5vdd9UZr1efyOZlEfv0idfcw/edit?gid=0#gid=0") 
        worksheet = sh.sheet1
        return worksheet
    except Exception as e:
        st.error(f"Imeshindikana kuunganisha na Google Sheets: {e}")
        return None

# Fungsha ya kusoma data
def load_data(worksheet):
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=['Tarehe', 'Kitu', 'Aina', 'Kiasi'])
    df = pd.DataFrame(data)
    # Tunahakikisha Tarehe ni format sahihi
    df['Tarehe'] = pd.to_datetime(df['Tarehe']).dt.date
    return df

# Fungsha ya kuhifadhi data (Inafuta yote ya kale na kuandika upya - Safi na rahisi)
# Fungsha mpya ya kuhifadhi data (Inahifadhi Tarehe kama String ili isilete Error)
def save_data(worksheet, df):
    worksheet.clear()
    
    # 1. Tunahifadhi Vichwa (Headers)
    # Tunahakikisha vichwa vinakuwa maneno (strings)
    headers = [str(col) for col in df.columns.tolist()]
    worksheet.append_row(headers)
    
    # 2. Tunahifadhi Data (Rows)
    for index, row in df.iterrows():
        # Tunabadilisha row kuwa list, lakini TUNAGEUZA TAREHE KUWA MANENO
        row_values = []
        for item in row:
            # Ikiwa ni Tarehe (Timestamp au date object), tunageuza kuwa String (YYYY-MM-DD)
            # Hii inazuia TypeError
            if isinstance(item, (pd.Timestamp, datetime.date)):
                row_values.append(str(item))
            else:
                row_values.append(item)
        
        worksheet.append_row(row_values)
# --- 2. MWANZO WA PROGRAMU ---
worksheet = get_connection()
if worksheet:
    st.session_state.df = load_data(worksheet)
else:
    st.session_state.df = pd.DataFrame(columns=['Tarehe', 'Kitu', 'Aina', 'Kiasi'])

st.title("💰 BUDGET TRACKER PRO ") #(Cloud Database)
st.markdown("Fahamu  matumizi yako, Jenga uchumi wako.")

# --- 3. MADARAJA (TABS) ---
tab1, tab2, tab3 = st.tabs(["📥 Kuingiza", "🛠️ Usimamizi", "📊 Dashboard"])

# TAB 1: KUINGIZA
with tab1:
    st.header("Ongeza Mpya")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Tarehe", value=datetime.now().date())
            new_category = st.selectbox("Aina", ["Chakula", "Nyumba", "Usafiri", "Michezo", "Mapato", "Mengine"])
        with col2:
            new_item = st.text_input("Kitu / Chanzo")
            new_amount = st.number_input("Kiasi (TSh)", min_value=0, value=0)
        
        submitted = st.form_submit_button("💾 ONGEZA KWA ORODHA")
        
        if submitted:
            new_data = pd.DataFrame({
                'Tarehe': [new_date],
                'Kitu': [new_item],
                'Aina': [new_category],
                'Kiasi': [new_amount]
            })
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            save_data(worksheet, st.session_state.df) # HII NI MUHIMU: Tunahifadhi kwenye Cloud
            st.success("Imewekwa kikamilifu kwenye Google Sheets!")

# TAB 2: USIMAMIZI
with tab2:
    st.header("Usimamizi wa Data")
    if not st.session_state.df.empty:
        st.dataframe(st.session_state.df, use_container_width=True)
        st.divider()
        
        action_col1, action_col2 = st.columns(2)
        
        # DELETE
        with action_col1:
            st.subheader("🗑️ Futa Mstari")
            del_idx = st.selectbox("Chagua Index ufutao:", options=st.session_state.df.index)
            if st.button("FUTA MSTARI HUU", type="primary"):
                st.session_state.df = st.session_state.df.drop(del_idx).reset_index(drop=True)
                save_data(worksheet, st.session_state.df) # HII NI MUHIMU
                st.success("Umefutwa!")
                st.rerun()
        
        # EDIT
        with action_col2:
            st.subheader("✏️ Badilisha")
            edit_idx = st.selectbox("Chagua Index uliopotoka:", options=st.session_state.df.index)
            row_data = st.session_state.df.loc[edit_idx]
            
            with st.form("edit_form"):
                e_date = st.date_input("Badilisha Tarehe", value=row_data['Tarehe'])
                e_cat = st.selectbox("Badilisha Aina", ["Chakula", "Nyumba", "Usafiri", "Michezo", "Mapato", "Mengine"], index=["Chakula", "Nyumba", "Usafiri", "Michezo", "Mapato", "Mengine"].index(row_data['Aina']))
                e_item = st.text_input("Badilisha Kitu", value=row_data['Kitu'])
                e_amount = st.number_input("Badilisha Kiasi", min_value=0, value=int(row_data['Kiasi']))
                
                if st.form_submit_button("🔄 SASISHA"):
                    st.session_state.df.at[edit_idx, 'Tarehe'] = e_date
                    st.session_state.df.at[edit_idx, 'Aina'] = e_cat
                    st.session_state.df.at[edit_idx, 'Kitu'] = e_item
                    st.session_state.df.at[edit_idx, 'Kiasi'] = e_amount
                    save_data(worksheet, st.session_state.df) # HII NI MUHIMU
                    st.success("Imesasishwa kwenye Cloud!")
                    st.rerun()
    else:
        st.warning("Hakuna data.")

# TAB 3: DASHBOARD
with tab3:
    st.header("Muonekano wa Pesa")
    if not st.session_state.df.empty:
        df_calc = st.session_state.df.copy()
        df_calc['Tarehe'] = pd.to_datetime(df_calc['Tarehe'])
        
        # FILTER
        st.subheader("🗓️ Chagua Kipindi")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Mwanzo", value=df_calc['Tarehe'].min())
        with col2:
            end_date = st.date_input("Mwisho", value=df_calc['Tarehe'].max())
            
        mask = (df_calc['Tarehe'] >= pd.to_datetime(start_date)) & (df_calc['Tarehe'] <= pd.to_datetime(end_date))
        filtered_df = df_calc.loc[mask]
        filtered_df['Aina'] = filtered_df['Aina'].str.lower().str.strip()
        
        # HESABU
        income = filtered_df[filtered_df['Aina'] == 'mapato']['Kiasi'].sum()
        expense = filtered_df[filtered_df['Aina'] != 'mapato']['Kiasi'].sum()
        balance = income - expense
        
        # METRIKI
        m1, m2, m3 = st.columns(3)
        m1.metric("Jumla Mapato", f"{income:,.0f} TSh")
        m2.metric("Jumla Matumizi", f"{expense:,.0f} TSh")
        m3.metric("Salio", f"{balance:,.0f} TSh")
        
        # CHATI
        st.subheader("Grafu ya Matumizi")
        expense_data = filtered_df[filtered_df['Aina'] != 'mapato']
        if not expense_data.empty:
            st.bar_chart(expense_data.groupby('Aina')['Kiasi'].sum())
        else:
            st.info("Hakuna data kwenye kipindi hiki.")
    else:
        st.info("Bado hakuna data.")