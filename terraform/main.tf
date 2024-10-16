provider "aws" {
  region = "us-east-2"  # Specify your AWS region
  profile = "tarik0219"
}

#Add variable net_flag to terraform
variable "net_flag" {
  default = "False"
}

variable "year" {
  default = "2025"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../lambda/src"
  output_path = "../lambda/lambda.zip"
}

#pip install layer/requirments.txt int layer/python
resource "null_resource" "install_requirements" {
  provisioner "local-exec" {
    command = "python -m pip install -r ../layer/requirements.txt -t ../layer/python"
    working_dir = "${path.module}"
  }
}

#copy app/utilscbb into layer/python
resource "null_resource" "copy_utilscbb" {
  provisioner "local-exec" {
    command = "cp -r ../app/utilscbb ../layer/python"
    working_dir = "${path.module}"
  }
}

# Package Lambda layer (dependencies)
data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = "../layer"
  output_path = "../lambda_layer.zip"
}

# Create a Lambda layer for dependencies
resource "aws_lambda_layer_version" "lambda_layer" {
  filename = "../lambda_layer.zip"
  layer_name = "my-python-layer"
  compatible_runtimes = ["python3.10"]  # Specify the Python runtime version

  # Optional: Specify license
  license_info = "MIT"
}

# Create the Lambda function for KenPom
resource "aws_lambda_function" "lambda_function_kenpom" {
  function_name = "kenpom"
  filename      = "../lambda/lambda.zip"
  handler       = "kenpom.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 300
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
  
  environment {
    variables = {
      ENV = "dev"
    }
  }
}

# Create the Lambda function for Barttorvik
resource "aws_lambda_function" "lambda_function_barttorvik" {
  function_name = "barttorvik"
  filename      = "../lambda/lambda.zip"
  handler       = "barttorvik.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 300
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
  
}

# Create the Lambda function for AP Top 25
resource "aws_lambda_function" "lambda_function_ap_top25" {
  function_name = "ap_top25"
  filename      = "../lambda/lambda.zip"
  handler       = "ap_25.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 300
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
}

# Create Lambda for net rating
resource "aws_lambda_function" "lambda_function_net_rating" {
  function_name = "net_rating"
  filename      = "../lambda/lambda.zip"
  handler       = "net.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 300
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer

  environment {
    variables = {
      NET_FLAG = var.net_flag
    }
  }
}

# Create Lambda for Stats Ranks
resource "aws_lambda_function" "lambda_function_stats_ranks" {
  function_name = "stats_ranks"
  filename      = "../lambda/lambda.zip"
  handler       = "stats.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 300
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
  environment {
    variables = {
      NET_FLAG = var.net_flag
    }
  }
}


# Create Lambda for Stats Records
resource "aws_lambda_function" "lambda_function_records" {
  function_name = "records"
  filename      = "../lambda/lambda.zip"
  handler       = "records.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 900
  memory_size = 512
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
  environment {
    variables = {
      NET_FLAG = var.net_flag
      YEAR = var.year
      ALL = "True"
    }
  }
}

#Create lambda for adding odds
resource "aws_lambda_function" "lambda_function_add_odds" {
  function_name = "add_odds"
  filename      = "../lambda/lambda.zip"
  handler       = "add_odds.lambda_handler"  # Update if needed
  runtime       = "python3.10"
  role          = "arn:aws:iam::867522236259:role/lambda"  # Update with the ARN of the IAM role
  timeout = 900
  layers = [aws_lambda_layer_version.lambda_layer.arn]  # Attach the Lambda layer
}

#Create a DynamoDB table
resource "aws_dynamodb_table" "example_table" {
  name           = "cbb-ai"  # Change the table name as per your requirement
  billing_mode   = "PAY_PER_REQUEST" # Choose billing mode, can be PROVISIONED for manual scaling

  hash_key       = "id"         # Primary key

  attribute {
    name = "id"
    type = "S"                 # Attribute type (S for String, N for Number, B for Binary)
  }

  tags = {
    project        = "cbb-ai" # Replace with your tag values
  }
}

#Create a S3 bucket
resource "aws_s3_bucket" "example_bucket" {
  bucket = "cbb-ai"  # Change the bucket name as per your requirement
  tags = {
    project        = "cbb-ai" # Replace with your tag values
  }
}

#Add objects in dicts folder to the bucket
resource "aws_s3_bucket_object" "example_object" {
  for_each = fileset("../dicts", "**/*")
  bucket = aws_s3_bucket.example_bucket.bucket
  key    = each.value
  source = "../dicts/${each.value}"
}