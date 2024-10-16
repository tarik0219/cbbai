import boto3
import os
from utilscbb.espn import call_espn_team_standings_api
from utilscbb.schedule import get_team_schedule
from utilscbb.dynamo import get_all_team_data
from aws_lambda_powertools import Logger
import concurrent.futures

logger = Logger(service="cbb-ai")


def update_team_records_dynamo(teamID, record):
    logger.info("Updating dynamoDB table with records data")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cbb-ai')
    table.update_item(
        Key={
            'id': teamID
        },
        UpdateExpression='SET records = :val',
        ExpressionAttributeValues={
            ':val': record
        }
    )
    logger.info("DynamoDB table updated with records data")
    
def check_env_bool(env_var):
    if env_var == "True":
        return True
    else:
        return False
    
def update_team_record(team, ALL, YEAR, NET_FLAG, teamRecords):
    try:
        if ALL:
            scheduleRecordData = get_team_schedule(team['id'], YEAR, NET_FLAG)['records']
            del scheduleRecordData["probs"]
            logger.info(f"Updating team record for {team['id']}", team=team['id'], record=scheduleRecordData)
            update_team_records_dynamo(team['id'], scheduleRecordData)
            return
        teamRecord = team.get('records', None)
        newTeamRecord = teamRecords[team['id']]
        if teamRecord is None or teamRecord['win'] + teamRecord['loss'] != newTeamRecord['win'] + newTeamRecord['loss']:
            logger.info(f"Updating team record for {team['id']}")
            scheduleRecordData = get_team_schedule(team['id'], YEAR, NET_FLAG)['records']
            del scheduleRecordData["probs"]
            update_team_records_dynamo(team['id'], scheduleRecordData)
    except Exception as e:
        logger.exception(f"Error updating team record for {team['id']}: {e}")

def lambda_handler(event, context):
    try:
        NET_FLAG = os.environ.get('NET_FLAG')
        NET_FLAG = check_env_bool(NET_FLAG)
        YEAR = os.environ.get('YEAR')
        ALL = check_env_bool(os.environ.get('ALL'))
        logger.info("Calling ESPN API for team records")
        try:
            teamRecords = call_espn_team_standings_api(YEAR)
        except Exception as e:
            teamRecords = {}
        logger.info("Getting all team data from dynamoDB")
        teams = get_all_team_data()
        logger.info("Comparing team records")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_team_record, team, ALL, YEAR, NET_FLAG, teamRecords) for team in teams]
            concurrent.futures.wait(futures)
    except Exception as e:
        logger.exception(e)
        return {
            'statusCode': 500,
            'body': str(e)
        }
    return {
        'statusCode': 200,
        'body': "Success"
    }