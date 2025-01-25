import boto3
import json

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
    file_path = '/Users/meghanakillada/VSCodeProjects/LPLHackathon2025Team8/documents/Detailed_Compliance_Workflow_Report.pdf'
    file_name = 'Detailed_Compliance_Workflow_Report.pdf'
    upload_document(file_path, file_name)
    
    # Extract text and simulate compliance flag
    job_id = extract_text(file_name)
    compliance_flag = True  # Example flag for testing
    
    # Trigger workflow with extracted data
    trigger_workflow(document_id=file_name, compliance_flag=compliance_flag)