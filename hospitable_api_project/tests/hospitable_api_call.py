# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 18:52:20 2023

@author: Eleazar Gonzalez
"""
import os
import requests
import json
import pandas as pd
from datetime import datetime, date, timedelta
#from src.utils.config import load_config

#hospitable_token = load_config()['hospitable_secret']

START_DATE = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
END_DATE = (datetime.today() + timedelta(days=15)).strftime('%Y-%m-%d')

def get_headers():
    # token = os.environ.get('HOSPITABLE_API')
    # if not token:
    #     raise ValueError("HOSPITABLE_API environment variable not found")
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        # "authorization": f"Bearer {hospitable_token}"
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5YTYyNGRmMC0xMmYxLTQ0OGUtYjg4NC00MzY3ODBhNWQzY2QiLCJqdGkiOiI4ODhhODg1ZWI0ZWRjOTNhYWQyYzEyNTM2ZDg2YzU5MmFhNzc1ODEyMDQxOTgzNzljZjY1YjhhMGNkNTk1NmEzNTVmNDRiNjc4MmU0NjA5MiIsImlhdCI6MTczOTczNjE0MC44NDA4NjksIm5iZiI6MTczOTczNjE0MC44NDA4NzQsImV4cCI6MTc3MTI3MjE0MC44MzY2NzIsInN1YiI6IjI3NDYyIiwic2NvcGVzIjpbInBhdDpyZWFkIiwicGF0OndyaXRlIl19.bBUvcpwhIy08zTb_WEy2Xf1nXgFIbZBjbt9lV8BzNYzVyC3xvVMObgkCNvVdFAKkhklPoL5Ur5CtUV1ebNX0rOaC7BTG4Z_0DChE4Jekmg6CA_dQXcqNIPPbBJlpt_YdJZnvYFL6RtfW0A7IBZ2jpTmYxL3HV7nl5zIxkh0Wp90sMLqIBA5PJHjAtS3vb1slHV0fma-gabEJ0Qf00qb8vsP69EvNSqUXqggA6MymYEsshKH5sN3N67oPSnyIIc8HOO50VhckBiO_fOcnG2sV4gPAaPTG4cGAHNdRF9p3JtD3shT1YsUeGXEuNmrnLdPlWlXXMGIqXXZMKAiUGFIgdhHFzcPB_EEM_PpbAdQUpetTMgtjEwoIm0Bg1GA7V-UWlFeeWDWoEM2ift1ttOHr6LwI3r8BbEqby0Rn7mbmPO1Pl5N9IJpc6c12NoZUDjPlf7GozNkQxctBsM5LgfXIIh-QvZOE0Y3HqQqHzK9yAoO_TJN_jGeB2C6iYh7v1LlmgSxG7quRAVK8Wx1FHh1AaqZ-Ewd5QBXEKulEcOS7ZSjLGO6RyL0wICLh_d6vmQS9KieiW_1_-N6-l3kXQL3huSKbS2CJudVf8dsMzTJcUvMSR_aPq8W8poJ_IlrCWERetsBsO8Yb4VigZFMmnZYtaJhplX0AtruEglejb03QXP8"
    }
    return headers

def get_properties():
    headers=get_headers()
    base_url = "https://public.api.hospitable.com/v2/properties"
    property_ids = []
    page = 1
    per_page = 10
    total_pages = 1
    while page <= total_pages:
        url = f"{base_url}?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        data = response.json()
        property_ids.extend([property['id'] for property in data['data']])
        total_pages = data['meta']['last_page']
        page += 1
    return property_ids

def get_reservations(property_ids, START_DATE, END_DATE):
    headers=get_headers()
    start_date = START_DATE
    end_date = END_DATE
    reservations = []
    for property_id in property_ids:
        page = 1
        total_pages = 1
        while page <= total_pages:
            url = f"https://public.api.hospitable.com/v2/reservations?page={page}&per_page=10&properties[]={property_id}&start_date={start_date}&end_date={end_date}&date_query=checkout"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data: # Check if 'data' key exists in the response
                    for reservation in data['data']:
                        reservation_id = reservation['id']
                        reservation_code = reservation.get('code', 'No code available')
                        reservations.append({'id': reservation_id, 'code': reservation_code})   
                    total_pages = data['meta']['last_page'] # Update the total_pages from the meta information
                    page += 1
                else:
                    print(f"No data found for property ID {property_id}")
                    break
            elif response.status_code == 404:
                break
            else:
                print(f"Failed to retrieve reservations for property ID {property_id}: {response.status_code} - {response.reason}")
                break
    return reservations

def get_conversations_json(reservations):
    headers=get_headers()
    output_file = 'conversations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        for reservation in reservations:
            reservation_id = reservation['id']
            reservation_code = reservation['code']
            url = f"https://public.api.hospitable.com/v2/reservations/{reservation_id}/messages"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                messages = data['data']
                for message in messages:
                    # Append reservation_id and code to the message
                    message['reservation_id'] = reservation_id
                    message['reservation_code'] = reservation_code
                    f.write(json.dumps(message) + '\n')
            else:
                raise Exception(f"Error: {response.status_code}")
    
    print(f"Saved newline-delimited JSON data to {output_file}")
    return output_file

###----------------------------------------------------------------------------------------------------------------------------###
def get_conversations(reservations):
    headers = get_headers()
    conversations = []
    for reservation in reservations:
        reservation_id = reservation['id']
        reservation_code = reservation['code']
        url = f"https://public.api.hospitable.com/v2/reservations/{reservation_id}/messages"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            messages = data['data']
            for message in messages:
                conversations.append({
                    "reservation_id": reservation_id,
                    "reservation_code": reservation_code,
                    "message_id": message.get("id", ""),
                    "sender": message.get("sender", ""),
                    "content": message.get("content", ""),
                    "created_at": message.get("created_at", "")
                })
        else:
            print(f"Error fetching messages for reservation {reservation_id}: {response.status_code}")
    return conversations
###----------------------------------------------------------------------------------------------------------------------------###
def save_properties_as_csv(property_ids, folder="files", filename="properties.csv"):
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, filename)
    df = pd.DataFrame({"Property ID": property_ids})
    df.to_csv(file_path, index=False)
    print(f"CSV file saved at: {file_path}")

def save_reservations_as_csv(reservations, folder="files", filename="reservations.csv"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, filename)
    if reservations:
        df = pd.DataFrame(reservations)
        df.to_csv(file_path, index=False)
        print(f"CSV file saved at: {file_path}")
    else:
        print("No reservations to save.")

def save_conversations_as_csv(conversations, folder="files", filename="conversations.csv"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, filename)
    if conversations:
        df = pd.DataFrame(conversations)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"CSV file saved at: {file_path}")
    else:
        print("No conversations to save.")

# Example Usage
property_ids = get_properties()
reservations = get_reservations(property_ids, START_DATE, END_DATE)
conversations = get_conversations(reservations)
save_conversations_as_csv(conversations)
