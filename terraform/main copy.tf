provider "google" {
  project = var.tgt_project_id
  region  = var.gcp_region
  zone    = var.gcp_rg_zone
}

data "google_project" "tgt_project" {
  project_id = var.tgt_project_id
}

###############################################
# BigQuery datasets
###############################################

resource "google_bigquery_dataset" "operations_dataset" {
  dataset_id = "operations" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Operational Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "support_dataset" {
  dataset_id = "support" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Operational Support Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "maintenance_dataset" {
  dataset_id = "maintenance" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Maintenance Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "finance_dataset" {
  dataset_id = "finance" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Finance Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "sales_dataset" {
  dataset_id = "sales" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Sales Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "customer_service_dataset" {
  dataset_id = "customer_service" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Customer Service Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}

resource "google_bigquery_dataset" "housekeeping_dataset" {
  dataset_id = "housekeeping" 
  project    = var.tgt_project_id                 
  location   = var.gcp_region                     
  description = "Housekeeping Dataset."
  labels = {
    environment = var.environment
  }
  access {
  role          = "OWNER"
  user_by_email = "eleazar@hostairmx.com" 
  }
  access {
  role          = "WRITER"    
  group_by_email = "bigquery-readers@hostairmx.com"   
  }
}
###############################################
