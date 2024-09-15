import requests
from bs4 import BeautifulSoup
import boto3
import json
from decimal import Decimal
import os
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")

def calc_average(stat, statNames, data):
    sum = 0
    count = 0
    for name in statNames:
        sum += data[name][stat]
        count += 1
    return sum/count

def addAverage(data):
    for count,team in enumerate(data):
        team['average'] = {
            "offRating":calc_average('offRating', ["barttorvik","kenpom"], team),
            "defRating":calc_average('defRating', ["barttorvik","kenpom"], team),
            "TempoRating":calc_average('TempoRating', ["barttorvik","kenpom"], team),
        }
        data[count] = team
    return data

def addStatRank(data):
    data.sort(key=lambda x: x["barttorvik"]["offRating"] - x["barttorvik"]["defRating"] + x["kenpom"]["offRating"] - x["kenpom"]["defRating"], reverse=True)
    for count,team in enumerate(data):
        team['ranks']['stat_rank'] = count + 1
        data[count] = team
    return data

def addRank(data, flag):
    if flag:
        data.sort(key=lambda x: float(x['ranks']["stat_rank"]) * .25  + (float(x['ranks']["ap_rank"]) or float(x['ranks']["stat_rank"]) + 10) * .50 + float(x['ranks']["net_rank"]) * .25, reverse=False)
    else:
        data.sort(key=lambda x: float(x['ranks']["stat_rank"]) * .50  + (int( x['ranks']["stat_rank"] if x['ranks']["ap_rank"] == None else  x['ranks']["ap_rank"]) + 10) * .50, reverse=False)
    for count,team in enumerate(data):
        team['ranks']['rank'] = count + 1
        data[count] = team
    return data

def addOff(data):
    data.sort(key=lambda x: x["barttorvik"]["offRating"]  + x["kenpom"]["offRating"] , reverse=True)
    for count,team in enumerate(data):
        team['ranks']['rankOff'] = count + 1
        data[count] = team
    return data

def addDef(data):
    data.sort(key=lambda x: x["barttorvik"]["defRating"]  + x["kenpom"]["defRating"] , reverse=False)
    for count,team in enumerate(data):
        team['ranks']['rankDef'] = count + 1
        data[count] = team
    return data

def addTempo(data):
    data.sort(key=lambda x: x["barttorvik"]["TempoRating"]  + x["kenpom"]["TempoRating"] , reverse=True)
    for count,team in enumerate(data):
        team['ranks']['rankTempo'] = count + 1
        data[count] = team
    return data

def update_dynamoDB_table(data):
    logger.info("Updating dynamoDB table")
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        for team in data:
            table.update_item(
                Key={
                    'id': team['id']
                },
                UpdateExpression="set ranks = :r, average = :a",
                ExpressionAttributeValues={
                    ':r': team['ranks'],
                    ':a': team['average']
                },
                ReturnValues="UPDATED_NEW"
            )
        logger.info("DynamoDB table updated")
    except Exception as e:
        logger.error(f"Error updating dynamoDB table: {e}")

def lambda_handler(event, context):
    flag = True if os.environ['NET_FLAG'] == "True" else False
    logger.info("Getting data from dynamoDB", flag = flag)
    errorResponse = {
        'statusCode': 500,
        'body': "error getting data from dynamoDB"
    }
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        response = table.scan()
        data = response['Items']
    except Exception as e:
        logger.error(f"Error getting data from dynamoDB: {e}")
        return errorResponse
    try:
        logger.info("Adding average")
        data = addAverage(data)
    except Exception as e:
        logger.error(f"Error adding average: {e}")
        return errorResponse
    try:
        logger.info("Adding stat rank")
        data = addStatRank(data)
    except Exception as e:
        logger.error(f"Error adding stat rank: {e}")
        return errorResponse
    try:
        logger.info("Adding rank")
        data = addRank(data, flag)
    except Exception as e:
        logger.error(f"Error adding rank: {e}")
        return errorResponse
    try:
        logger.info("Adding off rank")
        data = addOff(data)
    except Exception as e:  
        logger.error(f"Error adding off rank: {e}")
        return errorResponse
    try:
        logger.info("Adding def rank")
        data = addDef(data)
    except Exception as e:
        logger.error(f"Error adding def rank: {e}")
        return errorResponse
    try:
        logger.info("Adding tempo rank")
        data = addTempo(data)
    except Exception as e:
        logger.error(f"Error adding tempo rank: {e}")
        return errorResponse
    update_dynamoDB_table(data)
    return {
        'statusCode': 200,
        'body': "data updated"
    }