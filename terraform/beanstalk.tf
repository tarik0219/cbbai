# Create Zip file for app
data "archive_file" "app_zpi" {
  type        = "zip"
  source_dir  = "../app"
  output_path = "../app.zip"
}

# Create S3 bucket for Python Flask app
resource "aws_s3_bucket" "eb_bucket" {
  bucket = "tarik-flask-app-test-eb" # Name of S3 bucket to create for Flask app deployment needs to be unique 
}

# Upload app.zip to S3 bucket
resource "aws_s3_bucket_object" "app_zip" {
  bucket = aws_s3_bucket.eb_bucket.bucket
  key    = "app.zip"
  source = data.archive_file.app_zpi.output_path
}

# Create IAM role for Elastic Beanstalk
resource "aws_iam_role" "eb_role" {
  name = "elastic_beanstalk_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

# Attach policy to IAM role
resource "aws_iam_role_policy_attachment" "eb_role_policy" {
  role       = aws_iam_role.eb_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

# Create instance profile for Elastic Beanstalk
resource "aws_iam_instance_profile" "eb_instance_profile" {
  name = "elastic_beanstalk_instance_profile"
  role = aws_iam_role.eb_role.name
}

# Create Elastic Beanstalk application
resource "aws_elastic_beanstalk_application" "eb_app" {
  name = "tarik-flask-app-test-eb"
}

# Create Elastic Beanstalk environment
resource "aws_elastic_beanstalk_environment" "eb_env" {
  name                = "cbb-ai"
  application         = aws_elastic_beanstalk_application.eb_app.name
  solution_stack_name = "64bit Amazon Linux 2023 v4.1.4 running Python 3.9"
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "t2.micro"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = "1"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = "1"
  }
  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "EnvironmentType"
    value     = "SingleInstance"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.eb_instance_profile.name
  }
}

# Create Elastic Beanstalk application version
resource "aws_elastic_beanstalk_application_version" "eb_app_version" {
  application = aws_elastic_beanstalk_application.eb_app.name
  bucket      = aws_s3_bucket.eb_bucket.bucket
  key         = "app.zip"
  name        = "v2"
}

# Create a custom policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_full_access_policy" {
  name        = "DynamoDBFullAccessPolicy"
  description = "Policy to allow all DynamoDB operations"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "dynamodb:*"
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Attach the custom policy to the IAM role
resource "aws_iam_role_policy_attachment" "attach_dynamodb_full_access_policy" {
  role       = aws_iam_role.eb_role.name
  policy_arn = aws_iam_policy.dynamodb_full_access_policy.arn
}