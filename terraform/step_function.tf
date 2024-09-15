resource "aws_iam_role" "step_function_role" {
  name = "step_function_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { 
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_function_policy" {
  name   = "step_function_policy"
  role   = aws_iam_role.step_function_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "lambda:InvokeFunction",
          "lambda:ListFunctions"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "step_function" {
  name     = "CBB-AI"
  role_arn = aws_iam_role.step_function_role.arn
  definition = file("${path.module}/step_function.json")
}

# resource "aws_cloudwatch_event_rule" "step_function_trigger" {
#   name        = "StepFunctionTrigger"
#   description = "Trigger Step Function every morning at 8am central time"
#   schedule_expression = "cron(0 8 * * ? *)"
# }

# resource "aws_cloudwatch_event_target" "step_function_target" {
#   rule      = aws_cloudwatch_event_rule.step_function_trigger.name
#   arn       = aws_sfn_state_machine.step_function.arn
#   role_arn  = aws_iam_role.step_function_role.arn
#   target_id = "StepFunctionTarget"
# }