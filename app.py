import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import random
import requests 
from datetime import date

API_KEY = "0ASKD9hz3j4tj0pfBUULLIoe52liTcZf"
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

response = requests.get(url)
data = response.json()

st.set_page_config(page_title="Swiss Canton Capitals Events", layout="wide")
st.title("Swiss Events")

st.write("Tell us the city you want to find a concert in!")

city = st.text_input("Insert the city here.")

start_date = st.date_input("Which date do you want to start looking for?", value=date.today())

search = st.button("Search")

def get_concerts_from_ticketmaster(city: str, start: date):
    params = {
        "apikey": API_KEY,
        "countryCode": "CH",
        "classificationName": "Music",
        "size": 100,
        "city": city,
        "startDateTime": start.strftime("%Y-%m-%dT00:00:00Z"),
    }

    resp = requests.get(BASE_URL, params=params)
    if resp-status_code != 200:
        st.error(f"Error with the API request ({resp.status_code})")
        return pd.DataFrame()

    data = resp.json()

    events = data.get("_embedded", {}).get("events", [])
    if not events:
        return pd.DataFrame()

    rows = []
    for ev in events:
        name = ev.get("name")
        dates = ev.get("dates", {})
        start_info = dates.get("start", {})
        local_date = start_info.get("localDate")
        local_time = start_info.get("localTime")

        venue_name = None
        city_name = None
        lat = None
        lon = None

        embedded = ev.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            v = venues[0]
            venue_name = v.get("name")
            city_name = v.get("city", {}).get("name")
            loc = v.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")

        url = ev.get("url")

        rows.append(
            {
                "name": name,
                "date": local_date,
                "time": local_time,
                "city": city_name,
                "venue": venue_name,
                "lat": float(lat) if lat is not None else None,
                "lon": float(lon) if lon is not None else None,
                "url": url,
            }
        )

     df = pd.DataFrame(rows)

     if "date" in df.columns:
         df["date"] = pd.to_datetime(df["date"]).dt.date

     df = df.sort_values(by=["date", "time"], ascending=True)

     return df

if search and city.strip() != "":
    concerts = get_concerts_from_ticketmaster(stadt.strip(), start_date)

    if concerts.empty:
        st.warning(f"No concerts from {start_date} in {city} found.")

        st.subheader("Concerts found")
        display_df = concerts.copy()
        display_df["Ticket-Link"] = display_df["url"]
        display_df = display_df[["name", "date", "time", "venue", "city", "Ticket-Link"]]
        st.dataframe(dsiplay_df)

        map_df = concerts.dropna(subset=["lat, "lon"])
        if not map_df.empty:
            st.subheader("Map")
            st.map(map_df[["lat", "lon"]])
        else:
            st.info("For those Events there is no Map avaiable.")
else:
    st.info("Insert your desired City and press **Search**.")                             

@st.cache_data
def load_data():
    capitals = {
        "Zurich": [47.3769, 8.5417],
        "Bern": [46.9481, 7.4474],
        "Lucerne": [47.0502, 8.3093],
        "Uri": [46.8747, 8.6389],
        "Schwyz": [47.0207, 8.6536],
        "Obwalden": [46.9200, 8.2900],
        "Nidwalden": [46.9217, 8.3422],
        "Glarus": [47.0406, 9.0684],
        "Zug": [47.1712, 8.5155],
        "Fribourg": [46.8065, 7.1619],
        "Solothurn": [47.2087, 7.5326],
        "Basel": [47.5596, 7.5886],
        "Schaffhausen": [47.6980, 8.6359],
        "Appenzell": [47.3482, 9.4074],
        "St. Gallen": [47.4239, 9.3744],
        "Graubünden": [46.8496, 9.5300],
        "Aargau": [47.3926, 8.0446],
        "Thurgau": [47.5247, 9.0524],
        "Ticino": [46.0037, 8.9511],
        "Vaud": [46.5197, 6.6323],
        "Valais": [46.2276, 7.3606],
        "Neuchâtel": [46.9910, 6.9293],
        "Geneva": [46.2044, 6.1432],
        "Jura": [47.3493, 7.1510]
    }

    # Define city sizes for weighted event counts
    city_size_weight = {
        "Zurich": "large", "Geneva": "large", "Basel": "large", "Bern": "large", "Lausanne": "large",
        "Lucerne": "medium", "St. Gallen": "medium", "Lugano": "medium", "Fribourg": "medium", "Solothurn": "medium",
        "Schaffhausen": "small", "Appenzell": "small", "Glarus": "small", "Uri": "small", "Obwalden": "small",
        "Nidwalden": "small", "Zug": "medium", "Graubünden": "small", "Aargau": "medium", "Thurgau": "medium",
        "Ticino": "medium", "Valais": "medium", "Neuchâtel": "medium", "Jura": "small"
    }

    event_types = ["Concert", "Festival", "Exhibition", "Conference", "Market", "Art Show", "Seminar", "Fair"]

    data = []
    for city in capitals.keys():
        size = city_size_weight.get(city, "small")
        if size == "large":
            num_events = random.randint(6, 10)
        elif size == "medium":
            num_events = random.randint(3, 6)
        else:  # small
            num_events = random.randint(1, 3)
        for i in range(num_events):
            data.append({
                "city": city,
                "event_type": random.choice(event_types),
                "date": f"2025-12-{i+1:02d}"
            })

    df = pd.DataFrame(data)
    return df, capitals

# Load data
df, capitals = load_data()

# ---- BAR CHART ----
st.subheader("Number of Events per City")
event_counts = df.groupby("city").size()

fig, ax = plt.subplots(figsize=(12,6))
event_counts.plot(kind="bar", color="skyblue", ax=ax)
ax.set_ylabel("Number of Events")
ax.set_xlabel("City")
ax.set_ylim(1, 10)
plt.xticks(rotation=45, ha='right')
st.pyplot(fig)

# ---- INTERACTIVE MAP ----
st.subheader("Map of Events")
m = folium.Map(location=[46.8, 8.2], zoom_start=7)

for city, coords in capitals.items():
    events_for_city = df[df["city"] == city]
    popup_text = f"<b>{city}</b><br>"
    for _, row in events_for_city.iterrows():
        popup_text += f"{row['event_type']} ({row['date']})<br>"
    folium.Marker(
        location=coords,
        popup=popup_text,
        tooltip=city
    ).add_to(m)

st_folium(m, width=700, height=500)
