import streamlit as st
import requests
import pandas as pd
from io import StringIO

# Replace with your Dropbox shared link and modify for direct download
dropbox_url = st.secrets["dropbox_url"]
# Fetch the file content
response = requests.get(dropbox_url)

@st.cache_data # Decorator to save data as cache
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.reset_index(drop=True)
    return df


# Check if the request was successful
if response.status_code == 200:
    print("File fetched successfully!")
    
    # Convert the content into a DataFrame
    csv_data = StringIO(response.text)

    df = load_data(csv_data).loc[:,["title", "rating", "reviews", "type", "address"]]
    
    
    # Display the DataFrame
    print(df.head())
else:
    print(f"Failed to fetch file. Status code: {response.status_code}")

# Display Restaurants with Styled Cards
st.write("### What should we eat?")

st.sidebar.header("🔎 Search & Filters")
search_query = st.sidebar.text_input("Search for a restaurant")
selected_type = st.sidebar.multiselect("Filter by Type", options=df['type'].unique())

st.write(df)