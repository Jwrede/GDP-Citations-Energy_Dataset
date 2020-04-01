import pandas as pd
import numpy as np
import re

#data cleaning for the Energy Indicator dataset
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
energy = pd.read_excel(r"Energy Indicators.xls")
energy = energy[17:244]
energy = energy.iloc[:, 2:6]
energy.columns = ['Country', 'Energy Supply', 'Energy Supply per Capita', '% Renewable']
energy.replace(to_replace = "...", value = np.NaN, inplace = True)
energy.Country = energy.Country.apply(lambda x: re.sub(r'\d', '', x))
energy.Country = energy.Country.apply(lambda x: re.sub(r'\([^()]+\)', '', x))
energy.replace({"Republic of Korea": "South Korea",
            "United States of America": "United States",
            "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
            "China, Hong Kong Special Administrative Region": "Hong Kong",
            "Iran " : "Iran"}, inplace = True)
energy["Energy Supply"] *= 1000000
energy.set_index("Country")

#data cleaning for the world bank dataset
gdp = pd.read_csv(r"world_bank.csv")
gdp.replace({"Korea, Rep.": "South Korea", 
             "Iran, Islamic Rep.": "Iran",
             "Hong Kong SAR, China": "Hong Kong"}, inplace = True)
gdp.columns = gdp.iloc[3]
gdp = gdp[4:]
gdp.set_index("Country Name", inplace = True)
gdp = gdp.iloc[:, 49:59]
gdp.columns = gdp.columns.astype(int)

ScimEn = pd.read_excel(r"scimagojr.xlsx")

#merging of all 3 datasets
temp = energy.merge(gdp, how = "inner", left_on = "Country", right_on = "Country Name")
whole = ScimEn.merge(temp, how = "inner", left_on = "Country", right_on = "Country")
whole.reset_index()
whole.set_index("Country", inplace = True)

#sets a new Column for the Continent
ContinentDict = {'China':'Asia', 
                  'United States':'North America', 
                  'Japan':'Asia', 
                  'United Kingdom':'Europe', 
                  'Russian Federation':'Europe', 
                  'Canada':'North America', 
                  'Germany':'Europe', 
                  'India':'Asia',
                  'France':'Europe', 
                  'South Korea':'Asia', 
                  'Italy':'Europe', 
                  'Spain':'Europe', 
                  'Iran':'Asia',
                  'Australia':'Australia', 
                  'Brazil':'South America'}
whole["Continent"] = pd.Series(ContinentDict)


#top 15 countries ranked by the ScimEn dataset
whole = whole[:15]

def avgGdp():
    return whole.iloc[:,10:20].mean(axis = 1).sort_values(ascending = False)
    
def changeSixth():
    #returns the total change of the 6th highest ranked country
    whole["avg GDP"] = avgGdp()
    whole.sort_values("avg GDP", ascending = False, inplace = True)
    result = whole.iloc[5, 20] - whole.iloc[5, 10]
    whole.sort_values("Rank", inplace = True)
    return result


def energyMean():
    return whole.iloc[:, 8].mean()

def maxPercentRenewable():
    #returns a tuple with the name of the country with the highest
    #percentage of renewable energy and its percentage
    return (whole[whole.iloc[:, 9] == whole.iloc[:, 9].max()].index.format()[0], whole.iloc[:, 9].max())
    
def citationRatio():
    #creates a column for the ratio of Self-citations to Citations
    #and returns a tuple with the name and the ratio of the country
    #with the highest value
    whole["Citation Ratio"] = whole["Self-citations"] / whole["Citations"]
    return (whole[whole["Citation Ratio"] == whole["Citation Ratio"].max()].index.format()[0], whole["Citation Ratio"].max())

def estimatedPop():
    #creates a column for the estimated population per country
    #based the Energy Supply divided by the Energy Supply per Capita
    #and returns the name of the country with the highest estimated population
    whole["Estimated Population"] = whole["Energy Supply"] / whole["Energy Supply per Capita"]
    return whole[whole["Estimated Population"] == whole["Estimated Population"].max()].index.format()[0]
    
estimatedPop()

def citableDocumentPP():
    #creates a column that estimates the number of citable documents per person
    #and returns the correlation between the number of citable documents per capita and the energy supply per capita
    estimatedPop()
    whole["Citable Documents per Capita"] = (whole["Citable documents"] / whole["Estimated Population"]).round(decimals = 5)
    return whole[["Citable Documents per Capita", "Energy Supply per Capita"]].corr().iloc[1,0]

def isGreenClassifier():
    #creates a column that classifies if a country has a higher percentage
    #of renewable energy than the median of the top 15 countries and returns this column
    whole["High green Energy ratio"] = np.where(whole["% Renewable"] > whole["% Renewable"].median(), 1, 0)
    return whole["High green Energy ratio"]
    
def continentGroup():
    #returns a dataframe which groups the countries into their underlying continents. The continents are used as indeces and
    #summarized in its columns are the amount of countries in it and the sum, mean and standard devitation of the
    #countries estimated populations.
    return whole.groupby("Continent")["Estimated Population"].agg(["size", "sum", "mean", "std"])

def binCutting():
    #groups whole by Continent and by 5 bins of the column "% Renewable" and returns a Dataframe with the Continents and these bins
    #as a Multiindex with the column "size" that specifies how many countries are in these intervals
    return whole.groupby(["Continent", pd.cut(whole["% Renewable"],5)]).size().where(whole.groupby(["Continent", pd.cut(whole["% Renewable"],5)]).size() != 0).dropna()
    
def popToString():
    #seperates the "Estimated Population" values in thousands and then converts it into a string
    whole["Estimated Population"] = whole["Estimated Population"].apply(lambda x : "{:,}".format(x))
    whole["Estimated Population"] = whole["Estimated Population"].astype(str)
    
