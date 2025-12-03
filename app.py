import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import random
import requests 
from datetime import date
from openai import OpenAI
import json
import os

openai_api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))

API_KEY = "0ASKD9hz3j4tj0pfBUULLIoe52liTcZf"
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"   #Thats the API key thats being requested including the ticketmaster url with all the concert information

client = OpenAI()

st.set_page_config(page_title="Concert findings", layout="wide")
st.title("Concerts")

st.write("Tell us the city you want to find a concert in!")    #This is a command for the User to insert the name of the city where they wanna find the Concert in

city = st.text_input("Insert the city here.") #here is the input field for the city name

start_date = st.date_input("Which date do you want to start looking for?", value=date.today()) #here they can select the starting date for the time they want to look for the concerts

option = st.selectbox(
    "What country would you want to search in?",
    ("DE", "AT", "CH"),
) #here we can select the country which will be implemented into the api

options = st.multiselect(
    "What genre are you looking for?",
    ["Pop", "Rock", "Hip-Hop / Rap", "R&B", "Jazz", "Blues", "Classical", "Electronic / EDM", "House", "Techno", "Reggae", "Country", "Metal", "Punk", "Soul", "Funk", "Disco", "Folk", "Latin", "Gospel"],
    default=["Pop", "Rock"],
)

search = st.button("Search") #thats just the button to start the process/search

def get_concerts_from_ticketmaster(city: str, start: date):
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
                "url": url,  #here we define what information we want to have ready to implement later on in the table and the map, thats like our own library. Thats also why longitude and latitude are float variables because they are coordinates for the map
            }
        )

    df = pd.DataFrame(rows) #we convert our own library (rows) into the the DataFrame/table

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.sort_values(by=["date", "time"], ascending=True)

    df = df.reset_index(drop=True)
    df["id"] = df.index

    return df   #here we sort the concerts by date and time so they know which concerts are first 

def sort_concerts_by_genre_by_ai(options):
    df = get_concerts_from_ticketmaster(city.strip(), start_date)
    if df.empty:
        return df

    df_for_ai = df[["id", "name", "venue", "city", "date"]].copy()

    df_for_ai["date"] = df_for_ai["date"].astype(str)

    concerts_for_ai = df_for_ai[["id", "name", "venue", "city", "date"]].to_dict(orient="records")

    system_msg = f"""
    You are a strict concert sorter by music genres.
    You will receive a JSON array of Concerts.
    For each concert find if it matches any of the given genres:

    Given genres (human, not strict): {options}
    
    Rules:
    - Output ONLY valid JSON
    - Decide if the concerts fit at lest one of the given genres
    - Return only concerts that match

    Output format (JSON array):
    [
      {{"id": <id_of_concert_to_keep>}},
      ...
    ]
    """
    user_msg = "Here are the concerts to classify:\n\n" + json.dumps(concerts_for_ai, ensure_ascii = False, indent=2)


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content

    kept = json.loads(content)

    kept_ids = {item["id"] for item in kept if "id" in item}

    filtered_df = df[df["id"].isin(kept_ids)].copy()
    return filtered_df

if search and city.strip() != "":  #here we validate that the city insert field is not empty else it will show the error message at the end of this code
    concerts = sort_concerts_by_genre_by_ai(options)   #here we convert the information the user gave us like the city and starting date

    if concerts.empty:
        st.warning(f"No concerts from {start_date} in {city} found.") #when there are no events it will be displayed that there are no events in this city/at that time
    else:
        st.success(f"{len(concerts)} Concerts found in {city}!")  #if there are concerts it will be displayed that concerts were found

        st.subheader("Concerts found") #this is just a small text that concerts were found
        display_df = concerts.copy()  
        
        if "url" in display_df.columns:
            display_df["Ticket-Link"] = display_df["url"]  #here we just display the url in the table as the ticket link
            display_df = display_df[["name", "date", "time", "venue", "city", "Ticket-Link"]] #these are the columns in the table from the rows we defined before
        else:
            display_df = display_df[["name", "date", "time", "venue", "city"]] #if there is no url available than theres no ticket link
            
        st.dataframe(display_df) #here we display the table on the app

        map_df = concerts.dropna(subset=["lat", "lon"]) 
        if not map_df.empty:
            st.subheader("Map")
            st.map(map_df[["lat", "lon"]])  #here we use the coordinates to implement the concerts on the map and display it 
        else:
            st.info("For those Events there is no Map avaiable.")  #if this information is not available theres just not a map displayed and this text will show
else:
    st.info("Insert your desired City and press **Search**.")   #this is just if the user didnt insert a city                          

