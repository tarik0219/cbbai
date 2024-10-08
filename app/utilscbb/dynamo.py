import boto3



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

# batch get items from dynamodb odds table
def get_odds_data(gameIDs):
    client = boto3.client('dynamodb', region_name='us-east-2')
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