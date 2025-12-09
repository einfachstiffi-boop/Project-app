import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import random
import joblib
import requests 
from datetime import date
from folium.plugins import MarkerCluster


API_KEY = "0ASKD9hz3j4tj0pfBUULLIoe52liTcZf"
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"   #Thats the API key thats being requested including the ticketmaster url with all the concert information

model = joblib.load("model.pkl")

st.set_page_config(page_title="Concert findings", layout="wide")
st.title("🎵✨ Find Your Next Concert!")
st.markdown("""Discover upcoming concerts near you - by city, genre, or your favorite artists.""") #This is the title and the subtitle of our app

st.divider()

#User Inputs
st.write("📍 Tell us the city you want to find a concert in!")    #This is a command for the User to insert the name of the city where they want to find the concert in

col1, col2, col3, col4 = st.columns(4)
with col1:
    city = st.text_input("Insert the city here.") #here is the input field for the city name
with col2:
    artist = st.text_input("Insert the Artist here") #here is the input field for the artist
with col3:
    start_date = st.date_input("Which date do you want to start looking for?", value=date.today()) #here they can select the starting date for which the user wants to find ongoing concerts
with col4:
    option = st.selectbox(
    "What country would you want to search in?",
    ("DE", "AT", "CH"),
    ) #here we can select the country which will be implemented into the API

st.divider()

options = st.multiselect(
    "🎧 What genre are you looking for?",
    ["Pop", "Rock", "Hip-Hop / Rap", "R&B", "Jazz", "Blues", "Classical", "Electronic / EDM", "House", "Techno", "Reggae", "Country", "Metal", "Punk", "Soul", "Funk", "Disco", "Folk", "Latin", "Gospel"],
    default=["Pop", "Rock"],
) #here the user can select multiple music genres they are interested in. Pop and rock are used as default music genres

col5, col6 = st.columns(2)
with col5:
    search = st.button("🔎 Search in City") #thats just the button to start the process/search
with col6:
    look = st.button("🎤 Search Artist") 
    
#Functions to get the concerts from the ticketmaster API
def concerts_API(city: str, start: date):
    params = {
        "apikey": API_KEY,
        "countryCode": option,
        "classificationName": "Music",
        "size": 100,
        "city": city,
        "startDateTime": start.strftime("%Y-%m-%dT00:00:00Z"),   #here we def a function so we can request the right information from Ticketmaster for example we clarify music so its concert based and CH so its only for Switzerland also we limit the concerts to 100
    }

    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        st.error(f"Error with the API request ({resp.status_code})")
        return pd.DataFrame()  #here we send a status code to ticketmaster and if it responds everything is fine. If it doesnt respond we send back an empty dataframe

    data = resp.json()  #here the information of the API will get translated into a pyhton library

    events = data.get("_embedded", {}).get("events", [])
    if not events:
        return pd.DataFrame()   #here we try to get the events from ticketmaster if there are no events we return an empty dataframe

    rows = []
    for ev in events:
        name = ev.get("name")
        dates = ev.get("dates", {})
        start_info = dates.get("start", {})
        local_date = start_info.get("localDate")
        local_time = start_info.get("localTime")  #here we start getting the information we need to display like name, dates and the date and time it starts

        venue_name = None  
        city_name = None
        lat = None
        lon = None   #here we define variables so we can display the venue name, and latitude and longitude for the coordinates we need for the display in the map later on

        embedded = ev.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            v = venues[0]
            venue_name = v.get("name")    #here we get the venue name
            city_name = v.get("city", {}).get("name")   
            loc = v.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")   #here we get the location so the longitude/latitude for the coordinates

        url = ev.get("url")  #here we just get the url which will later serve as the Ticket Link

        rows.append(
            {
                "name": name,
                "date": local_date,
                "time": local_time,
                "city": city_name,
                "venue": venue_name,
                "lat": float(lat) if lat is not None else None,
                "lon": float(lon) if lon is not None else None,
                "url": url,  #here we define what information we want to have ready to implement later on in the table and the map, that's like our own library. That's also why longitude and latitude are float variables because they are coordinates for the map
            }
        )

    df = pd.DataFrame(rows) #we convert our own library (rows) into the the DataFrame/table

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.sort_values(by=["date", "time"], ascending=True)

    df = df.reset_index(drop=True)
    df["id"] = df.index

    return df   #here we sort the concerts by date and time so the user knows which concerts are first 

#Search
if search and city.strip() != "": #here we validate that the city insert field is not empty else it will show the error message at the end of this code
    with st.spinner("Searching for concerts..."):
        st.session_state['concerts'] = concerts_API(city.strip(), start_date) #sort_concerts_by_genre_by_ai(options)   #here we convert the information the user gave us like the city and starting date

concerts = st.session_state.get('concerts', pd.DataFrame())

