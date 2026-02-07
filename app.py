#load all the libraries
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

#add caching decorator so the app isn't slow
@st.cache_data
def load_data(url):
    map_data = pd.read_csv(url)
    #map_data["Drought Risk Score"] = 0.0*map_data["None"] + 0.1*map_data["D0"] + 0.3*map_data["D1"] + 0.4*map_data["D2"] + 0.6*map_data["D3"] + 0.9*map_data["D4"]
    map_data["geometry"] = map_data["geometry"].apply(wkt.loads) 
    return gpd.GeoDataFrame(map_data, crs="EPSG:4326")

map_data = load_data("condensed.csv")    


def environmental_score(gdf, wildfire_user, drought_user, rank):
    #make a copy
    gdf = gdf.copy()

    #compute a proportion of the weight so it is scalable
    total_weight = wildfire_user + drought_user
    wildfire_weight = wildfire_user / total_weight
    drought_weight = drought_user / total_weight

    #compute the risk score
    gdf["Suitability Score"] = (wildfire_weight * gdf["Wildfire Hazard Potential"] +
                                   drought_weight * gdf["Drought Risk Score"])
    
    #rank the counties from the highest to lowest score
    top_gdf = gdf.sort_values(by="Suitability Score", ascending=False).head(rank) #will be fed into the map
    rankings = gdf[["County","State","Suitability Score"]].sort_values(by="Suitability Score", ascending=False).head(rank) #used to display

    rankings = rankings.reset_index(drop=True)
    rankings.index = rankings.index + 1 

    #return values
    return rankings, top_gdf

#create a folium map
def build_map(gdf):
    us_center = [37.0902, -95.7129] #center of the US to start the display

    m = folium.Map(
        location=us_center, 
        tiles = "Cartodb Positron", 
        zoom_start=4
        )
    
    folium.GeoJson(
        gdf,
        name = "Suitability Score",
        style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'blue',
            'weight': 0.5,
            'fillOpacity': 0.7,
        },
        ).add_to(m)
    
    return m

#STREAMLIT
st.set_page_config(layout="wide") #wide display on the app

#text
st.title("Data Center Siting Optimizer Prototype") 
st.markdown("### Recommends optimal locations to build data centers based on environmental risk factors.")

col1, col2 = st.columns([1,2])

with col1:
    st.markdown(f"#### Slider Options")
    WFH_value = st.slider("Wildfire Weight", 0.0, 1.0, 0.5)
    DR_value = st.slider("Drought Weight", 0.0, 1.0, 0.5)
    rank_value = st.slider("Number of Locations", 1, 20, 5)
    rankings, top_gdf = environmental_score(map_data, WFH_value, DR_value, rank_value)
    st.dataframe(rankings)


with col2:
    st.markdown(f"#### Top {rank_value} Recommended Counties:")
    st_folium(build_map(top_gdf), width = "stretch")


"""
#user input
st.text("Change the slides to select weights for the map")
WFH_value = st.slider("Select a weight for Wildfire Hazard Potential", 0.0, 1.0, 0.5)
DR_value = st.slider("Select a weight for Drought Risk", 0.0, 1.0, 0.5)
rank_value = st.slider("Select number of locations to recommend", 1, 20, 5)

#call the function
rankings, top_gdf = environmental_score(map_data, WFH_value, DR_value, rank_value)

st.header("Top " + str(rank_value) + " Recommended Counties:")

#display the table and map
st.dataframe(rankings)
st_folium(build_map(top_gdf), width=True)
"""