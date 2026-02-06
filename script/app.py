import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os

#load the dataset we will use
combined = pd.read_csv("/Users/sahana_krishnaraj/Github/siting-optimizer-lmichallange/Datasets/Cleaned Data/final_combined_data.csv")

#subset to get relevant columns
subset = combined[["County","State","H + VH Pct","None","D0","D1","D2","D3","D4"]]
subset = subset.copy()

#rename the columns and create a drought risk score
subset = subset.rename(columns={"H + VH Pct": "Wildfire Hazard Potential"})

###SHOULD I NORMALIZE THE SCORES BEFORE COMBINING?###
scaler = MinMaxScaler()
subset["Drought Risk Score"] = 0.0*subset["None"] + 0.1*subset["D0"] + 0.3*subset["D1"] + 0.4*subset["D2"] + 0.6*subset["D3"] + 0.9*subset["D4"]

def environmental_score(wildfire_user, drought_user, rank, high=True):
    #compute a proportion of the weight so it is scalable
    total_weight = wildfire_user + drought_user
    wildfire_weight = wildfire_user / total_weight
    drought_weight = drought_user / total_weight

    #compute the risk score
    subset["Suitability Score"] = (wildfire_weight * subset["Wildfire Hazard Potential"] +
                                   drought_weight * subset["Drought Risk Score"])
    
    #standardize the Suitability Score
    subset["Suitability Score"] = scaler.fit_transform(subset[["Suitability Score"]])
    
    #rank the counties
    ranked_counties = subset[["County","State", "Suitability Score"]].sort_values(by="Suitability Score", ascending=False).head(rank)
    return ranked_counties


st.title("Data Center Siting Optimizer Prototype") 
st.text("Recommends optimal locations to build data centers based on environmental risk factors.")
WFH_value = st.slider("Select a weight for Wildfire Hazard Potential", 0.0, 1.0, 0.5)
DR_value = st.slider("Select a weight for Drought Risk", 0.0, 1.0, 0.5)
rank_value = st.slider("Select number of locations to recommend", 1, 20, 5)
st.header("Top " + str(rank_value) + " Recommended Counties:")
st.write(environmental_score(WFH_value, DR_value, rank_value, high=True))