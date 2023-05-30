# -*- coding: utf-8 -*-
"""
Created on Thu May 25 18:16:39 2023

@author: Claudio
"""

import json
import math
import pandas as pd


FRAME_LENGTH = 0.1
DIST_PRESSURE = 3 # max distance to player/ball to be considered a pressure
TIME_PRESSURE = 30 # cooldown time (frames) to count a new pressure event
TIME_PRESSURE_SUCCESS = 50 # time to recover the ball while pressing successfully
FACTOR_COORDINATES = {'home': 1, 'away': -1}
PRESSING_FACTOR = 0 # 0.125
PATH1 = 'opendata-master\\data\\'
PATH2 = PATH1+'matches\\'


# Matches id's
with open(PATH1+'\\matches.json') as f:
    matches = json.load(f)
matches_id = [x['id'] for x in matches]

df_final = pd.DataFrame()
for match_id in matches_id:
    # Game files
    with open(PATH2+str(match_id)+'\\match_data.json') as f:
        match_data = json.load(f)
    with open(PATH2+str(match_id)+'\\structured_data.json') as f:
        structured_data = json.load(f)    
    # Game Information
    home_team = match_data['home_team']['name']
    away_team = match_data['away_team']['name']
    home_team_id = match_data['home_team']['id']
    away_team_id = match_data['away_team']['id']
    location = {home_team_id: 'home', away_team_id: 'away'}
    ball_id = match_data['ball']['trackable_object']
    pitch_length = match_data['pitch_length']
    pitch_width = match_data['pitch_width']
    players_team = {}
    for player in match_data['players']:
        players_team[player['trackable_object']] = player['team_id']
    
    # Check pressure events
    pressure_events = []
    for data in structured_data:
        if data['period'] is not None and data['time'] is not None:
            # Check team/player in posession
            possesion_team_id =  None
            possession_player_id = None
            if data['possession']['trackable_object'] is not None:
                possession_player_id = data['possession']['trackable_object']
                possesion_team_id = players_team.get(possession_player_id)
                if possesion_team_id == home_team_id:
                    possession_team = away_team
                    pressure_team_id = home_team_id
                    pressure_team = home_team
                elif possesion_team_id == away_team_id:
                    possession_team = home_team
                    pressure_team_id = away_team_id
                    pressure_team = away_team
            elif data['possession']['group'] is not None:
                if 'home' in data['possession']['group']:
                    possesion_team_id = away_team_id
                    possession_team = away_team
                    pressure_team_id = home_team_id
                    pressure_team = home_team
                elif 'away' in data['possession']['group']:
                    possesion_team_id = home_team_id
                    possession_team = home_team
                    pressure_team_id = away_team_id
                    pressure_team = away_team
            # Save event if a team has possession
            if possesion_team_id:
                # Check for location of possession (player or ball) and opposition players
                f = FACTOR_COORDINATES[location[possesion_team_id]]
                player_possession, ball = None, None
                players_pressure, players_possession = [], []
                for obj in data['data']:
                    obj_id = obj.get('trackable_object')
                    if obj_id:
                        if players_team.get(obj_id) == pressure_team_id:
                            players_pressure.append(obj)
                        elif players_team.get(obj_id) == possesion_team_id:
                            players_possession.append(obj)
                        elif obj_id == possession_player_id:
                            player_possession = obj                    
                        elif obj_id == ball_id:
                            ball = obj
                p0 = player_possession if player_possession else ball
                # Check if there's a possesion that ocurrs in a high pressure zone
                if p0:
                    n_passing_options = 0 # count teammates in own half as passing options
                    n_options_pressed = 0 # count of n_passing_options being pressed
                    n_possible_pressing = 0 # count of out of possession players in high pressing zone
                    possession_pressed = 0 # is player in possession being pressed
                    list_players_pressing = [] # player who are doing high pressing
                    high_pressure_zone = 0
                    if p0['x']*f < -pitch_length*PRESSING_FACTOR:
                        high_pressure_zone = 1
                        for p2 in players_pressure:
                            dist0 = math.dist([p0['x'], p0['y']], [p2['x'], p2['y']])
                            if dist0 < DIST_PRESSURE:
                                possession_pressed = 1
                            if p2['x']*f < -pitch_length*PRESSING_FACTOR:
                                n_possible_pressing += 1
                        for p1 in players_possession:
                            if p1['x']*f < -pitch_length*PRESSING_FACTOR:  
                                if p1['trackable_object'] != possession_player_id:
                                    n_passing_options += 1
                                bool_player_pressed = False                            
                                for p2 in players_pressure:                        
                                    dist1 = math.dist([p1['x'], p1['y']], [p2['x'], p2['y']])
                                    if dist1 < DIST_PRESSURE:
                                        if not bool_player_pressed:
                                            bool_player_pressed = True
                                            n_options_pressed += 1
                                        if p2['trackable_object'] not in list_players_pressing:
                                            list_players_pressing.append(p2['trackable_object'])
                    pressure_events.append({
                        'match_id': match_id,
                        'high_pressure_zone': high_pressure_zone,
                        'possession_team_id': possesion_team_id,
                        'possession_team': possession_team,
                        'pressure_team_id': pressure_team_id,
                        'pressure_team': pressure_team,
                        'team_possession_location': location[possesion_team_id],
                        'possession_player_id': possession_player_id,
                        'n_passing_options': n_passing_options,
                        'n_options_pressed': n_options_pressed,
                        'n_players_pressing': len(list_players_pressing),
                        'n_possible_pressing': n_possible_pressing,
                        'possession_pressed': possession_pressed,
                        'period': data['period'],
                        'frame': data['frame'],
                        'time': data['time'],
                        'track_id': p0['track_id'],
                        'x': p0['x'],
                        'y': p0['y'],
                        })
                    
    # Dataframe with all possesion frames  
    df = pd.DataFrame(pressure_events)
    df['possession_id'] = 1
    for index, row in df.iterrows():
        try:
            row_next = df.loc[index+1]
            if row['possession_team_id'] != row_next['possession_team_id'] \
                or row['period'] != row_next['period'] \
                or row_next['frame'] - row['frame'] > TIME_PRESSURE \
                or ((not math.isnan(row['possession_player_id']) or not math.isnan(row_next['possession_player_id'])) and row['possession_player_id'] != row_next['possession_player_id']):
                df.loc[index+1, 'possession_id'] = df.loc[index, 'possession_id'] + 1
            else:
                df.loc[index+1, 'possession_id'] = df.loc[index, 'possession_id']
        except:
            if index+1 != len(df):
                print(index, 'error1')
                  
    # Dataframe summary, 1 row for every possession            
    df_summary = df.groupby(by='possession_id', dropna=False).agg({
        'frame': ['min', 'max'],
        'n_passing_options': 'max',
        'n_options_pressed': 'max', 
        'n_players_pressing': 'max',
        'n_possible_pressing': 'max',
        'possession_pressed': 'max'
        }).reset_index()
    df_summary.columns = ['possession_id', 'frame_start', 'frame_end', 'n_passing_options', 
                          'n_options_pressed', 'n_players_pressing', 'n_possible_pressing', 
                          'possession_pressed']
    df_summary['possesion_time'] = (df_summary['frame_end'] - df_summary['frame_start'])*FRAME_LENGTH
    df_summary['pressure_success'] = 0
    cols = ['match_id', 'frame', 'period', 'time', 'track_id', 'x', 'y', 
            'team_possession_location', 'possession_team_id', 'possession_team', 
            'pressure_team_id', 'pressure_team', 'possession_player_id', 
            'high_pressure_zone']
    df_summary = df_summary.merge(df[cols], left_on='frame_start', right_on='frame')
    df_summary = df_summary.drop('frame', axis=1)
    df_summary = df_summary.merge(df[['frame', 'high_pressure_zone']], left_on='frame_end', 
                                  right_on='frame', suffixes=('_start', '_end'))
    df_summary = df_summary.drop('frame', axis=1)

    for index, row in df_summary.iterrows():
        try:        
            if row['high_pressure_zone_start'] == 1:
                i = 1
                while i==1 or df_summary.loc[index+i]['frame_start'] - row['frame_start'] < 30:
                    if row['high_pressure_zone_end'] == 0:
                        break
                    row_next = df_summary.loc[index+i]
                    if (row.possession_team_id == row_next.possession_team_id and row_next['high_pressure_zone_start'] == 0):
                        break
                    if row.possession_team_id != row_next.possession_team_id:
                        df_summary.loc[index, 'pressure_success'] = 1
                        break
                    i += 1            
        except:
            if index+1 != len(df_summary):
                print(index, 'error2')   
    df_summary['x'] = df_summary['x']/(pitch_length/2)
    df_summary['y'] = df_summary['y']/(pitch_width/2)
    df_final = pd.concat([df_final, df_summary])

df_final.loc[df_final['team_possession_location']=='away', ['x', 'y']] = -df_final[df_final['team_possession_location']=='away'][['x', 'y']]
df_final.to_csv(PATH1+'possessions.csv', index=False)   
