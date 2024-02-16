import boto3

# Set up AWS SES client
client = boto3.client('ses', region_name='us-east-2')

# Set up the email parameters
sender_email = 'illusionare@tingoeg.com'
recipient_email = 'recipient_email@example.com'
subject = 'Test email from AWS SES'
body = 'Hello, this is a test email sent using AWS SES and Python!'

# Send the email
response = client.send_email(
    Source=sender_email,
    Destination={
        'ToAddresses': [
            recipient_email,
        ],
    },
    Message={
        'Subject': {
            'Data': subject,
        },
        'Body': {
            'Text': {
                'Data': body,
            },
        },
    },
)

# Print the response
print(response)
