import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

#load the dataset we will use
map_data = pd.read_csv("condensed.csv")

###SHOULD I NORMALIZE THE SCORES BEFORE COMBINING?###
#if you need to modify the weights for the drought risk score, you can do so here. already made a column, but this will just replace!
scaler = MinMaxScaler()
map_data["Drought Risk Score"] = 0.0*map_data["None"] + 0.1*map_data["D0"] + 0.3*map_data["D1"] + 0.4*map_data["D2"] + 0.6*map_data["D3"] + 0.9*map_data["D4"]

#create geodataframe
map_data["geometry"] = map_data["geometry"].apply(wkt.loads)
map_gdf = gpd.GeoDataFrame(map_data, crs="EPSG:4326") #crs is the map grid system 

def environmental_score(wildfire_user, drought_user, rank, high=True):
    #compute a proportion of the weight so it is scalable
    total_weight = wildfire_user + drought_user
    wildfire_weight = wildfire_user / total_weight
    drought_weight = drought_user / total_weight

    #compute the risk score
    map_gdf["Suitability Score"] = (wildfire_weight * map_gdf["Wildfire Hazard Potential"] +
                                   drought_weight * map_gdf["Drought Risk Score"])
    
    #standardize the Suitability Score
    map_gdf["Suitability Score"] = scaler.fit_transform(map_gdf[["Suitability Score"]])
    
    #rank the counties from the highest to lowest score
    mapped_counties = map_gdf.sort_values(by="Suitability Score", ascending=False).head(rank)
    ranked_counties = map_gdf[["County","State","Suitability Score"]].sort_values(by="Suitability Score", ascending=False).head(rank)

    #create a folium map
    us_center = [37.0902, -95.7129] #center of the US to start the display

    m = folium.Map(location=us_center, tiles = "Cartodb Positron", zoom_start=4)
    folium.GeoJson(
        mapped_counties,
        name = "Suitability Score",
        style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'blue',
            'weight': 0.5,
            'fillOpacity': 0.7,
        }).add_to(m)
    return ranked_counties, m

st.set_page_config(layout="wide")
st.title("Data Center Siting Optimizer Prototype") 
st.text("Recommends optimal locations to build data centers based on environmental risk factors.")
WFH_value = st.slider("Select a weight for Wildfire Hazard Potential", 0.0, 1.0, 0.5)
DR_value = st.slider("Select a weight for Drought Risk", 0.0, 1.0, 0.5)
rank_value = st.slider("Select number of locations to recommend", 1, 20, 5)
st.header("Top " + str(rank_value) + " Recommended Counties:")
rankings, display = environmental_score(WFH_value, DR_value, rank_value, high=True)
st_folium(display, use_container_width=True)