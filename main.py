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



import boto3
import time
import json
import os

# Initialize AWS clients
textract_client = boto3.client('textract')
sns_client = boto3.client('sns')

# SNS Topic ARN from environment variable (you must set this in Lambda's environment variables)
COMPLIANCE_SNS_TOPIC_ARN = os.environ['COMPLIANCE_SNS_TOPIC_ARN']

def lambda_handler(event, context):
    # Extract the S3 bucket and document name from the event
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_document_key = event['Records'][0]['s3']['object']['key']
    
    print(f"Document uploaded: Bucket={s3_bucket}, Document={s3_document_key}")
    
    # Step 1: Start Textract job
    job_id = start_textract_job(s3_bucket, s3_document_key)
    print(f"Started Textract job with JobId: {job_id}")
    
    # Step 2: Poll for Textract job completion
    status, textract_response = check_textract_job_status(job_id)
    
    if status == 'SUCCEEDED':
        # Step 3: Process the extracted data
        compliance_flag = process_extracted_data(textract_response)
        
        # Step 4: Validate compliance
        if compliance_flag:
            print("Document complies with the rules.")
            notify_compliance_result(True)
        else:
            print("Document failed compliance.")
            notify_compliance_result(False)
    else:
        print(f"Textract job failed with status: {status}")
        notify_compliance_result(False)

def start_textract_job(s3_bucket, s3_document_key):
    """Starts the Textract job to extract text from the document"""
    response = textract_client.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': s3_bucket, 'Name': s3_document_key}}
    )
    return response['JobId']

def check_textract_job_status(job_id):
    """Polls the Textract job status until completion"""
    while True:
        response = textract_client.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
        
        if status in ['SUCCEEDED', 'FAILED']:
            return status, response
        print(f"Textract job still in progress. Status: {status}")
        time.sleep(30)  # Poll every 30 seconds

def process_extracted_data(textract_response):
    """Process the extracted data from Textract and check for compliance"""
    extracted_data = textract_response['Blocks']
    compliance_flag = validate_compliance(extracted_data)
    return compliance_flag

def validate_compliance(extracted_data):
    """Validate compliance by checking the extracted data for certain conditions"""
    # Example compliance check: if 'compliant' keyword exists in any extracted text
    for block in extracted_data:
        if block['BlockType'] == 'LINE' and 'compliant' not in block['Text'].lower():
            return False
    return True

def notify_compliance_result(is_compliant):
    """Send an SNS notification based on the compliance check"""
    message = "Document complies with the rules." if is_compliant else "Document failed compliance."
    response = sns_client.publish(
        TopicArn=COMPLIANCE_SNS_TOPIC_ARN,
        Message=message
    )
    print(f"Sent notification: {message}, SNS response: {response}")

