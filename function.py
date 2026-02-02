import pandas as pd
from sklearn.preprocessing import MinMaxScaler

#load the dataset we will use
combined = pd.read_csv("/Users/sahana_krishnaraj/Documents/Spring 2026/LMI/final_combined_data.csv")

#subset to get relevant columns
'''
Wildfire Hazard Potential (WHP)
H + VH Pct = Percent of area in the geographic unit mapped as high or very high WHP

Drought Levels (Percentiles)
Nnone = No Drought
DO = Drought Level 0 (Abnormally Dry)
D1 = Drought Level 1 (Moderate Drought)
D2 = Drought Level 2 (Severe Drought)
D3 = Drought Level 3 (Extreme Drought)
'''
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
    if high: #sort the counties in descending order based on the number of counties requested
        ranked_counties = subset[["County","State", "Suitability Score"]].sort_values(by="Suitability Score", ascending=False).head(rank)
    else: #sort the counties in ascending order based on the number of counties requested
        ranked_counties = subset[["County","State", "Suitability Score"]].sort_values(by="Suitability Score", ascending=True).head(rank)

    return ranked_counties

