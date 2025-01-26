import boto3
import json
import time
import os

# Initialize AWS clients
s3 = boto3.client('s3')
textract = boto3.client('textract')
stepfunctions = boto3.client('stepfunctions')

# S3 bucket and Step Functions ARN
BUCKET_NAME = 'compliancedocsbucket'
STEP_FUNCTION_ARN = 'arn:aws:states:us-west-2:847343299502:stateMachine:MyStateMachine-k143ab3o4'

# Step 1: Upload document to S3
def upload_document(file_path, file_name):
    s3.upload_file(file_path, BUCKET_NAME, file_name)
    print(f"Document {file_name} uploaded to S3 bucket {BUCKET_NAME}.")

# Step 2: Extract text using Textract
def extract_text(file_name):
    response = textract.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': BUCKET_NAME,
                'Name': file_name
            }
        }
    )
    job_id = response['JobId']
    print(f"Textract job started with Job ID: {job_id}")
    return job_id

# Step 3: Trigger Step Functions workflow
def check_textract_status(job_id):
    while True:
        response = textract.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
        if status == 'SUCCEEDED':
            print("Textract job completed successfully.")
            return response['Blocks']
        elif status == 'FAILED':
            print("Textract job failed.")
            return None
        print("Textract job in progress, checking again...")
        time.sleep(30)  # Wait before checking status again


def process_extracted_data(extracted_data):
    # Process the Textract output and check compliance (simple example)
    compliance_flag = "compliant" in extracted_data  # Simplified compliance check
    return compliance_flag

def trigger_workflow(document_id, compliance_flag):
    input_data = {
        "DocumentID": document_id,
        "ComplianceFlag": compliance_flag
    }
    response = stepfunctions.start_execution(
        stateMachineArn=STEP_FUNCTION_ARN,
        input=json.dumps(input_data)
    )
    print(f"Step Functions workflow triggered. Execution ARN: {response['executionArn']}")


# Example Usage
if __name__ == "__main__":
    # Upload a document
    file_path = input("Please enter the full file path of the document you want to upload: ")
    file_name = os.path.basename(file_path)

    upload_document(file_path, file_name)
    
    job_id = extract_text(file_name)

    # Extract text and simulate compliance flag
    extracted_data = check_textract_status(job_id)
    if extracted_data:
        compliance_flag = process_extracted_data(str(extracted_data))
    
        # Trigger workflow with extracted data
        trigger_workflow(document_id=file_name, compliance_flag=compliance_flag)