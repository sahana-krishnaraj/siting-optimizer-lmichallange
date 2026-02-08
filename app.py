#load all the libraries
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import MinMaxScaler

#add caching decorator so the app isn't slow
@st.cache_data
def load_data(url):
    map_data = pd.read_csv(url)
    map_data["geometry"] = map_data["geometry"].apply(wkt.loads) 
    return gpd.GeoDataFrame(map_data, crs="EPSG:4326")

map_data = load_data("dataset.csv") #load the dataset


def environmental_score(gdf, wildfire_user, drought_user, wind_user, oil_user, gas_user, rank):
    #make a copy
    gdf = gdf.copy()
    gdf = gdf[gdf["Pareto Efficient"] == True] #filter for pareto efficient locations

    ##higher weight for wildfire, drought, oil, gas is less suitable and higher for wind is more suitable
    total_weight = wildfire_user + drought_user + wind_user + oil_user + gas_user
    wildfire_weight = wildfire_user / total_weight
    drought_weight = drought_user / total_weight
    wind_weight = wind_user / total_weight
    oil_weight = oil_user / total_weight
    gas_weight = gas_user / total_weight

    #compute the risk score
    gdf["Environmental Compatibility (%)"] = ((wind_weight * gdf["Wind Plant Capacity"]) + (wildfire_weight * gdf["Wildfire Hazard Potential Score"] + drought_weight * gdf["Drought Risk Score"]) + oil_weight * gdf["Oil Production Quantity"] + gas_weight * gdf["Gas Production Quantity"]) 

    scaler = MinMaxScaler(feature_range=(0, 100))
    gdf["Environmental Compatibility (%)"] = scaler.fit_transform(gdf[["Environmental Compatibility (%)"]])

    #rank the counties from the highest to lowest score
    top_gdf = gdf.sort_values(by="Environmental Compatibility (%)", ascending=False).head(rank) #will be fed into the map
    rankings = gdf[["County","State Name","Environmental Compatibility (%)"]].sort_values(by="Environmental Compatibility (%)", ascending=False).head(rank) #used to display

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

    #WILDFIRE
    st.write("Wildfire Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Priority</span>", unsafe_allow_html=True)
    WFH_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance wildfire risk", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Priority</span>", unsafe_allow_html=True)

    #DROUGHT
    st.write("Drought Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Priority</span>", unsafe_allow_html=True)
    DR_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance drought risk", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Priority</span>", unsafe_allow_html=True)

    #WIND ENERGY
    st.write("Wind Energy Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Priority</span>", unsafe_allow_html=True)
    WI_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance wind energy", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Priority</span>", unsafe_allow_html=True)

    #OIL PRODUCTION
    st.write("Oil Production Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Sustainability</span>", unsafe_allow_html=True)
    OI_value = subcol2.slider("", -1.0, 1.0, 0.0, help="Allows you to adjust the importance oil production", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Sustainability</span>", unsafe_allow_html=True)

    #GAS PRODUCTION
    st.write("Gas Production Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Sustainability</span>", unsafe_allow_html=True)
    GA_value = subcol2.slider("", -1.0, 1.0, 0.0, help="Allows you to adjust the importance gas production", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Sustainability</span>", unsafe_allow_html=True)

    rank_value = st.slider("Number of Locations", 1, 38, 3)
    rankings, top_gdf = environmental_score(map_data, WFH_value, DR_value, WI_value, OI_value, GA_value, rank_value)
    st.dataframe(rankings)


with col2:
    st.markdown(f"#### Top {rank_value} Recommended Counties:")
    st_folium(build_map(top_gdf), width = "stretch")

