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
END_DATE = (datetime.today() + timedelta(days=5)).strftime('%Y-%m-%d')

def get_headers():
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

def save_properties_to_csv():
    headers = get_headers()
    base_url = "https://public.api.hospitable.com/v2/properties"
    properties_list = []
    page = 1
    per_page = 10
    total_pages = 1
    while page <= total_pages:
        url = f"{base_url}?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            properties = data.get('data', [])
            total_pages = data.get('meta', {}).get('last_page', 1)
            # Append all property details to the list
            properties_list.extend(properties)
            page += 1
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            break
    # Convert to DataFrame
    if properties_list:
        df = pd.DataFrame(properties_list)
        df = df.drop(columns=['summary', 'description'])
        # Ensure the folder exists
        output_folder = "files/table/"
        os.makedirs(output_folder, exist_ok=True)
        # Save as CSV
        file_path = os.path.join(output_folder, "hospitable_properties.csv")
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"File saved at: {file_path}")
    else:
        print("No properties found.")

#----------------------------------------------------------
def get_reservations(property_ids, START_DATE, END_DATE):
    headers = get_headers()
    reservations = []
    for property_id in property_ids:
        page = 1
        total_pages = 1
        while page <= total_pages:
            url = f"https://public.api.hospitable.com/v2/reservations?page={page}&per_page=10&properties[]={property_id}&start_date={START_DATE}&end_date={END_DATE}&date_query=checkout"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
            
                if 'data' in data:
                    reservations.extend(data['data'])  # Collect all reservation data
                    
                    total_pages = data.get('meta', {}).get('last_page', 1)  # Update total pages
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


def save_reservations_to_csv(property_ids, START_DATE, END_DATE):
    reservations_data = get_reservations(property_ids, START_DATE, END_DATE)
    if reservations_data:
        df = pd.DataFrame(reservations_data)  # Convert to DataFrame
        # Ensure the folder exists
        output_folder = "files/table/"
        os.makedirs(output_folder, exist_ok=True)
        # Save as CSV
        file_path = os.path.join(output_folder, "hospitable_reservations.csv")
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"CSV saved with all reservation fields at: {file_path}")
    else:
        print("No reservations found. CSV was not created.")
#----------------------------------------------------------
# Run function

def main():
    #save_properties_to_csv()
    property_ids = get_properties()
    save_reservations_to_csv(property_ids, START_DATE, END_DATE)

    return "This works! :)"


main()