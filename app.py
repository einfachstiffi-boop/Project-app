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
st.markdown("""Discover concerts fitting your personal preference and music taste.""") #This is the title and the subtitle of our app

st.divider()

st.subheader("Tell us about your music taste")

energy = st.slider("**ENERGY**: this describes the how hyped up you want to be when listening to music", 0.0, 1.0, 0.5)
tempo = st.slider("**TEMPO**: really selfexplanatory either fast paced or slow paced music", 40.0, 220.0, 120.0)
danceability = st.slider("**DANCEABILITY**: just imagine your music taste in the Club and if the crowd would go crazy for it", 0.0, 1.0, 0.5)
loudness = st.slider("**LOUDNESS**: really selfexplanatory as well", -60.0, 0.0, -8.0)
time_signature = st.slider("**TIME SIGNATURE**: this is the beat pattern of a song", 1, 7, 4)
speechiness = st.slider("**SPEECHINESS**: this describes how much is really spoken in this song or if its more musical", 0.0, 1.0, 0.05)
track_popularity = st.slider("**TRACK POPULARITY**: just think about your music taste and if its more mainstream or more underground", 0, 100, 50)
acousticness = st.slider("**ACOUSTICNESS**: this describes if your music taste uses more natural instruments than it would be more acoustic. Higher value = more acoustic", 0.0, 1.0, 0.3)


ml_features = pd.DataFrame([{
    "energy": energy,
    "tempo": tempo,
    "danceability": danceability,
    "loudness": loudness,
    "time_signature": time_signature,
    "speechiness": speechiness,
    "track_popularity": track_popularity,
    "acousticness": acousticness
}])

predicted_bin = model.predict(ml_features)[0]


st.divider()

#User Inputs
st.write("📍 Tell us the city you want to find a concert in!")    #This is a command for the User to insert the name of the city where they want to find the concert in

col1, col2, col3 = st.columns(3)
with col1:
    city = st.text_input("Insert the city here.") #here is the input field for the city name 
with col2:
     option = st.selectbox(
    "What country would you want to search in?",
    ("DE", "AT", "CH"),
    ) #here we can select the country which will be implemented into the API
with col3:
    start_date = st.date_input("Which date do you want to start looking for?", value=date.today()) #here they can select the starting date for which the user wants to find ongoing concerts

st.divider()


search = st.button("🔎 Search in City") #thats just the button to start the process/search

bin1 = [
'Hip-Hop/Rap','Pop','Reggae','Dance','R&B'
]

bin2 = [
    'Blues','Country'
]

bin3 = [
'Jazz','Miscellaneous Theatre','Theatre','Alternative','Classical','Fairs & Festivals',
]

bin4 = [
'Hockey',  'Undefined','Metal','Dance/Electronic','Miscellaneous','Other',
    'Rock',
] 


def map_event_to_bin(genre):
    if genre in bin1:
        return "bin1"
    if genre in bin2:
        return "bin2"
    if genre in bin3:
        return "bin3"
    return "bin4"
def concerts_API(city: str, start: date, predicted_bin, option: str):

    params = {
        "apikey": API_KEY,
        "countryCode": option,
        "classificationName": "Music",
        "size": 100,
        "city": city,
        "startDateTime": start.strftime("%Y-%m-%dT00:00:00Z")
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
        start_info = ev.get("dates", {}).get("start", {})
        local_date = start_info.get("localDate")
        local_time = start_info.get("localTime")

        classifications = ev.get("classifications", [])
        genre_name = None
        if classifications:
            genre = classifications[0].get("genre") or {}
            genre_name = genre.get("name")

        venues = ev.get("_embedded", {}).get("venues", [])
        venue_name = None
        city_name = None
        lat = None
        lon = None
        if venues:
            v = venues[0]
            venue_name = v.get("name")
            city_name = v.get("city", {}).get("name")
            loc = v.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")

        url = ev.get("url")

        rows.append({
            "name": name,
            "date": local_date,
            "time": local_time,
            "city": city_name,
            "genre": genre_name,
            "venue": venue_name,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "url": url,
        })

    df = pd.DataFrame(rows)

    df["event_bin"] = df["genre"].apply(map_event_to_bin)
    df = df[df["event_bin"] == predicted_bin]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.sort_values(by=["date", "time"], ascending=True)
    df = df.reset_index(drop=True)
    df["id"] = df.index

    return df




      
#Search
#Search
if search and city.strip() != "":
    with st.spinner("Searching for concerts..."):
        st.session_state["concerts"] = concerts_API(
            city.strip(),
            start_date,
            predicted_bin,
            option
        )

 #sort_concerts_by_genre_by_ai(options)   #here we convert the information the user gave us like the city and starting date

concerts = st.session_state.get('concerts', pd.DataFrame())

if concerts.empty:
    if search:
        st.warning(f"🙁 No concerts from {start_date} in {city} found.") #when there are no events it will be displayed that there are no events in this city/at that time
    else:
        st.info("Insert your desired city and press *Search*.")
else:
    st.success(f"🎉 {len(concerts)} Concerts found in {city}!")  #if there are concerts it will be displayed that concerts were found

    st.subheader("🎵 Concerts found") #this is just a small text that concerts were found
    display_df = concerts.copy()  
        
    if "url" in display_df.columns:
        display_df["Ticket-Link"] = display_df["url"] #here we just display the url in the table as the ticket link
        st.dataframe(
            display_df,
            column_config={
                "Ticket-Link": st.column:config.LinkColumn(
                    "Ticket Link",
                     display_text = "Open Event"
        )
        }
        )

        display_df = display_df[["name", "genre", "date", "time", "venue", "city", "Ticket-Link"]] #these are the columns in the table from the rows we defined before
    else:
        display_df = display_df[["name", "genre", "date", "time", "venue", "city"]] #if there is no url available than theres no ticket link
            
 
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
