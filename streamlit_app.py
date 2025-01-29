import streamlit as st
import requests
import pandas as pd
from io import StringIO
import altair as alt
import pydeck as pdk

# Replace with your Dropbox shared link and modify for direct download
dropbox_url = st.secrets["dropbox_url"]

# Fetch the file content
response = requests.get(dropbox_url)

@st.cache_data
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.reset_index(drop=True)
    return df

if response.status_code == 200:
    csv_data = StringIO(response.text)
    df = load_data(csv_data)
else:
    st.error(f"Failed to fetch file. Status code: {response.status_code}")
    st.stop()

def clean_restaurant_types(df):
    type_mapping = {
        "Restaurang": "Restaurant",
        "Lunchrestaurang": "Restaurant",
        "Exklusiv restaurang": "Restaurant",
        "Vietnamesisk restaurang": "Vietnamese",
        "Indisk restaurang": "Indian",
        "Modern indisk restaurang": "Indian",
        "Kinesisk restaurang": "Chinese",
        "Japansk restaurang": "Japanese",
        "Koreansk restaurang": "Korean",
        "Thailändsk restaurang": "Thai",
        "Asiatisk restaurang": "Asian",
        "Asiatisk fusionrestaurang": "Asian Fusion",
        "Ramen-restaurang": "Japanese",
        "Palestinsk restaurang": "Palestinian",
        "Persisk restaurang": "Persian",
        "Turkisk restaurang": "Turkish",
        "Grekisk restaurang": "Greek",
        "Medelhavsrestaurang": "Mediterranean",
        "Etiopisk restaurang": "Ethiopian",
        "Argentinsk restaurang": "Argentinian",
        "Sydamerikansk restaurang": "South American",
        "Baskisk restaurang": "Basque",
        "Amerikansk restaurang": "American",
        "Svensk restaurang": "Swedish",
        "Fransk restaurang": "French",
        "Italiensk restaurang": "Italian",
        "Skandinavisk restaurang": "Scandinavian",
        "Europeisk restaurang": "European",
        "Modern europeisk restaurang": "Modern European",
        "Polsk restaurang": "Polish",
        "Tjeckisk restaurang": "Czech",
        "Nepalesisk restaurang": "Nepalese",
        "Bulgarisk restaurang": "Bulgarian",
        "Sushirestaurang": "Sushi",
        "Fiskrestaurang": "Seafood",
        "Fisk- och skaldjursrestaurang": "Seafood",
        "Kycklingrestaurang": "Chicken",
        "Kötträtter, restaurang": "Steakhouse",
        "Pizzeria": "Pizza",
        "Tacorestaurang": "Tacos",
        "Tapasrestaurang": "Tapas",
        "Tapasbar": "Tapas",
        "Hamburgerrestaurang": "Burgers",
        "Grillrestaurang": "Grill",
        "Brasserie": "Brasserie",
        "Bistro": "Bistro",
        "Gastropub": "Gastropub",
        "Vinbar": "Wine Bar",
        "Bar och grill": "Bar & Grill",
        "Bryggeripub": "Brewery Pub",
        "Fusion, restaurang": "Fusion",
    }
    df["cleaned_type"] = df["type"].map(type_mapping).fillna(df["type"])
    return df

df = clean_restaurant_types(df)

st.title("🫕 Gothenburg's Restaurants 🍖")
st.caption("A.K.A what should we eat?")

# ---------- Filter controls in columns ----------
col1, col2 = st.columns([2, 1])

with col1:
    # Range slider
    min_rating, max_rating = st.slider(
        "Select rating range",
        min_value=float(df["rating"].min()),
        max_value=float(df["rating"].max()),
        value=(float(df["rating"].min()), float(df["rating"].max())),
        step=0.1,
        format="%.1f"
    )

with col2:
    all_types = sorted(df["cleaned_type"].dropna().unique())
    type_options = ["All"] + all_types
    selected_type = st.selectbox("Select restaurant Type", type_options)

# ---------- Apply Filters ----------
filtered_df = df[(df["rating"] >= min_rating) & (df["rating"] <= max_rating)]
if selected_type != "All":
    filtered_df = filtered_df[filtered_df["cleaned_type"] == selected_type]

st.dataframe(filtered_df[["title", "rating", "reviews", "cleaned_type"]], use_container_width=True)


# ---------- Prepare map data ----------
map_df = filtered_df.dropna(subset=["latitude", "longitude"])

if not map_df.empty:
    # Determine a good center for the map (e.g., mean lat/lon or a fixed location)
    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

    # Define the initial view state
    initial_view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=12,          # Adjust for your city scale
        pitch=0
    )

    # Create a ScatterplotLayer to control marker size, color, and tooltips
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        pickable=True,              # Enable tooltip "picking"
        get_position="[longitude, latitude]",
        get_radius=50,              # Radius in *meters*; increase for bigger dots
        get_fill_color=[255, 0, 0], # Red markers (R, G, B)
        get_line_color=[0, 0, 0],   # Optional: marker outline color
        line_width_min_pixels=1
    )

    # Configure the tooltip to show restaurant name
    # You can display other fields with {field_name} placeholders
    tooltip = {
        "html": "<b>Restaurant:</b> {title}<br/><b>Rating:</b> {rating}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    # Build the Deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=initial_view_state,
        tooltip=tooltip
    )

    # Display the map
    st.pydeck_chart(deck)
else:
    st.write("No valid coordinates to display on the map.")

# ---------- Histogram & Average side by side ----------
col_hist, col_avg = st.columns([3, 1])


with col_hist:
    # Small header (caption) for the histogram
    st.caption("Rating Distribution")

    hist = (
        alt.Chart(filtered_df)
        .transform_bin(
            "bin_rating",
            field="rating",
            bin=alt.Bin(step=0.1)
        )
        .mark_bar(color="#4C78A8", opacity=0.7)
        .encode(
            x=alt.X("bin_rating:Q", axis=alt.Axis(format=".1f", title="Rating")),
            y=alt.Y("count()", title="Count"),
            tooltip=["count()"]
        )
        .properties(width=600, height=300)
        .interactive()
    )
    st.altair_chart(hist, use_container_width=True)

with col_avg:
    # Small header (caption) for the average rating
    st.caption("Average Rating")

    if len(filtered_df) > 0:
        avg_rating = filtered_df["rating"].mean()
        # Create a simple centered box with HTML/CSS
        box_html = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid #ccc;
            border-radius: 6px;
            background-color: transparent;
            padding: 20px;
            margin-top: 10px;
        ">
            <span style="font-size:24px; font-weight: 600;">{avg_rating:.2f}</span>
        </div>
        """
        st.markdown(box_html, unsafe_allow_html=True)
    else:
        st.write("No restaurants found.")

