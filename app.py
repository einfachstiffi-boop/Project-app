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
    if resp.status_code != 200:
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
    concerts = get_concerts_from_ticketmaster(city.strip(), start_date)

    if concerts.empty:
        st.warning(f"No concerts from {start_date} in {city} found.")

        st.subheader("Concerts found")
        display_df = concerts.copy()
        
        if "url" in display_df.columns:
            display_df["Ticket-Link"] = display_df["url"]
            display_df = display_df[["name", "date", "time", "venue", "city", "Ticket-Link"]]
        else:
            display_df = display_df[["name", "date", "time", "venue", "city"]]
            
        st.dataframe(dsiplay_df)

        map_df = concerts.dropna(subset=["lat", "lon"])
        if not map_df.empty:
            st.subheader("Map")
            st.map(map_df[["lat", "lon"]])
        else:
            st.info("For those Events there is no Map avaiable.")
else:
    st.info("Insert your desired City and press **Search**.")                             


