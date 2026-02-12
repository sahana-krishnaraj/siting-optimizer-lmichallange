#load all the libraries
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import shape
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import MinMaxScaler
import branca

#add caching decorator so the app isn't slow
@st.cache_data
def load_data(url):
    map_data = pd.read_csv(url)
    map_data = map_data.drop(columns=["cn geometry"]) #drop unnecessary column
    map_data["geometry"] = map_data["geometry"].apply(wkt.loads)

    #takes the geometry column, if it is a dictionary, it converts it to a shapely geometry object using the shape function. If it's not a dictionary, it leaves it as is. 
    map_data["geometry"] = map_data["geometry"].apply(lambda x: shape(x) if isinstance(x, dict) else x)
    #return the function
    return gpd.GeoDataFrame(map_data, crs="EPSG:4326")

map_data = load_data("latest.csv") #load the dataset


def environmental_score(gdf, wildfire_user, drought_user, wind_user, oil_user, gas_user, rank):
    #make a copy
    gdf = gdf.copy()
    gdf = gdf[gdf["Pareto Efficient"] == True] #filter for pareto efficient locations


    ##higher weight for wildfire, drought, oil, gas is less suitable and higher for wind is more suitable
    total_weight = abs(wildfire_user) + abs(drought_user) + abs(wind_user) + abs(oil_user) + abs(gas_user)

    if total_weight == 0:
        st.warning("All weights are zero. Defaulting to equal importance for all factors.")
        wildfire_weight = drought_weight = wind_weight = oil_weight = gas_weight = 0.2
    else:
        wildfire_weight = wildfire_user / total_weight
        drought_weight = drought_user / total_weight
        wind_weight = wind_user / total_weight
        oil_weight = oil_user / total_weight
        gas_weight = gas_user / total_weight

    #compute the risk score
    gdf["Environmental Compatibility (%)"] = (
    wind_weight * gdf["Wind Plant Capacity (SCALE)"]
    - wildfire_weight * gdf["Wildfire Hazard Potential Score"]
    - drought_weight * gdf["Drought Risk Score"]
    + oil_weight * gdf["Oil Production Quantity (SCALE)"]
    + gas_weight * gdf["Gas Production Quantity (SCALE)"]
) 

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
def build_map(gdf, index_rankings):
    us_center = [37.0902, -95.7129] #center of the US to start the display
    html = gdf.to_html(index = False)
    #build the map
    m = folium.Map(location=us_center, tiles = "Cartodb dark_matter", zoom_start=4)
    #add the dataset
    folium.GeoJson(gdf).add_to(m)
    for index, row in gdf.iterrows():
        html = f"""
    <div style="
        width:280px;
        background:#000000;
        color:white;
        padding:10px;
        border-radius:2px;
        border-color:#000000;
        font-size:13px;
    ">
        <h3 style="margin:0 0 6px 0;">
            {row['County']}, {row['State Name']}
        </h3>
        <div style="
            font-size:14px;
            margin-bottom:8px;
            color:#7CFC98;
        ">
        <b>
            Ranking: {(index_rankings.loc[index_rankings['County'] == row['County']]).index[0]}
            </b>
        </div>
        <div style="
            font-size:14px;
            margin-bottom:8px;
            color:#7CFC98;
        ">
            Environmental Compatibility: {row['Environmental Compatibility (%)']:.2f}%
        </div>

        <table style="width:100%;">
            <tr>
                <td>Wildfire Risk</td>
                <td align="right">{row['Wildfire Hazard Potential Score']:.3f}</td>
            </tr>
            <tr>
                <td>Drought Risk</td>
                <td align="right">{row['Drought Risk Score']:.3f}</td>
            </tr>
        </table>
        <table style="width:100%;">
            <tr>
                <td>Wind Capacity</td>
                <td align="right">{row['Wind Plant Capacity']:.3f} MW</td>
            </tr>
            <tr>
                <td>Oil Production</td>
                <td align="right">{row['Oil Production Quantity']:.3f}</td>
            </tr>
            <tr>
                <td>Gas Production</td>
                <td align="right">{row['Gas Production Quantity']:.3f}</td>
            </tr>
    </div>
    """

        folium.Marker(
            location = [row.geometry.y, row.geometry.x],
            icon = folium.Icon(icon="leaf", prefix="fa", color="green", icon_color="white"),
            popup = html).add_to(m)
    return m

#STREAMLIT
st.set_page_config(layout="wide") #wide display on the app

#text
st.title("Data Center Siting Optimizer Prototype") 
st.markdown("### A recommendation tool to assist in building data centers based on environmental risk factors.")
st.divider()

col1, col2 = st.columns([1,2])

with col1:
    st.header("Slider Options")
    st.write("Set the sliders to reflect your preferences for each factor. The rankings and map will change based on what you prioritize.")

    #WILDFIRE
    st.subheader("Disaster Risk Weights")
    st.write("_Category reflects Wildfire Hazard Potential and Drought Risk in a given area. Move the slider to indicate how important avoiding these risks is to you: lower values = less concern, higher values = greater concern._")

    st.write("Wildfire Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Wildfire Risk</span>", unsafe_allow_html=True)
    WFH_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance wildfire risk", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Wildfire Risk</span>", unsafe_allow_html=True)

    #DROUGHT
    st.write("Drought Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Drought Risk</span>", unsafe_allow_html=True)
    DR_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance drought risk", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Drought Risk</span>", unsafe_allow_html=True)

    #WIND ENERGY
    st.subheader("Energy Source Weights")
    st.write("_Category reflects energy production in each area. Move the sliders to indicate your preference: higher wind = more wind energy, higher oil or gas = more of those resources._")
    st.write("Wind Energy Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Priority</span>", unsafe_allow_html=True)
    WI_value = subcol2.slider("", 0.0, 1.0, 0.5, help="Allows you to adjust the importance wind energy", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Priority</span>", unsafe_allow_html=True)

    #OIL PRODUCTION
    st.write("Oil Production Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Preference</span>", unsafe_allow_html=True)
    OI_value = subcol2.slider("", -1.0, 1.0, 0.0, help="Allows you to adjust the importance oil production", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Preference</span>", unsafe_allow_html=True)

    #GAS PRODUCTION
    st.write("Gas Production Weight")
    subcol1, subcol2, subcol3 = st.columns([0.25, 0.3, 0.25])
    subcol1.markdown("<span style='font-size: 12px;'>Low Preference</span>", unsafe_allow_html=True)
    GA_value = subcol2.slider("", -1.0, 1.0, 0.0, help="Allows you to adjust the importance gas production", label_visibility="collapsed")
    subcol3.markdown("<span style='font-size: 12px;'>High Preference</span>", unsafe_allow_html=True)

    #RANK
    st.subheader("Presentation Options")
    rank_value = st.slider("Number of Locations to Recommend", 1 , 10, 3)
    rankings, top_gdf = environmental_score(map_data, WFH_value, DR_value, WI_value, OI_value, GA_value, rank_value)

with col2:
    st.header(f"Top {rank_value} Recommended Counties:")
    st_folium(build_map(top_gdf, rankings), width = "stretch")
    st.subheader("Rankings Table")
    st.dataframe(rankings)


