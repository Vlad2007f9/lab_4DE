import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px

st.set_page_config(page_title = "Metals Dashboard", layout="wide")

if not firebase_admin._apps:
    cred = credentials.Certificate('lab3-de-firebase-adminsdk-fbsvc-21a58ed6f5.json')
    firebase_admin.initialize_app(cred, {'databaseURL' : 'https://lab3-de-default-rtdb.firebaseio.com'})


@st.cache_data
def load_data():
    ref = db.reference('historical_data')
    data = ref.get()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(data, orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Date'}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])
    for col in df.columns:
        if col != 'Date':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.sort_values('Date').reset_index(drop=True)
    return df

df = load_data()

if df.empty:
    st.error("No data available")
    st.stop()

st.sidebar.header('Панель керуванння')

metals = [col for col in df.columns if col != 'Date']

selected_metals = st.sidebar.multiselect("Оберіть метали:", options=metals, default=metals[:2] if len(metals) >= 2 else metals)

min_date = df['Date'].min()
max_date = df['Date'].max()

start_date = st.sidebar.date_input("Дата початку:", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Дата кінця:", value=max_date, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.sidebar.error("Помилка: Дата початку не може бути більшою за дату кінця.")
    st.stop()

days_count = st.sidebar.slider('Кількість попередніх днів для перегляду в таблиці:', min_value=1, max_value=30, value=5)

st.title("Фінансова інформаційна панель (Metals Dashboard)")
st.markdown("Візуалізація історичних даних, отриманих з **Firebase Realtime Database**")


mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
df_filtered = df.loc[mask]

if not selected_metals:
    st.warning('Будь ласка, оберіть хоча б один метал у бічній панелі')
    st.stop()

st.subheader('Динаміка цін для обраних значеннь')

df_melted = df_filtered.melt(id_vars=['Date'], value_vars=selected_metals, var_name='Asset', value_name='Price' )

fig = px.line(df_melted, x='Date', y="Price", color='Asset', labels={'Price' : 'Ціна(USD)', 'Date' : 'Дата', 'Assets' : 'Актив'})

fig.update_layout(hovermode='x unified', height=500)
st.plotly_chart(fig, use_container_width=True)

if not df_filtered.empty:
    df_recent = df_filtered[['Date'] + selected_metals].tail(days_count).sort_values('Date', ascending=False)
    df_recent['Date'] = df_recent['Date'].dt.strftime('%Y-%m-%d')

    st.dataframe(df_recent, use_container_width=True, hide_index=True)
else:
    st.info("Немає даних для відображення за обраний період")