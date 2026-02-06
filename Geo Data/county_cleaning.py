import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# read in data for wind and fuel
    # changed path but might not work, final csv is already in the folder.
wind = pd.read_csv('Datasets/Wind\ and\ Fuel/Wind.csv')
fuel = pd.read_csv("Datasets/Wind\ and\ Fuel/Oil_Gas_Fuel.csv")

# create geometries of each obs using lat and long columns
wind['geometry'] = wind.apply(
    lambda row: Point(row['Longitude'], row['Latitude']), 
    axis=1
)
fuel['geometry'] = fuel.apply(
    lambda row: Point(row['Longitude'], row['Latitude']), 
    axis=1
)

# convert to geo dataframes
wind_gdf = gpd.GeoDataFrame(wind, geometry='geometry', crs='EPSG:4326') # crs tells python how to relate the coordinates to earth. epsg:4326 is the standard system
fuel_gdf = gpd.GeoDataFrame(fuel, geometry='geometry', crs='EPSG:4326')

# read in counties shapefile
counties = gpd.read_file('counties_shapefile') # entire folder
counties = counties.to_crs('EPSG:4326') # make sure the same crs is used

# join the three datasets
    # left join from counties to data - we want all counties as obs, and not all counties are in the data files
counties_wind = gpd.sjoin(counties, wind_gdf, how='left', predicate='within', rsuffix='wind') # within: the entire coordinate should be completely in the county boundary (no part of it can be outside the border line)
final = gpd.sjoin(counties_wind, fuel_gdf, how='left', predicate='within', rsuffix='fuel') # suffix so dup column names arent created

# final.to_csv('windfuel_counties.csv', index=False) # worked!


# important new variables:
    # statefp: state's fips code
    # countyfp: county's fips code
    # GEOID: full 5-digit FIPS code
    # countyns: county's GNIS - unique permanent identifier
    # AFFGEOID: American FactFinder GEOID - common in census data
    # lsad: legal/statistical area description