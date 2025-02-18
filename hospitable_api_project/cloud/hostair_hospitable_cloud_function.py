#import functions_framework
from google.cloud import storage
from datetime import datetime, date, timedelta
import requests
import json
import os


bucket_name = 'hostair_hospitable'

START_DATE = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
END_DATE = (datetime.today() + timedelta(days=150)).strftime('%Y-%m-%d')


def get_headers():
    token = os.environ.get('HOSPITABLE_API')
    if not token:
        raise ValueError("HOSPITABLE_API environment variable not found")
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}"
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
        # Collect property IDs from the current page
        property_ids.extend([property['id'] for property in data['data']])
        # Update the total_pages from the meta information
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
                
                # Check if 'data' key exists in the response
                if 'data' in data:
                    for reservation in data['data']:
                        reservation_id = reservation['id']
                        reservation_code = reservation.get('code', 'No code available')
                        reservations.append({'id': reservation_id, 'code': reservation_code})
                    
                    # Update the total_pages from the meta information
                    total_pages = data['meta']['last_page']
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



def get_conversations(reservations):
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


def upload_to_gcs(bucket_name, START_DATE, conversations):
    project_id = 'hostair-gcp-prod'
    destination_blob = f"conversations/dt={START_DATE}/conversations"
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(conversations)
    print (f"File {conversations} uploaded to {destination_blob} in bucket {bucket_name}.")


def main_2():
    property_ids = get_property_ids(headers)
    reservations = get_reservations(headers, property_ids, START_DATE,END_DATE)
    conversations = get_conversations(headers,reservations)
    upload_to_gcs(bucket_name, START_DATE, conversations)



def main(request):
    if request.method == 'GET':
        try:
            property_ids = get_properties()  
            reservations = get_reservations(property_ids, START_DATE,END_DATE)
            conversations = get_conversations(reservations)
            upload = upload_to_gcs(bucket_name, START_DATE, conversations)
            return upload, 200  # Return the headers with a 200 OK status
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
    else:
        return "Method not supported", 405