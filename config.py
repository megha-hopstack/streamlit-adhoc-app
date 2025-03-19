#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 21:24:01 2025

@author: megha
"""

import os
from dotenv import load_dotenv, find_dotenv
import boto3

# Load local .env file
load_dotenv(find_dotenv())

def get_boto3_session():
    session = boto3.Session(
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
    )
    return session

def get_secret(session, region, secret_arn):
    client = session.client(service_name='secretsmanager', region_name=region)
    return client.get_secret_value(SecretId=secret_arn)['SecretString']
