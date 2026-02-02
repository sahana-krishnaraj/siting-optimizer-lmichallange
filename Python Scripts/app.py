import streamlit as st
import pandas as pd
import function as fn 


st.title("Data Center Siting Optimizer Prototype") 
st.text("Recommends optimal locations to build data centers based on environmental risk factors.")
WFH_value = st.slider("Select a weight for Wildfire Hazard Potential", 0.0, 1.0, 0.5)
DR_value = st.slider("Select a weight for Drought Risk", 0.0, 1.0, 0.5)
rank_value = st.slider("Select number of locations to recommend", 1, 20, 5)
st.header("Top " + str(rank_value) + " Recommended Counties:")
st.write(fn.environmental_score(WFH_value, DR_value, rank_value, high=True))