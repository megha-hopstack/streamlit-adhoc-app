#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 21:33:29 2025

@author: megha
"""

from pymongo import MongoClient
import pandas as pd
from config import get_boto3_session, get_secret

# Get boto3 session
session = get_boto3_session()

# Define secret ARNs
SECRET_NA_ARN = 'arn:aws:secretsmanager:us-east-1:893141651859:secret:HSI-PROD-DB-READ-ONLY-USER-US-EAST-1-EVeOjL'
SECRET_SE_ARN = 'arn:aws:secretsmanager:ap-southeast-1:893141651859:secret:HSI-PROD-DB-READ-ONLY-USER-AP-SOUTHEAST-1-G8hGif'

# Retrieve connection URIs
north_america_uri = get_secret(session, 'us-east-1', SECRET_NA_ARN)
south_east_uri = get_secret(session, 'ap-southeast-1', SECRET_SE_ARN)

# Create MongoClient connections
north_america_client = MongoClient(north_america_uri)
south_east_client = MongoClient(south_east_uri)

north_america_database = north_america_client["platform-production"]
south_east_database = south_east_client["platform-production"]

