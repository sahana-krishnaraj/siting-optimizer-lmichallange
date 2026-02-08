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
    map_data["geometry"] = map_data["geometry"].apply(wkt.loads) 
    return gpd.GeoDataFrame(map_data, crs="EPSG:4326")

map_data = load_data("true_final.csv")    


def environmental_score(gdf, wildfire_user, drought_user, wind_user, oil_user, gas_user, rank):
    #make a copy
    gdf = gdf.copy()
    gdf = gdf[gdf["Pareto Efficient"] == True] #filter for pareto efficient locations

    #compute a proportion of the weight so it is scalable
    total_weight = wildfire_user + drought_user
    wildfire_weight = wildfire_user / total_weight
    drought_weight = drought_user / total_weight
    wind_weight = wind_user / total_weight
    oil_weight = oil_user / total_weight
    gas_weight = gas_user / total_weight

    #compute the risk score
    gdf["Suitability Score"] = (wildfire_weight * gdf["Wildfire Hazard Potential Score"] +
                                   drought_weight * gdf["Drought Risk Score"] 
                                    + wind_weight * gdf["Wind Plant Capacity"]
                                   - oil_weight * gdf["Oil Production Quantity"]
                                   - gas_weight * gdf["Gas Production Quantity"])
    
    #rank the counties from the highest to lowest score
    top_gdf = gdf.sort_values(by="Suitability Score", ascending=False).head(rank) #will be fed into the map
    rankings = gdf[["County","State Name","Suitability Score"]].sort_values(by="Suitability Score", ascending=False).head(rank) #used to display

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
    WI_value = st.slider("Wind Energy Weight", 0.0, 1.0, 0.5)
    OI_value = st.slider("Oil Production Weight", 0.0, 1.0, 0.5)
    GA_value = st.slider("Gas Production Weight", 0.0, 1.0, 0.5)
    rank_value = st.slider("Number of Locations", 1, 20, 5)
    rankings, top_gdf = environmental_score(map_data, WFH_value, DR_value, WI_value, OI_value, GA_value, rank_value)
    st.dataframe(rankings)


with col2:
    st.markdown(f"#### Top {rank_value} Recommended Counties:")
    st_folium(build_map(top_gdf), width = "stretch")