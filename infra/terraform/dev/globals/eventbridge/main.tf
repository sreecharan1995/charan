provider "aws" {
  region = var.region
}

#####################################################################################################################
# terraform state module                                                                                            #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest                                       #
#####################################################################################################################
module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinfx"
  stage      = "dev"
  name       = "eventbridge"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}

###########################################################################################################
# Local variables                                                                                         #
###########################################################################################################

locals {
  aws_account_id  = var.aws_account_id
}

###########################################################################################################
# Event bridge for Dev Environment                                                                        #
###########################################################################################################

module "eventbridge" {
  source  = "terraform-aws-modules/eventbridge/aws"
  version = "1.14.0"

  create_bus              = true
  create_connections      = true
  create_api_destinations = true

  bus_name = var.dev_bus_name


  attach_cloudwatch_policy = true
  cloudwatch_target_arns   = [aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn]

  attach_api_destination_policy = true 
 
  rules = {
    dependency_service_messages = {
      description   = "Capture all messages with source = dependency-service"
      event_pattern = jsonencode({ "source" : ["dependency-service"] })
      enabled       = true
    }
    rez_service_messages = {
      description   = "Capture all messages  with source = rez-service"
      event_pattern = jsonencode({ "source" : ["rez-service"] })
      enabled       = true
    }
    sourcing_service_messages = {
      description   = "Capture all messages with source = sourcing-service"
      event_pattern = jsonencode({ "source" : ["sourcing-service"] })
      enabled       = true
    }
    scheduler_job_messages = {
      description   = "Capture all messages with source = scheduler-job"
      event_pattern = jsonencode({ "source" : ["scheduler-job"] })
      enabled       = true
    }
    scheduler_messages = {
      description   = "Capture all messages with source = scheduler-service"
      event_pattern = jsonencode({ "source" : ["scheduler-service"] })
      enabled       = true
    }
  }

