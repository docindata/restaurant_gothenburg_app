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
        st.error(f"Misslyckades att hämta filen. Statuskod: {response.status_code}")
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
    "Restaurang": "Restaurang",
    "Lunchrestaurang": "Restaurang",
    "Exklusiv restaurang": "Restaurang",
    "Vietnamesisk restaurang": "Vietnamesisk",
    "Indisk restaurang": "Indisk",
    "Modern indisk restaurang": "Indisk",
    "Kinesisk restaurang": "Kinesisk",
    "Japansk restaurang": "Japansk",
    "Koreansk restaurang": "Koreansk",
    "Thailändsk restaurang": "Thailändsk",
    "Asiatisk restaurang": "Asiatisk",
    "Asiatisk fusionrestaurang": "Asiatisk fusion",
    "Ramen-restaurang": "Japansk",
    "Palestinsk restaurang": "Palestinsk",
    "Persisk restaurang": "Persisk",
    "Turkisk restaurang": "Turkisk",
    "Grekisk restaurang": "Grekisk",
    "Medelhavsrestaurang": "Medelhavs",
    "Etiopisk restaurang": "Etiopisk",
    "Argentinsk restaurang": "Argentinsk",
    "Sydamerikansk restaurang": "Sydamerikansk",
    "Baskisk restaurang": "Baskisk",
    "Amerikansk restaurang": "Amerikansk",
    "Svensk restaurang": "Svensk",
    "Fransk restaurang": "Fransk",
    "Italiensk restaurang": "Italiensk",
    "Skandinavisk restaurang": "Skandinavisk",
    "Europeisk restaurang": "Europeisk",
    "Modern europeisk restaurang": "Modern europeisk",
    "Polsk restaurang": "Polsk",
    "Tjeckisk restaurang": "Tjeckisk",
    "Nepalesisk restaurang": "Nepalesisk",
    "Bulgarisk restaurang": "Bulgarisk",
    "Sushirestaurang": "Sushi",
    "Fiskrestaurang": "Fisk",
    "Fisk- och skaldjursrestaurang": "Fisk & skaldjur",
    "Kycklingrestaurang": "Kyckling",
    "Kötträtter, restaurang": "Biffrestaurang",
    "Pizzeria": "Pizzeria",
    "Tacorestaurang": "Tacos",
    "Tapasrestaurang": "Tapas",
    "Tapasbar": "Tapas",
    "Hamburgerrestaurang": "Hamburgare",
    "Grillrestaurang": "Grill",
    "Brasserie": "Brasserie",
    "Bistro": "Bistro",
    "Gastropub": "Gastropub",
    "Vinbar": "Vinbar",
    "Bar och grill": "Bar & Grill",
    "Bryggeripub": "Bryggeripub",
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
    map_df = df.dropna(subset=["latitude", "longitude"])
    if map_df.empty:
        st.write("Inga giltiga koordinater att visa på kartan.")
        return

    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

    initial_view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=12,
        pitch=0
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        pickable=True,
        get_position="[longitude, latitude]",
        get_radius=50,
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1
    )

    tooltip = {
        "html": "<b>Restaurang:</b> {title}<br/><b>Betyg:</b> {rating}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

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
    hist = (
        alt.Chart(df)
        .transform_bin(
            "bin_rating",
            field="rating",
            bin=alt.Bin(step=0.1)
        )
        .mark_bar(color="#4C78A8", opacity=0.7)
        .encode(
            x=alt.X("bin_rating:Q", axis=alt.Axis(format=".1f", title="Betyg")),
            y=alt.Y("count()", title="Antal"),
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
        st.write("Inga restauranger hittades.")

def display_creator_name(str='Skapad av Hashim Al-Haboobi'):
    st.caption(str)

# -------------------------------------------------------------------
# 4. Main Application Flow
# -------------------------------------------------------------------

def main():
    # Hämta data från Dropbox (direktlänk i secrets)
    dropbox_url = st.secrets["dropbox_url"]
    df = fetch_data_from_dropbox(dropbox_url)

    # Rensa upp restaurangtyper
    df = clean_restaurant_types(df)

    # Titel & beskrivning
    st.title("🫕 Göteborgs Restauranger 🍖")
    st.caption("a.k.a What should we eat?")

    # Skapa två kolumner för filter
    col1, col2 = st.columns([2, 1])

    with col1:
        # Välj betygsintervall
        min_val, max_val = float(df["rating"].min()), float(df["rating"].max())
        rating_range = st.slider(
            "Välj betygsintervall",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=0.1,
            format="%.1f"
        )

    with col2:
        # Välj restaurangtyp
        all_types = sorted(df["cleaned_type"].dropna().unique())
        type_options = ["All"] + all_types
        selected_type = st.selectbox("Välj restaurangtyp", type_options)

    # Filtrera data
    filtered_df = filter_restaurants(df, rating_range, selected_type)

    # Visa tabell över filtrerade data
    st.dataframe(
        filtered_df[["title", "rating", "reviews", "cleaned_type"]]
        .rename(columns={
            "title": "Namn",
            "rating": "Betyg",
            "reviews": "Recensioner",
            "cleaned_type": "Typ"
        }),
        use_container_width=True
    )

    # Visa karta
    display_map(filtered_df)

    # Visa histogram & genomsnittsbetyg
    col_hist, col_avg = st.columns([3, 1])

    with col_hist:
        st.caption("Betygsfördelning")
        if len(filtered_df) > 0:
            display_histogram(filtered_df)
        else:
            st.write("Ingen data att visualisera.")

    with col_avg:
        st.caption("Genomsnittligt Betyg")
        display_average_rating(filtered_df)

    display_creator_name()

# Kör appen
if __name__ == "__main__":
    main()