if concerts.empty:
    if search:
        st.warning(f"🙁 No concerts from {start_date} in {city} found.") #when there are no events it will be displayed that there are no events in this city/at that time
    else:
        st.info("Insert your desired city and press **Search**.")
else:
    st.success(f"🎉 {len(concerts)} Concerts found in {city}!")  #if there are concerts it will be displayed that concerts were found

    st.subheader("🎵 Concerts found") #this is just a small text that concerts were found
    display_df = concerts.copy()  
        
    if "url" in display_df.columns:
        display_df["Ticket-Link"] = display_df["url"]  #here we just display the url in the table as the ticket link
        display_df = display_df[["name", "date", "time", "venue", "city", "Ticket-Link"]] #these are the columns in the table from the rows we defined before
    else:
        display_df = display_df[["name", "date", "time", "venue", "city"]] #if there is no url available than theres no ticket link
            
 
    from datetime import date
    display_df["date"] = pd.to_datetime(display_df["date"]).dt.date
    today = date.today()

    def highlight_today(row):
        return [
            "background-color: #fff3cd; font-weight: bold"
            if (col == "date" and row["date"] == today)
            else ""
            for col in display_df.columns
        ]

    st.dataframe (display_df.style.apply(highlight_today, axis=1)) #here we set up a definition which highlight today's date in the dataframe/table
    
#Map Display
    map_df = concerts.dropna(subset=["lat", "lon"]) 
    if not map_df.empty:
        st.divider()
        st.subheader("🗺️ Map of Concerts")
        m = folium.Map(location=[map_df["lat"].mean(), map_df["lon"].mean()], zoom_start=10) #here we center the map around the average coordinates
        marker_cluster = MarkerCluster().add_to(m) #here we cluster nerby markers

        for idx, row in map_df.iterrows():
            
            popup_html = f"""
            <div style="width:200px; text-align:center;">
                <b>{row['name']}</b><br>
                📍 {row['venue']}, {row['city']}<br>
                 📅 {row['date']} {row['time']}<br>
                 {f'<a href="{row["url"]}" target="_blank" style ="text-decoration:none; font-weight:bold;">🎟️ Get Tickets</a>' if row.get('url') else ''} 
            </div>
            """ #here we create the content that will appear when you click on the marker
            
            folium.Marker(
                location = [row["lat"], row["lon"]],
                popup = popup_html,
                icon=folium.Icon(color = 'blue', icon = 'music', prefix = 'fa')
            ).add_to(marker_cluster) #here we create the folium marker 
                
        st_folium(m, height=500, width="100%")
           
    else:
        st.info("For these events there is no map avaiable.")  #if this information is not available theres just not a map displayed and this text will show

def artists_API(artist: str, start: date):
    params = {
        "apikey": API_KEY,
        "countryCode": option,
        "classificationName": "Music",
        "size": 100,
        "name": artist,
        "startDateTime": start.strftime("%Y-%m-%dT00:00:00Z"),   #here we def a function so we can request the right information from Ticketmaster for example we clarify music so its concert based and CH so its only for Switzerland also we limit the concerts to 100
    }

    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        st.error(f"Error with the API request ({resp.status_code})")
        return pd.DataFrame()  #here we send a status code to ticketmaster and if it responds everything is fine. If it doesnt respond we send back an empty dataframe

    data = resp.json()  #here the information of the API will get translated into a pyhton library

    events = data.get("_embedded", {}).get("events", [])
    if not events:
        return pd.DataFrame()   #here we try to get the events from ticketmaster if there are no events we return an empty dataframe

    rows = []
    for ev in events:
        name = ev.get("name")
        dates = ev.get("dates", {})
        start_info = dates.get("start", {})
        local_date = start_info.get("localDate")
        local_time = start_info.get("localTime")  #here we start getting the information we need to display like name, dates and the date and time it starts

        venue_name = None  
        city_name = None
        lat = None
        lon = None   #here we define variables so we can display the venue name, and latitude and longitude for the coordinates we need for the display in the map later on

        embedded = ev.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            v = venues[0]
            venue_name = v.get("name")    #here we get the venue name
            city_name = v.get("city", {}).get("name")   
            loc = v.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")   #here we get the location so the longitude/latitude for the coordinates

        url = ev.get("url")  #here we just get the url which will later serve as the Ticket Link

        rows.append(
            {
                "name": name,
                "date": local_date,
                "time": local_time,
                "city": city_name,
                "venue": venue_name,
                "lat": float(lat) if lat is not None else None,
                "lon": float(lon) if lon is not None else None,
                "url": url,  #here we define what information we want to have ready to implement later on in the table and the map, thats like our own library. Thats also why longitude and latitude are float variables because they are coordinates for the map
            }
        )

    df = pd.DataFrame(rows) #we convert our own library (rows) into the the DataFrame/table

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.sort_values(by=["date", "time"], ascending=True)

    df = df.reset_index(drop=True)
    df["id"] = df.index

    return df
                         
