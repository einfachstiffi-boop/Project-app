import streamlit as st

st.write("Hello World")

if look and artist.strip() != "": #here we validate that the city insert field is not empty else it will show the error message at the end of this code
    with st.spinner("Searching for artists..."):
        st.session_state['concerts'] = get_artists_from_ticketmaster(artist.strip(), start_date) #sort_concerts_by_genre_by_ai(options)   #here we convert the information the user gave us like the city and starting date

artists = st.session_state.get('concerts', pd.DataFrame())

if artists.empty:
    if look:
        st.warning(f"🙁 No concerts from {artist} found.") #when there are no events it will be displayed that there are no events in this city/at that time
    else:
        st.info("Insert your desired artist and press **Search**.")
else:
    st.success(f"🎉 {len(artists)} Concerts found from {artist}!")  #if there are concerts it will be displayed that concerts were found

    st.subheader("artist found") #this is just a small text that concerts were found
    display_df = artists.copy()  
        
    if "url" in display_df.columns:
        display_df["Ticket-Link"] = display_df["url"]  #here we just display the url in the table as the ticket link
        display_df = display_df[["name", "date", "time", "venue", "city", "Ticket-Link"]] #these are the columns in the table from the rows we defined before
    else:
        display_df = display_df[["name", "date", "time", "venue", "city"]] #if there is no url available than theres no ticket link
            
    st.dataframe(display_df) #here we display the table on the app

    map_df = artists.dropna(subset=["lat", "lon"]) 
    if not map_df.empty:
        st.subheader("Map of Concerts")
        m = folium.Map(location=[map_df["lat"].mean(), map_df["lon"].mean()], zoom_start=10) #here we center the map around the average coordinates
        marker_cluster = MarkerCluster().add_to(m) #here we cluster nerby markers

        for idx, row in map_df.iterrows():
            popup_html = f"""
            <b>{row['name']}</b><br>
            📍 {row['venue']}, {row['city']}<br>
             📅 {row['date']} {row['time']}<br>
             {'<a href="' + row['url'] + '" target="_blank">🎟️ Tickets</a>' if row.get('url') else ''} #here we create the content that will appear when you click on the marker
            """
            folium.Marker(
                location = [row["lat"], row["lon"]],
                popup = popup_html,
                icon=folium.Icon(color = 'blue', icon = 'music', prefix = 'fa')
            ).add_to(marker_cluster) #here we create the folium marker 
                
        st_folium(m, height=500)
           
    else:
        st.info("For these events there is no map avaiable.")  #if this information is not available theres just not a map displayed and this text will show
