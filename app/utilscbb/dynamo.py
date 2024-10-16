import boto3
from boto3.dynamodb.conditions import Key


def get_all_team_data():
    try:
        boto3.setup_default_session(profile_name='tarik0219')
    except:
        pass
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')
    response = table.scan()
    data = response['Items']
    return data

def get_team_data_name(team_name):
    try:
        boto3.setup_default_session(profile_name='tarik0219')
    except:
        pass
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')  # Replace with your actual table name
    response = table.query(
        IndexName='teamName-index',
        KeyConditionExpression=Key('teamName').eq(team_name)
    )

    return response.get('Items', [])

# batch get items from dynamodb odds table
def get_odds_data(gameIDs):
    try:
        boto3.setup_default_session(profile_name='tarik0219')
    except:
        pass
    client = boto3.client('dynamodb', region_name='us-east-2')
    if not gameIDs:
        return []
    if len(gameIDs) > 100:
        return []
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