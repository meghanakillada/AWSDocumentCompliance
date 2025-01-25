from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, AWS EC2!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
    import boto3
import random
from fpdf import FPDF

class MockComplianceDocument(FPDF):
    def header(self):
        self.set_font("Arial", size=12)
        self.cell(0, 10, "Compliance Report", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")

    def add_section(self, title, content):
        self.set_font("Arial", size=12, style="B")
        self.cell(0, 10, title, ln=True)
        self.ln(5)
        self.set_font("Arial", size=10)
        self.multi_cell(0, 10, content)
        self.ln(5)

# Generate mock compliance document
def create_mock_document(output_path):
    pdf = MockComplianceDocument()
    pdf.alias_nb_pages()
    pdf.add_page()

    employee_details = (
        f"Employee ID: {random.randint(1000, 9999)}\n"
        f"Name: John Doe\n"
        f"Department: Sales\n"
        f"Position: Advisor\n"
        f"Date: {random.randint(1, 28)}/01/2025\n"
    )
    pdf.add_section("Employee Details", employee_details)

    compliance_observations = (
        "1. Policy exception request regarding client data sharing.\n"
        "2. Customer interaction flagged for possible privacy breach.\n"
        "3. Late submission of quarterly reports.\n"
    )
    pdf.add_section("Compliance Observations", compliance_observations)

    recommendations = (
        "- Provide training on data privacy policies.\n"
        "- Implement stricter deadlines for report submissions.\n"
        "- Conduct a follow-up audit to ensure compliance.\n"
    )
    pdf.add_section("Recommendations", recommendations)

    sign_off = (
        "Reviewed by: Jane Smith\n"
        "Title: Compliance Officer\n"
        "Signature: ______________________\n"
    )
    pdf.add_section("Sign-Off", sign_off)

    pdf.output(output_path)

# Upload the document to AWS S3
def upload_to_s3(file_path, bucket_name, object_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        print(f"File uploaded to S3: s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

# Start AWS Step Functions workflow
def start_step_function(state_machine_arn, document_key):
    stepfunctions = boto3.client('stepfunctions')
    try:
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({"documentKey": document_key})
        )
        print(f"Step Function started: {response['executionArn']}")
    except Exception as e:
        print(f"Error starting Step Function: {e}")

# Train model with SageMaker
def train_sagemaker_model(training_data_s3_path, model_output_s3_path):
    sagemaker = boto3.client('sagemaker')
    try:
        training_job_name = f"compliance-training-{random.randint(1000, 9999)}"
        response = sagemaker.create_training_job(
            TrainingJobName=training_job_name,
            AlgorithmSpecification={
                'TrainingImage': '123456789012.dkr.ecr.us-east-1.amazonaws.com/compliance-model:latest',
                'TrainingInputMode': 'File'
            },
            RoleArn='arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole',
            InputDataConfig=[
                {
                    'ChannelName': 'training',
                    'DataSource': {
                        'S3DataSource': {
                            'S3DataType': 'S3Prefix',
                            'S3Uri': training_data_s3_path,
                            'S3DataDistributionType': 'FullyReplicated'
                        }
                    },
                    'ContentType': 'text/csv'
                }
            ],
            OutputDataConfig={
                'S3OutputPath': model_output_s3_path
            },
            ResourceConfig={
                'InstanceType': 'ml.m5.large',
                'InstanceCount': 1,
                'VolumeSizeInGB': 10
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 3600
            }
        )
        print(f"SageMaker training job started: {training_job_name}")
    except Exception as e:
        print(f"Error starting SageMaker training job: {e}")

# AWS Resource Details
output_path = "Mock_Compliance_Report.pdf"
bucket_name = "compliance-docs-bucket"
object_name = "mock_reports/Mock_Compliance_Report.pdf"
state_machine_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:ComplianceWorkflow"
training_data_s3_path = f"s3://{bucket_name}/training_data/"
model_output_s3_path = f"s3://{bucket_name}/model_output/"

# Workflow Execution
create_mock_document(output_path)
upload_to_s3(output_path, bucket_name, object_name)
start_step_function(state_machine_arn, object_name)
train_sagemaker_model(training_data_s3_path, model_output_s3_path)

print("Compliance automation workflow executed.")
