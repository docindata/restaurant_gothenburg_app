import streamlit as st
import requests
import pandas as pd
from io import StringIO
import altair as alt
import pydeck as pdk

# -------------------------------------------------------------------
# 1. Data Fetching & Loading
# -------------------------------------------------------------------

@st.cache_data
def load_data_from_csv(csv_text):
    """
    Load data from CSV content (in-memory text), 
    reset index, and return the DataFrame.
    """
    df = pd.read_csv(csv_text)
    df = df.reset_index(drop=True)
    return df

def fetch_data_from_dropbox(dropbox_url):
    """
    Fetch the CSV file content from Dropbox using an HTTP GET request.
    Return the loaded DataFrame if successful, or stop the app with an error.
    """
    response = requests.get(dropbox_url)
    
    if response.status_code == 200:
        csv_content = StringIO(response.text)
        return load_data_from_csv(csv_content)
    else:
        st.error(f"Failed to fetch file. Status code: {response.status_code}")
        st.stop()


# -------------------------------------------------------------------
# 2. Data Cleaning
# -------------------------------------------------------------------

def clean_restaurant_types(df):
    """
    Map Swedish restaurant types to English (e.g. 'Kinesisk restaurang' -> 'Chinese').
    Stores result in a new column 'cleaned_type'.
    """
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


# -------------------------------------------------------------------
# 3. Filters & Visualization Helpers
# -------------------------------------------------------------------

def filter_restaurants(df, rating_range, selected_type):
    """
    Given a DataFrame 'df', filter by the specified rating range 
    and 'cleaned_type' if selected_type != 'All'.
    Returns the filtered DataFrame.
    """
    min_rating, max_rating = rating_range
    filtered = df[(df["rating"] >= min_rating) & (df["rating"] <= max_rating)]
    
    if selected_type != "All":
        filtered = filtered[filtered["cleaned_type"] == selected_type]
    
    return filtered

def display_map(df):
    """
    Given a DataFrame with valid latitude and longitude columns,
    create a PyDeck ScatterplotLayer and display it on a Streamlit map.
    """
    # Drop rows with missing lat/lon
    map_df = df.dropna(subset=["latitude", "longitude"])
    
    if map_df.empty:
        st.write("No valid coordinates to display on the map.")
        return

    # Calculate a center for the map (average lat/lon)
    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

    # Define the initial map view
    initial_view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=12,  # Adjust for your city scale
        pitch=0
    )

    # ScatterplotLayer for the markers
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        pickable=True,
        get_position="[longitude, latitude]",
        get_radius=50,              # Marker size in meters
        get_fill_color=[255, 0, 0], # Red markers (RGB)
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1
    )

    # Configure hover tooltip
    tooltip = {
        "html": "<b>Restaurant:</b> {title}<br/><b>Rating:</b> {rating}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    # Build the deck and display
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=initial_view_state,
        tooltip=tooltip
    )
    st.pydeck_chart(deck)

def display_histogram(df):
    """
    Given a DataFrame, create an Altair histogram of 'rating'.
    """
    # Transform the rating into bins of size 0.1
    hist = (
        alt.Chart(df)
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

def display_average_rating(df):
    """
    Display the average rating of the given DataFrame in a styled box.
    If the DataFrame is empty, shows a placeholder message.
    """
    if len(df) > 0:
        avg_rating = df["rating"].mean()
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


# -------------------------------------------------------------------
# 4. Main Application Flow
# -------------------------------------------------------------------

def main():
    # Fetch data from Dropbox (direct download link in secrets)
    dropbox_url = st.secrets["dropbox_url"]
    df = fetch_data_from_dropbox(dropbox_url)

    # Clean the restaurant types
    df = clean_restaurant_types(df)

    # Title & caption
    st.title("🫕 Gothenburg's Restaurants 🍖")
    st.caption("A.K.A what should we eat?")

    # Create two columns for filters
    col1, col2 = st.columns([2, 1])

    with col1:
        # Rating range slider
        min_val, max_val = float(df["rating"].min()), float(df["rating"].max())
        rating_range = st.slider(
            "Select rating range",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=0.1,
            format="%.1f"
        )

    with col2:
        # Restaurant type selector
        all_types = sorted(df["cleaned_type"].dropna().unique())
        type_options = ["All"] + all_types
        selected_type = st.selectbox("Select restaurant Type", type_options)

    # Apply filters
    filtered_df = filter_restaurants(df, rating_range, selected_type)

    # Display a table of filtered data
    st.dataframe(filtered_df[["title", "rating", "reviews", "cleaned_type"]], use_container_width=True)

    # Show map of filtered data
    display_map(filtered_df)

    # Show histogram & average rating side by side
    col_hist, col_avg = st.columns([3, 1])

    with col_hist:
        st.caption("Rating Distribution")
        if len(filtered_df) > 0:
            display_histogram(filtered_df)
        else:
            st.write("No data to visualize.")

    with col_avg:
        st.caption("Average Rating")
        display_average_rating(filtered_df)

# Run the app
if __name__ == "__main__":
    main()
