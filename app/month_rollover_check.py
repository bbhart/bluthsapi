"""
Month-Rollover Check Lambda Handler

Invoked by EventBridge on the 1st of each month at 00:05 UTC. Reads the
API Gateway prod stage's throttle setting. If the throttle is still 0
(meaning a previous-month BudgetShutdownFunction invocation disabled the
API and was never restored), publishes a reminder email to BudgetAlertsTopic
pointing the operator at docs/budget-reset.md.

This Lambda is strictly READ-ONLY. Its IAM role grants only apigateway:GET
and sns:Publish.
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

apigatewayv2 = boto3.client('apigatewayv2')
sns = boto3.client('sns')


def handler(event, context):
    api_id = os.environ.get('API_GATEWAY_ID')
    topic_arn = os.environ.get('SNS_TOPIC_ARN')

    if not api_id or not topic_arn:
        error_msg = 'API_GATEWAY_ID and SNS_TOPIC_ARN env vars are required'
        print(f'ERROR: {error_msg}')
        return {'statusCode': 500, 'body': json.dumps({'error': error_msg})}

    try:
        stage = apigatewayv2.get_stage(ApiId=api_id, StageName='prod')
        default_settings = stage.get('DefaultRouteSettings', {})
        throttle = default_settings.get('ThrottlingRateLimit')

        print(f'API {api_id} prod stage ThrottlingRateLimit={throttle}')

        disabled = throttle == 0

        if disabled:
            message = (
                f'The bluths-api API Gateway ({api_id}) prod stage throttle '
                f'is set to 0, meaning the API is disabled. This typically '
                f'happens after a budget-triggered shutdown.\n\n'
                f'To restore service, follow the runbook at '
                f'docs/budget-reset.md in the bluths-api repository.\n\n'
                f'This is a monthly check — if you intended to leave the API '
                f'disabled, you can ignore this message.'
            )
            sns.publish(
                TopicArn=topic_arn,
                Subject='Bluths API still disabled — see docs/budget-reset.md',
                Message=message,
            )
            print(f'Published reminder to {topic_arn}')

        return {
            'statusCode': 200,
            'body': json.dumps({'disabled': disabled, 'throttle': throttle}),
        }

    except ClientError as e:
        error_msg = f'Failed to read or publish: {str(e)}'
        print(f'ERROR: {error_msg}')
        return {'statusCode': 500, 'body': json.dumps({'error': error_msg})}
