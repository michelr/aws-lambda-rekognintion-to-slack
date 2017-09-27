import logging
import json
import httplib2
import locale
import boto3
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
reko_client = boto3.client('rekognition')


def handler(event, context):
    locale.setlocale(locale.LC_ALL, "sv_SE.UTF-8")
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = reko_client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key,
            },
        },
        MaxLabels=10,
        MinConfidence=70,
    )

    celebs = reko_client.recognize_celebrities(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key,
            },
        }
    )

    body = ''
    for item in response['Labels']:
        body += '{0:.0f}% sure -> {1} \n'.format(item['Confidence'], item['Name'])

    for celeb in celebs['CelebrityFaces']:
        response = reko_client.get_celebrity_info(Id=celeb['Id'])
        body += 'Famous fucker: {} \n'.format(response['Name'])
    
    # slack
    webhook_url = "https://hooks.slack.com/services/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"
    payload = {
        "attachments": [
            {
                "fallback": "Image rekogn on it's way!",
                "color": "#36a64f",
                "title": "I think image {} might be: ".format(key),
                "pretext": "Image rekogno",
                "text": body + "\n",
                "mrkdwn_in": [
                    "text",
                    "pretext"
                ]
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    http = httplib2.Http()
    response, content = http.request(webhook_url, 'POST', headers=headers, body=json.dumps(payload))
    logger.info(response)

    return "SUCCESS"
