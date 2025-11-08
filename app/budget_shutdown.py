"""
Budget Shutdown Lambda Handler

Automatically disables the API Gateway when the AWS Budget limit is reached.
This Lambda is invoked by AWS Budget Actions when spending hits $20/month.

The handler sets the API Gateway throttle rate to 0, causing all requests
to return 429 (Too Many Requests) errors until manually re-enabled.
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
apigatewayv2 = boto3.client('apigatewayv2')


def handler(event, context):
    """
    Lambda handler invoked by AWS Budget Actions.

    Disables the API Gateway by setting throttle limits to 0.

    Args:
        event: Budget action event (contains budget details)
        context: Lambda context

    Returns:
        dict: Response with status code and message
    """

    # Get API Gateway ID from environment variable
    api_id = os.environ.get('API_GATEWAY_ID')

    if not api_id:
        error_msg = "API_GATEWAY_ID environment variable not set"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    try:
        # Log the budget event for debugging
        print(f"Budget limit reached. Event: {json.dumps(event)}")

        # Get current stage configuration
        stage_response = apigatewayv2.get_stage(
            ApiId=api_id,
            StageName='prod'
        )

        print(f"Current stage config: {json.dumps(stage_response, default=str)}")

        # Update stage to disable throttling (set to 0 requests/second)
        update_response = apigatewayv2.update_stage(
            ApiId=api_id,
            StageName='prod',
            DefaultRouteSettings={
                'ThrottlingBurstLimit': 0,
                'ThrottlingRateLimit': 0.0
            }
        )

        success_msg = f"API Gateway {api_id} has been disabled due to budget limits"
        print(f"SUCCESS: {success_msg}")
        print(f"Updated stage config: {json.dumps(update_response, default=str)}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': success_msg,
                'api_id': api_id,
                'action': 'throttle_disabled'
            })
        }

    except ClientError as e:
        error_msg = f"Failed to disable API Gateway: {str(e)}"
        print(f"ERROR: {error_msg}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'api_id': api_id
            })
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"ERROR: {error_msg}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }
