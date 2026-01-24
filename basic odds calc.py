import json
import numpy as np
from scipy.stats import norm
from bokeh.plotting import figure, show
import pandas as pd
template= '{"autoFuel": [],"transitionFuel":[], "shift1Fuel":[], "shift2Fuel":[],"shift3Fuel":[],"shift4Fuel":[],"endgameFuel":[]}'
data1 = json.loads(template)
data_home = json.loads(template)
team_numbers = []
match_ids=[]
#all_matches= []
with open("sample_data.json", "r") as f:
        data = json.load(f)
for teamnum, matches in data["root"].items():
    team_numbers.append(teamnum)
    for match_id, match_data in matches.items():
        match_ids.append(match_id)
        for fieldName, fieldValue in match_data.items():
            if isinstance(fieldValue, (int, float)):


                if teamnum =="3464" and fieldName in template:
                    data_home[fieldName].append(fieldValue)
                   
                if fieldName in data1:
                    data1[fieldName].append(fieldValue)
                   
        #all_matches.append(current_match)
#for i in range(len(team_numbers)):
    #dihta = {
        #"teams": pd.Series(team_numbers[i]),
        #"auto": pd.Series(data1["autoFuel"])
    #}
    #dihtas = pd.DataFrame(dihta)
    #print(dihtas)




home_list = list(data_home.values())
enemy_list = list(data1.values())
all_diffs=[]


for i in range(len(data1['autoFuel'])):
    enemy_total = (
        data1["autoFuel"][i] +
        data1["transitionFuel"][i] +
        data1["shift1Fuel"][i] +
        data1["shift2Fuel"][i] +
        data1["shift3Fuel"][i] +
        data1["shift4Fuel"][i] +
        data1["endgameFuel"][i]
    )
    all_diffs.append(np.sum(home_list)-enemy_total)
    mean_home = np.mean(all_diffs[i])
    std= np.std(all_diffs)
    #prints the stuff
    print(f"Mean: {mean_home}")
    print(f"Standard Deviation: {std}")
    #calculates the area under the curve to perdict probablility
    prob_3464 = norm.sf(0, loc=mean_home, scale=std)
    prob_3464_percentage = prob_3464*100
    print(f"Probability winning of match {match_ids[i]}: {prob_3464_percentage}+%")
   


#p = figure(title = "Data", x_axis_label="phases",y_axis_label="scores",x_range =list(data.keys()))
#p.scatter(list(data.keys()), list(data.values()),legend_label = "line", line_width = 2)
#show(p)


