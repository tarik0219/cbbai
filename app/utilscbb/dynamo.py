import boto3
from boto3.dynamodb.conditions import Key
from constants import constants


def boto3_setup():
    try:
        boto3.setup_default_session(aws_access_key_id=constants.aws_access_key_id, aws_secret_access_key=constants.aws_secret_access) 
    except:
        try:
            boto3.setup_default_session(profile_name='tarik0219')
        except:
            pass


def get_all_team_data():
    boto3_setup()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')
    response = table.scan()
    data = response['Items']
    # get rid of all the items with no teamName
    data = [item for item in data if 'teamName' in item]
    return data

def get_team_data_name(team_name):
    boto3_setup()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')  # Replace with your actual table name
    response = table.query(
        IndexName='teamName-index',
        KeyConditionExpression=Key('teamName').eq(team_name)
    )

    return response.get('Items', [])

# batch get items from dynamodb odds table
def get_odds_data(gameIDs):
    boto3_setup()
    client = boto3.client('dynamodb', region_name='us-east-2')
    if not gameIDs:
        return []
    if len(gameIDs) > 100:
        #get first 100 odds
        gameIDs = gameIDs[:100]
    response = client.batch_get_item(
        RequestItems={
            'odds': {
                'Keys': [
                    {
                        'gameID': {'S': gameID}
                    } for gameID in gameIDs
                ]
            }
        }
    )
    return response['Responses']['odds']