  targets = {
    dependency_service_messages = [
      {
        name            = "send-messages-to-websitehook_dev"
        destination     = "webhook_site_dev"
        attach_role_arn = true
      },
      {
        name = "log-message-to-cloudwatch"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      },
      {
        name = "lambday-relay-to-rez-service"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_rez_api_relay"  
      }    
    ]

    rez_service_messages = [
      {
        name            = "send-messages-to-websitehook_dev_ds"
        destination     = "webhook_site_dev"
        attach_role_arn = true
      },
      {
        name = "lambda-relay-dependency-service"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_dependency_api_relay"
      },
      {
        name = "log-message-to-cloudwatch_ds"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]
    sourcing_service_messages = [
      {
        name            = "send-messages-to-websitehook_dev_sourcing"
        destination     = "webhook_site_dev"
        attach_role_arn = true
      },
      {
        name = "lambda-relay-scheduler-service"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_api_relay_dev"
      },
      {
        name = "log-message-to-cloudwatch_dev_sourcing"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]
    scheduler_job_messages = [
      {
        name            = "send-messages-to-websitehook_dev_scheduler_job"
        destination     = "webhook_site_dev"
        attach_role_arn = true
      },
      {
        name = "lambda_scheduler_job_api_relay_dev"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_job_api_relay_dev"
      },
      {
        name = "log-message-to-cloudwatch_dev_scheduler_job"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      }
    ]
    scheduler_messages = [
      {
        name = "log-message-to-cloudwatch_dev_scheduler"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      }
    ]
  }

  connections = {
    webhook_site_dev = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "dev"
        }
      }
    },
    rez-service_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "dev"
        }
      }
    },
    dependency-service_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "dev"
        }
      }
    }
  }

  api_destinations = {
    webhook_site_dev = {
      description                      = "request inspector endpoint"
      invocation_endpoint              = "https://requestinspector.com/inspect/01gg7v81zyxj2rwnsxh8rvn4x5"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    rez-service_endpoint = {
      description                      = "rez-service onevent endpoint"
      invocation_endpoint              = "https://rez-service.dev.spinvfx.com/on-event"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    dependency-service_endpoint = {
      description                      = "dependency-service onevent endpoint"
      invocation_endpoint              = "https://dependencies.dev.spinvfx.com/on-validity-change"
      http_method                      = "PUT"
      invocation_rate_limit_per_second = 20
    }
  }

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

}

###########################################################################################################
# Event bridge for UAT Environment                                                                        #
###########################################################################################################
module "eventbridge_uat" {
  source  = "terraform-aws-modules/eventbridge/aws"
  version = "1.14.0"

  create_bus              = true
  create_connections      = true
  create_api_destinations = true

  bus_name = var.uat_bus_name


  attach_cloudwatch_policy = true
  cloudwatch_target_arns   = [aws_cloudwatch_log_group.uat_bus_cloudwatch_logs.arn]

  attach_api_destination_policy = true

  rules = {
    dependency_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["dependency-service"] })
      enabled       = true
    }
    rez_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["rez-service"] })
      enabled       = true
    }
    sourcing_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["sourcing-service"] })
      enabled       = true
    }
    scheduler_job_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["scheduler-job"] })
      enabled       = true
    }
  }

  targets = {
    dependency_service_messages = [
      {
        name            = "send-messages-to-websitehook_uat"
        destination     = "webhook_site_uat"
        attach_role_arn = true
      },
      # {
      #   name            = "send-messages-to-rez-service"
      #   destination     = "rez-service_uat_endpoint"
      #   attach_role_arn = true
      # },
      {
        name = "lambday-relay-to-rez-service-uat"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_rez_api_relay_uat"  
      },        
      {
        name = "log-message-to-cloudwatch"
        arn  = aws_cloudwatch_log_group.uat_bus_cloudwatch_logs.arn
      } 
    ]

    rez_service_messages = [
      {
        name            = "send-messages-to-websitehook_dev_ds"
        destination     = "webhook_site_uat"
        attach_role_arn = true
      },
      # {
      #   name            = "send-messages-to-dependency-service"
      #   destination     = "dependency-service_uat_endpoint"
      #   attach_role_arn = true

      # },
      {
        name = "lambda-relay-dependency-service-uat"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_dependency_api_relay_uat"
      },      
      {
        name = "log-message-to-cloudwatch_ds"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]

    sourcing_service_messages = [
      {
        name            = "send-messages-to-websitehook_uat_sourcing"
        destination     = "webhook_site_uat"
        attach_role_arn = true
      },
      {
        name = "lambda-relay-scheduler-service"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_api_relay_uat"
      },
      {
        name = "log-message-to-cloudwatch_uat_sourcing"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]

    scheduler_job_messages = [
      {
        name            = "send-messages-to-websitehook_uat_scheduler_job"
        destination     = "webhook_site_uat"
        attach_role_arn = true
      },
      {
        name = "lambda_scheduler_job_api_relay_uat"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_job_api_relay_uat"
      },
      {
        name = "log-message-to-cloudwatch_dev_scheduler_job"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]
  }
  
  connections = {
    webhook_site_uat = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    },
    rez-service_uat_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    },
    dependency-service_uat_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    }
  }

  api_destinations = {
    webhook_site_uat = {
      description                      = "request inspector endpoint - uat env"
      invocation_endpoint              = "https://requestinspector.com/inspect/01gg7v9memwn545gb5pz974b0z"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    rez-service_uat_endpoint = {
      description                      = "rez-service onevent endpoint - uat env"
      invocation_endpoint              = "https://rez-service-uat.dev.spinvfx.com/on-event"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    dependency-service_uat_endpoint = {
      description                      = "dependency-service onevent endpoint - uat env"
      invocation_endpoint              = "https://dependencies-uat.dev.spinvfx.com/on-validity-change"
      http_method                      = "PUT"
      invocation_rate_limit_per_second = 20
    }
  }

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

}

###########################################################################################################
# Event bridge for PROD Environment                                                                        #
###########################################################################################################
module "eventbridge_prod" {
  source  = "terraform-aws-modules/eventbridge/aws"
  version = "1.14.0"

  create_bus              = true
  create_connections      = true
  create_api_destinations = true

  bus_name = var.prod_bus_name


  attach_cloudwatch_policy = true
  cloudwatch_target_arns   = [aws_cloudwatch_log_group.uat_bus_cloudwatch_logs.arn]

  attach_api_destination_policy = true

  rules = {
    dependency_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["dependency-service"] })
      enabled       = true
    }
    rez_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["rez-service"] })
      enabled       = true
    }
    sourcing_service_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["sourcing-service"] })
      enabled       = true
    }
    scheduler_job_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["scheduler-job"] })
      enabled       = true
    }
  }

  targets = {
    dependency_service_messages = [
      {
        name            = "send-messages-to-websitehook_prod"
        destination     = "webhook_site_prod"
        attach_role_arn = true
      },
      # {
      #   name            = "send-messages-to-rez-service"
      #   destination     = "rez-service_uat_endpoint"
      #   attach_role_arn = true
      # },
      {
        name = "lambday-relay-to-rez-service-prod"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_rez_api_relay_prod"  
      },        
      {
        name = "log-message-to-cloudwatch"
        arn  = aws_cloudwatch_log_group.uat_bus_cloudwatch_logs.arn
      } 
    ]

    rez_service_messages = [
      {
        name            = "send-messages-to-websitehook_prod_ds"
        destination     = "webhook_site_prod"
        attach_role_arn = true
      },
      # {
      #   name            = "send-messages-to-dependency-service"
      #   destination     = "dependency-service_uat_endpoint"
      #   attach_role_arn = true

      # },
      {
        name = "lambda-relay-dependency-service-prod"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_dependency_api_relay_prod"
      },      
      {
        name = "log-message-to-cloudwatch_prod_ds"
        arn  = aws_cloudwatch_log_group.prod_bus_cloudwatch_logs.arn
      } 
    ]

    sourcing_service_messages = [
      {
        name            = "send-messages-to-websitehook_prod_sourcing"
        destination     = "webhook_site_prod"
        attach_role_arn = true
      },
      {
        name = "lambda-relay-scheduler-service"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_api_relay_prod"
      },
      {
        name = "log-message-to-cloudwatch_prod_sourcing"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ]

    scheduler_job_messages = [
      {
        name            = "send-messages-to-websitehook_prod_scheduler_job"
        destination     = "webhook_site_prod"
        attach_role_arn = true
      },
      {
        name = "lambda_scheduler_job_api_relay_prod"
        arn = "arn:aws:lambda:us-east-1:${local.aws_account_id}:function:lambda_scheduler_job_api_relay_prod"
      },
      {
        name = "log-message-to-cloudwatch_dev_scheduler_job"
        arn  = aws_cloudwatch_log_group.dev_bus_cloudwatch_logs.arn
      } 
    ] 
  }
  
  connections = {
    webhook_site_prod = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    },
    rez-service_prod_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    },
    dependency-service_prod_endpoint = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "uat"
        }
      }
    }
  }

  api_destinations = {
    webhook_site_prod = {
      description                      = "request inspector endpoint - uat env"
      invocation_endpoint              = "https://requestinspector.com/inspect/01gjkc3b80d7c4p2psmbjz31cv"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    rez-service_prod_endpoint = {
      description                      = "rez-service onevent endpoint - prod env"
      invocation_endpoint              = "https://rez-service-prod.dev.spinvfx.com/on-event"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
    dependency-service_prod_endpoint = {
      description                      = "dependency-service onevent endpoint - uat env"
      invocation_endpoint              = "https://dependencies-prod.dev.spinvfx.com/on-validity-change"
      http_method                      = "PUT"
      invocation_rate_limit_per_second = 20
    }
  }

  tags = {
    env   = "prod"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

}

resource "aws_cloudwatch_log_group" "dev_bus_cloudwatch_logs" {
  name = "/aws/events/dev-bus"

  tags = {
    env   = "dev"
    owner = "rocketpad"
  }
}

resource "aws_cloudwatch_log_group" "uat_bus_cloudwatch_logs" {
  name = "/aws/events/uat-bus"

  tags = {
    env   = "uat"
    owner = "rocketpad"
  }
}

resource "aws_cloudwatch_log_group" "prod_bus_cloudwatch_logs" {
  name = "/aws/events/prod-bus"

  tags = {
    env   = "prod"
    owner = "rocketpad"
  }
}

###########################################################################################################
# Vinita's Event bridge for dev Environment                                                               #
###########################################################################################################
module "vinita_dev_bus" {
  source  = "terraform-aws-modules/eventbridge/aws"
  version = "1.14.0"

  create_bus              = true
  create_connections      = true
  create_api_destinations = true

  bus_name = "vinita-dev"

  attach_api_destination_policy = true

  rules = {
    vinita_messages = {
      description   = "Capture all messages"
      event_pattern = jsonencode({ "source" : ["dependency-service"] })
      enabled       = true
    }
  }
  
  targets = {
    vinita_messages = [
      {
        name            = "send-messages-to-vinita_endpoint"
        destination     = "webhook_site_vinita"
        attach_role_arn = true
      },
      {
        name            = "send-messages-to-webhook_endpoint"
        destination     = "webhook_site"
        attach_role_arn = true
      }
    ] 
  }
  
  connections = {
    webhook_site_vinita = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "dev"
        }
      }
    },
    webhook_site = {
      authorization_type = "API_KEY"
      auth_parameters = {
        api_key = {
          key   = "x-signature-id"
          value = "dev"
        }
      }
    }
  }

  api_destinations = {
    webhook_site_vinita = {
      description                      = "vinita endpoint - dev env"
      invocation_endpoint              = "https://edb6-96-45-204-62.ngrok.io/on-event"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }

    webhook_site = {
      description                      = "request inspector endpoint"
      invocation_endpoint              = "https://requestinspector.com/inspect/01gs8xs2hc214g4m619q7m1p50"
      http_method                      = "POST"
      invocation_rate_limit_per_second = 20
    }
  }

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

}

