# Allianz
# Allianz Serverless VPC Deployment

This project automates the creation of AWS VPCs using a serverless architecture built on:
- AWS Lambda
- API Gateway (secured with Cognito User Pools)
- DynamoDB for VPC metadata storage

## 🧱 Architecture
- REST API (GET/POST)
- Cognito authentication
- Lambda function that creates and fetches VPCs
- Infrastructure provisioned via CloudFormation

## 📦 Files Included
- `Solution-Infra.json`: CloudFormation template to deploy all AWS resources
- `TokenGen.py`: Script to authenticate with Cognito and get JWT token
- `Allianz_Final_VPC_Documentation.pdf`: Full implementation guide
- `Allianz_Final_VPC_Documentation.docx`: Word version of documentation

## 🚀 Deployment Steps

### 1. Clone the Repository
```bash
git clone https://github.com/pratik1415/Allianz.git
cd Allianz

Deploy with CloudFormation:
Upload Solution-Infra.json
Enter Stack Name and Lambda Function Name
Wait for deployment to complete
Token Generation
Run TokenGen.py after configuring it with Cognito credentials to get your Bearer token.

API Usage

POST /invoke
Authorization: Bearer <ID_TOKEN>
Body:
{
  "vpcName": "MyCustomVPC"
}

GET /invoke?vpcName=MyCustomVPC
Authorization: Bearer <ID_TOKEN>