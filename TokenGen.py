import boto3

#Update Region Name
client = boto3.client('cognito-idp', region_name='ap-south-1')  # e.g., 'us-east-1'

#Add Details
uesername = 'admin'
password = 'admin@123'
clientID = 'admin'
UserPoolID = 'admin'


# Step 1: Start authentication
auth_response = client.admin_initiate_auth(
    AuthFlow='ADMIN_NO_SRP_AUTH',
    AuthParameters={
        'USERNAME': uesername,
        'PASSWORD': password
    },
    ClientId=clientID,
    UserPoolId=UserPoolID
)

# Step 2: Handle NEW_PASSWORD_REQUIRED challenge
if auth_response.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
    session = auth_response["Session"]

    challenge_response = client.respond_to_auth_challenge(
        ClientId=clientID,
        ChallengeName='NEW_PASSWORD_REQUIRED',
        Session=session,
        ChallengeResponses={
            'USERNAME': uesername,
            'NEW_PASSWORD': password
        }
    )

    # Tokens
    id_token = challenge_response['AuthenticationResult']['IdToken']
    access_token = challenge_response['AuthenticationResult']['AccessToken']
    refresh_token = challenge_response['AuthenticationResult']['RefreshToken']

    print("✅ ID Token:", id_token)
    print("✅ Access Token:", access_token)
    print("✅ Refresh Token:", refresh_token)
