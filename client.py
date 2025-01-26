# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose
Test code for running the Amazon Textract Lambda
function example code.
"""

import argparse
import logging
import base64
import json
import io
import boto3

from botocore.exceptions import ClientError
from PIL import Image, ImageDraw


logger = logging.getLogger(__name__)


def analyze_image(function_name, image):
    """Analyzes a document with an AWS Lambda function.
    :param image: The document that you want to analyze.
    :return The list of Block objects in JSON format.
    """

    lambda_client = boto3.client('lambda')

    lambda_payload = {}

    if image.startswith('s3://'):
        logger.info("Analyzing document from S3 bucket: %s", image)
        bucket, key = image.replace("s3://", "").split("/", 1)
        s3_object = {
            'Bucket': bucket,
            'Name': key
        }

        lambda_payload = {"S3Object": s3_object}

    else:
        with open(image, 'rb') as image_file:
            logger.info("Analyzing local document: %s ", image)
            image_bytes = image_file.read()
            data = base64.b64encode(image_bytes).decode("utf8")

            lambda_payload = {"image": data}

    # Call the lambda function with the document.

    response = lambda_client.invoke(FunctionName=function_name,
                                    Payload=json.dumps(lambda_payload))

    return json.loads(response['Payload'].read().decode())


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "function", help="The name of the AWS Lambda function that you want " \
        "to use to analyze the document.")
    parser.add_argument(
        "image", help="The document that you want to analyze.") 


def check_for_missing_values(blocks):
    """
    Checks if any key (Date: or Signature:) is missing its associated value.
    :param blocks: List of Block objects from Textract response.
    :return: List of missing values.
    """
    missing_values = []

    for block in blocks:
        if block['BlockType'] == 'LINE':
            text = block.get('Text', '').strip()
            if text.startswith("Date:"):
                # Check if there's no value after "Date:"
                value = text[len("Date:"):].strip()
                if not value:
                    missing_values.append("Date: is missing a value")
            elif text.startswith("Signature:"):
                # Check if there's no value after "Name:"
                value = text[len("Signature:"):].strip()
                if not value:
                    missing_values.append("Signature: is missing a value")
    
    return missing_values

def main():
    """
    Entrypoint for script.
    """
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")

        # Get command line arguments.
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        # Get analysis results.
        result = analyze_image(args.function, args.image)
        print("Result:", result)

        if 'errorType' in result:
            print(f"Error: {result['errorType']}")
            print(f"Message: {result['errorMessage']}")
            return

        status = result['statusCode']

        body = result['body']
        if isinstance(body, str):
            blocks = json.loads(body)
        elif isinstance(body, dict):
            blocks = body
        else:
            raise ValueError("Unexpected response body format")
            
        logger.debug(f"Received {len(blocks)} blocks from Textract")  # Debugging line to check the number of blocks

        if status == 200:
            # Check for missing values for "Date:" and "Name:".
            missing_values = check_for_missing_values(blocks)
            
            if missing_values:
                for missing in missing_values:
                    print(missing)
            else:
                print("All values for 'Date:' and 'Signature:' are present.")
        else:
            print(f"Error: {result['statusCode']}")
            print(f"Message: {result['body']}")

    except ClientError as error:
        logging.error(error)
        print(error)

if __name__ == "__main__":
    main()

'''
def main():
    """
    Entrypoint for script.
    """
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")

        # Get command line arguments.
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
        add_arguments(parser)
        args = parser.parse_args()

        # Get analysis results.
        result = analyze_image(args.function, args.image)
        print("Result:", result)
        status = result['statusCode']

   
        body = result['body']
        if isinstance(body, str):
            blocks = json.loads(body)
        elif isinstance(body, dict):
            blocks = body
        else:
            raise ValueError("Unexpected response body format")

        if status == 200:
            print("Raw Blocks:")
            print(json.dumps(blocks, indent=4))  # Pretty-print the blocks

            # Process the key-value pairs.
            key_value_pairs = process_key_value_pairs(blocks)
            
            for key, value in key_value_pairs.items():
                print(f"Key: {key}, Value: {value}")

            print("Total key-value pairs detected: " + str(len(key_value_pairs)))
        else:
            print(f"Error: {result['statusCode']}")
            print(f"Message: {result['body']}")


    except ClientError as error:
        logging.error(error)
        print(error)


if __name__ == "__main__":
    main()


'''