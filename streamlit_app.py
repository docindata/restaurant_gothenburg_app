import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

import requests
import pandas as pd
from io import StringIO

# Replace with your Dropbox shared link and modify for direct download
dropbox_url = st.secrets["dropbox_url"]
# Fetch the file content
response = requests.get(dropbox_url)

# Check if the request was successful
if response.status_code == 200:
    print("File fetched successfully!")
    
    # Convert the content into a DataFrame
    csv_data = StringIO(response.text)
    df = pd.read_csv(csv_data).loc[:,["title", "rating", "reviews", "type"]]
    
    
    # Display the DataFrame
    print(df.head())
else:
    print(f"Failed to fetch file. Status code: {response.status_code}")


st.dataframe(df)