#####################################################################################################################
# Define lambda permission to call as Event bridge target                                                           #
#####################################################################################################################
resource "aws_lambda_permission" "lambda_rez_api_relay_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_rez_api_relay"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rule_arns.dependency_service_messages
}

resource "aws_lambda_permission" "lambda_dependency_api_relay_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_dependency_api_relay"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rule_arns.rez_service_messages
}

resource "aws_lambda_permission" "lambda_scheduler_api_relay_dev_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_api_relay_dev"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rule_arns.sourcing_service_messages
}

resource "aws_lambda_permission" "lambda_rez_api_relay_uat_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_rez_api_relay_uat"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_uat.eventbridge_rule_arns.dependency_service_messages
}

resource "aws_lambda_permission" "lambda_dependency_api_relay_uat_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_dependency_api_relay_uat"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_uat.eventbridge_rule_arns.rez_service_messages
}

resource "aws_lambda_permission" "lambda_scheduler_api_relay_uat_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_api_relay_uat"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_uat.eventbridge_rule_arns.sourcing_service_messages
}

resource "aws_lambda_permission" "lambda_rez_api_relay_prod_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_rez_api_relay_prod"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_prod.eventbridge_rule_arns.dependency_service_messages
}

resource "aws_lambda_permission" "lambda_dependency_api_relay_prod_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_dependency_api_relay_prod"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_prod.eventbridge_rule_arns.rez_service_messages
}

resource "aws_lambda_permission" "lambda_scheduler_api_relay_prod_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_api_relay_prod"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_prod.eventbridge_rule_arns.sourcing_service_messages
}

resource "aws_lambda_permission" "lambda_scheduler_job_api_relay_dev_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_job_api_relay_dev"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rule_arns.scheduler_job_messages
}

resource "aws_lambda_permission" "lambda_scheduler_job_api_relay_uat_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_job_api_relay_uat"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_uat.eventbridge_rule_arns.scheduler_job_messages
}

resource "aws_lambda_permission" "lambda_scheduler_job_api_relay_prod_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "lambda_scheduler_job_api_relay_prod"
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge_prod.eventbridge_rule_arns.scheduler_job_messages
}
