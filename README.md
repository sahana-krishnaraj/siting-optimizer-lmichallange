# Environmental Risk Siting Optimzer
Streamlit App: https://sahana-siting.streamlit.app 

## Documentation
-  **Pareto Efficiency**: looking at the non-dominated counties and providing the user options to weigh certain amongst selected counties. 
- For this project, the goal is to minimize Wildfire Risk and Drought risk so we would look for candidates that match this criteria. 

## Pseudocode for Pareto
1. First, take the first county, obtain its drought and WHP scores.
2. Take the second county in the dataframe, and compare the drought to the first county. If it is smaller than that, check the WHP. If WHP is smaller, then second county be pareto efficient.  
3. Iterate through by comparing the first county with the others and clasiffying them as pareto efficient. 


