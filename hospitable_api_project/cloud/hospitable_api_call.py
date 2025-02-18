# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 18:52:20 2023

@author: Eleazar Gonzalez
"""
import requests
import json
import io
import pandas as pd
from google.cloud import bigquery
from google.cloud import storage
import os 
from datetime import datetime, date, timedelta



bucket_name = 'hostair_hostable'
url = "https://auth.hospitable.com/oauth/token"
headers = {
    "Content-Type": "application/json"
}
data = {
    "client_id": "",
    "client_secret": "",
    "audience": "api.hospitable.com",
    "grant_type": "client_credentials"
}

START_DATE = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')


#### AUTHENTICATE ###
def authenticate(url, headers, data):
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    token_value = response_json["access_token"]
    return token_value



#token = authenticate(url,headers,data) 
#print(token)
#### GET LISTINGS ###

def get_listings(token):
    url = f"https://api.hospitable.com/listings"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    result = response.json()
    pagination = result['_pagination']
    response_json = result['data']

    while pagination['current_page'] < pagination['total_pages']:
        pagination['current_page'] += 1
        response = requests.get(url, headers=headers, params={'page': pagination['current_page']})
        response_json += response.json()['data']
        response_df = pd.DataFrame(response_json)

    return response_df



#### GET PROPERTIES ###
def get_properties(token):
    url = f"https://api.hospitable.com/properties"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    result = response.json()
    pagination = result['_pagination']
    response_json = result['data']

    while pagination['current_page'] < pagination['total_pages']:
        pagination['current_page'] += 1
        response = requests.get(url, headers=headers, params={'page': pagination['current_page']})
        response_json += response.json()['data']
        response_df = pd.DataFrame(response_json)

    return response_df

def get_list_properties(token):
    url = f"https://api.hospitable.com/properties"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    result = response.json()
    pagination = result['_pagination']
    response_json = result['data']

    while pagination['current_page'] < pagination['total_pages']:
        pagination['current_page'] += 1
        response = requests.get(url, headers=headers, params={'page': pagination['current_page']})
        response_json += response.json()['data']
        response_df = pd.DataFrame(response_json)
        properties_list = response_df['id'].tolist()
        properties_list = list(map(int, properties_list))

    return properties_list

#### GET RESERVATIONS ###

def get_reservations(token): 
    url = "https://api.hospitable.com/calendar/reservations"
    properties_list = get_list_properties(token)

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    params = {
        "properties[]": properties_list
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    pagination = result['_pagination']
    response_json = result['data']
  
    while pagination['current_page'] < pagination['total_pages']:
        pagination['current_page'] += 1
        response = requests.get(url, headers=headers, params={'page': pagination['current_page'], "properties[]": properties_list})
        response_dict = response.json()
        if 'data' in response_dict:
            response_json += response_dict['data']

    df = pd.DataFrame(response_json)
    
    # Insert new "Date" column with current date in yyyy-mm-dd format at the beginning of the DataFrame
    date_str = START_DATE
    df.insert(0, "Date", date_str)
    
    # Add condition to replace 'listing_id' with 99999999 if 'provider' is not "airbnb-official"
    df.loc[df['provider'] != 'airbnb-official', 'listing_id'] = 99999999
    
    return df

################### UPLOAD TO GCS    ############


def upload_reservations_to_gcs(bucket_name, token):
    file_name = "hostable_report.csv"
    df = get_reservations(token)
    path = 'reservations/' +"dt="+ START_DATE + "/"
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    blob = bucket.blob(path+file_name)
    blob.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')
    print(f"File uploaded to {bucket_name}/{path}")
    
def upload_properties_to_gcs(bucket_name):
    file_name = "properties_test.csv"
    df = get_properties(token)
    path = 'properties/'
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    blob = bucket.blob(path+file_name)
    blob.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')
    print(f"File uploaded to {bucket_name}/{file_name}")

def upload_listings_to_gcs(bucket_name):
    file_name = "listings_test.csv"
    df = get_listings(token)
    path = 'listings/'
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    blob = bucket.blob(path+file_name)
    blob.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')
    print(f"File uploaded to {bucket_name}/{file_name}")
    





###################  UPLOAD TO BIGQUERY  ############


#######################################################################################
def upload_properties_bigquery(token):
    data = get_properties(token)
    project_id = 'hostair-gcp-prod'
    dataset = 'hostable_pipeline'
    table = 'Hostable_Properties'
    client = bigquery.Client(project=project_id, location="EU")
    dataset_ref = client.dataset(dataset)
    table_ref = dataset_ref.table(table)
    # Check if table exists and get the schema
    try:
        table = client.get_table(table_ref)
        schema = table.schema
    except NotFound:
        schema = None
    # Check if the data already exists in the table
    if schema:
        primary_key = ["id", "name"]
        query = f"SELECT COUNT(*) FROM `{table}` WHERE {' AND '.join([f'`{key}` IN UNNEST(@value_{i})' for i, key in enumerate(primary_key)])}"
        # Add query parameter
        query_params = []
        for i, key in enumerate(primary_key):
            query_params.append(bigquery.ArrayQueryParameter(f"value_{i}", "STRING", [str(val) for val in data[key]]))
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = query_params
        job = client.query(query, job_config=job_config)
        results = job.result()
        count = sum([row.values()[0] for row in results])
        if count > 0:
            print(f"The data already exists in the table, skipping upload.")
            return
    # Upload the data to BigQuery
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.schema_update_options = [bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    job_config.create_disposition = bigquery.CreateDisposition.CREATE_IF_NEEDED
    job_config.autodetect = False
    job = client.load_table_from_dataframe(data, table_ref, job_config=job_config)
    job.result()
    # Confirm that the data has been uploaded
    print(f"The data has been uploaded to the table {project_id}.{dataset}.{table}.")


def upload_listings_bigquery(token):
    data = get_listings(token)
    project_id = 'hostair-gcp-prod'
    dataset = 'hostable_pipeline'
    table = 'Hostable_Listings'
    client = bigquery.Client(project=project_id, location="EU")
    dataset_ref = client.dataset(dataset)
    table_ref = dataset_ref.table(table)
    # Check if table exists and get the schema
    try:
        table = client.get_table(table_ref)
        schema = table.schema
    except NotFound:
        schema = None
    # Check if the data already exists in the table
    if schema:
        primary_key = ["id", "name"]
        query = f"SELECT COUNT(*) FROM `{table}` WHERE {' AND '.join([f'`{key}` IN UNNEST(@value_{i})' for i, key in enumerate(primary_key)])}"
        # Add query parameters
        query_params = []
        for i, key in enumerate(primary_key):
            query_params.append(bigquery.ArrayQueryParameter(f"value_{i}", "STRING", [str(val) for val in data[key]]))
        
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = query_params
        job = client.query(query, job_config=job_config)
        results = job.result()
        count = sum([row.values()[0] for row in results])
        if count > 0:
            print(f"The data already exists in the listings table, skipping upload.")
            return
    # Upload the data to BigQuery
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.schema_update_options = [bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    job_config.create_disposition = bigquery.CreateDisposition.CREATE_IF_NEEDED
    job_config.autodetect = False
    job = client.load_table_from_dataframe(data, table_ref, job_config=job_config)
    job.result()
    # Confirm that the data has been uploaded
    print(f"The data has been uploaded to the table {project_id}.{dataset}.{table}.")   


##########################
def main():
    bucket='hostair_hostable'
    token = authenticate(url, headers, data)
    upload_properties_bigquery(token)
    upload_listings_bigquery(token)
    upload_reservations_to_gcs(bucket_name, token)
    print ("This works :)")

main()