# -*- coding: utf-8 -*-
"""
Created on Mon May 29 11:45:09 2023

@author: Claudio
"""
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

PATH1 = 'opendata-master\\data\\'
PITCH_LENGTH = 105
PITCH_WIDTH = 68

df0 = pd.read_csv(PATH1+'possessions.csv')
df = df0[(df0.n_players_pressing>=2)&(df0.high_pressure_zone_start==1)]
df.x = df.x*PITCH_LENGTH/2
df.y = df.y*PITCH_WIDTH/2

# Average high pressure succes
df2 = df.groupby(by='pressure_success').size()
print(df2.loc[1]/df2.sum())


# Heatmap high pressure success
x_buckets = 10
y_buckets = 5
x_length = PITCH_LENGTH/2/x_buckets
y_length = PITCH_WIDTH/2/y_buckets

pressure = np.empty([x_buckets,y_buckets*2])
pressure[:] = np.nan
pressure_yx, pressure_yy = [], []

x_limit = [x*PITCH_LENGTH/x_buckets/2 for x in range(x_buckets)]
y_limit = [y*PITCH_WIDTH/y_buckets/2 for y in range(-y_buckets, y_buckets)]

fig, ax = plt.subplots()
x = 0
for i in range(x_buckets):
    for j in range(y_buckets*2):
        x_min, y_min = x_limit[i], y_limit[j]
        x_max, y_max = x_min+x_length, y_min+y_length
        aux = df[(-df.x>x_min)&(-df.x<=x_max)&(df.y>y_min)&(df.y<=y_max)]       
        if len(aux)>0:
            pressure[j][i] = len(aux[aux.pressure_success==1])/len(aux)
               
plt.imshow(pressure, vmin=0, vmax=1,aspect='auto')
circle1 = plt.Circle((-0.5, 4.5), 1.5, color='r', fill=False)
plt.plot([7, 9.5], [2.0, 2.0], c='r')
plt.plot([8.5, 9.5], [3.25, 3.25], c='r')
plt.plot([7, 9.5], [7, 7], c='r')
plt.plot([8.5, 9.5], [5.75, 5.75], c='r')
plt.plot([7, 7], [2, 7], c='r')
plt.plot([8.5, 8.5], [3.25, 5.75], c='r')
plt.scatter([-0.5], [4.5], c='r')
plt.scatter([7.8], [4.5], c='r')
ax.add_patch(circle1)
ax.set_xlim(-0.5, 9.5)
plt.tick_params(which='both', bottom=False, labelbottom=False, left=False, labelleft=False)
plt.title('Heatmap High Pressure Success')
plt.colorbar()
plt.savefig(PATH1+'heat-map-pressure-success.png', dpi=1000, bbox_inches='tight')
plt.show()

# High pressure success versus ball depth
pressure_xx, pressure_xy = [], []
for i in range(x_buckets):
    x_min = x_limit[i]
    x_max = x_min+x_length
    aux = df[(-df.x>x_min)&(-df.x<=x_max)]
    if len(aux)>0:
        pressure_xx.append((x_min+x_max)/2)
        pressure_xy.append(len(aux[aux.pressure_success==1])/len(aux))
fig = plt.figure()
ax = plt.subplot(111)
plt.plot(pressure_xx, pressure_xy)
ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])
plt.title('High Pressure Succes vs Ball Depth')
plt.savefig(PATH1+'depth-vs-pressure-success.png', dpi=1000, bbox_inches='tight')
plt.show()

            
# High pressure success versus ball width
pressure_yx, pressure_yy = [], []
for i in range(y_buckets*2):
    y_min = y_limit[i]
    y_max = y_min+y_length
    aux = df[(df.y>y_min)&(df.y<=y_max)]
    if len(aux)>0:
        pressure_yx.append((y_min+y_max)/2)
        pressure_yy.append(len(aux[aux.pressure_success==1])/len(aux))
fig = plt.figure()
ax = plt.subplot(111)
plt.plot(pressure_yx, pressure_yy)
plt.title('High Pressure Succes vs Ball Width')
ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])
plt.savefig(PATH1+'width-vs-pressure-success.png', dpi=1000, bbox_inches='tight')
plt.show()


# High pressure success uplift - Ball Pressed vs Ball Not PRessed
df3 = df.groupby(by='possession_pressed').agg({'pressure_success': 'mean'})
uplift_possession_pressed = df3.loc[1] - df3.loc[0]
print('uplift_possession_pressed: ', uplift_possession_pressed['pressure_success'])


# High pressure succes by metric
df.loc[:,'percent_passing_options_pressed'] = df['n_options_pressed']/df['n_passing_options']
metrics = [
    'n_passing_options', 'n_options_pressed', 'n_players_pressing', 
    'n_possible_pressing', 'percent_passing_options_pressed'
    ]
TITLES = {
    'n_passing_options': 'Number of Passing Options',
    'n_options_pressed': 'Number of Passing Options Pressed',
    'n_players_pressing': 'Number of Players High Pressing',
    'n_possible_pressing': 'Number of Players in Opposition Half',
    'percent_passing_options_pressed': 'Percentage of Passing Options Pressed'
    }

for metric in metrics:
    fig = plt.figure()
    ax = plt.subplot(111)
    metric_values = df[metric].unique()
    metric_values.sort()
    x, y = [], []
    for i in metric_values:
        aux = df[df[metric]==i]
        if len(aux)>0:
            x.append(i)
            y.append(len(aux[aux.pressure_success==1])/len(aux))
    plt.plot(x, y)
    plt.title(TITLES[metric])
    plt.ylabel('Percentage Pressure Success')
    ax.set_ylim(0, 1)
    ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])
    plt.savefig(PATH1+metric+'.png', dpi=1000, bbox_inches='tight')
    plt.show()
    