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


def process_key_value_pairs(blocks):
    """Process the key-value pairs from the list of blocks.
    :param blocks: List of Block objects from Textract response.
    :return: Dictionary of key-value pairs.
    """
    key_value_pairs = {}

    # Create a mapping of Key Ids to Value Ids
    key_map = {}
    value_map = {}

    for block in blocks:
        if block['BlockType'] == 'KEY':
            key_map[block['Id']] = block
        elif block['BlockType'] == 'VALUE':
            value_map[block['Id']] = block

    # Now we need to find the relationship between keys and values
    for block in blocks:
        if block['BlockType'] == 'KEY':
            key_id = block['Id']
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        value_id = relationship['Ids'][0]
                        if value_id in value_map:
                            value_text = value_map[value_id].get('Text', '')
                            key_text = block.get('Text', '')
                            key_value_pairs[key_text] = value_text

    return key_value_pairs

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
        status = result['statusCode']

        #blocks = result['body']
        #blocks = json.loads(blocks)
        body = result['body']
        if isinstance(body, str):
            blocks = json.loads(body)
        elif isinstance(body, dict):
            blocks = body
        else:
            raise ValueError("Unexpected response body format")

        if status == 200:
            # Process the key-value pairs.
            key_value_pairs = process_key_value_pairs(blocks)
            
            for key, value in key_value_pairs.items():
                print(f"Key: {key}, Value: {value}")

            print("Total key-value pairs detected: " + str(len(key_value_pairs)))
        else:
            print(f"Error: {result['statusCode']}")
            print(f"Message: {result['body']}")

        '''
        if status == 200:
            for block in blocks:
                print('Type: ' + block['BlockType'])
                if block['BlockType'] != 'PAGE':
                    print('Detected: ' + block['Text'])
                    print('Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

                print('Id: {}'.format(block['Id']))
                if 'Relationships' in block:
                    print('Relationships: {}'.format(block['Relationships']))
                print('Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
                print('Polygon: {}'.format(block['Geometry']['Polygon']))
                print()
            print("Blocks detected: " + str(len(blocks)))
        else:
            print(f"Error: {result['statusCode']}")
            print(f"Message: {result['body']}")
        '''

    except ClientError as error:
        logging.error(error)
        print(error)


if __name__ == "__main__":
    main()


