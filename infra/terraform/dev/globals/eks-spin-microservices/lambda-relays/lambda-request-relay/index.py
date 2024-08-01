import requests
import os

def lambda_handler(event, context):

    global request_url

    # Debug
    print("event: ", event)

    # Input var
    request_url = os.environ['request_url']
    request_http_method = os.environ['request_http_method']

    response = send_request(request_http_method, request_url, event)
    response_body = response.text
    response_status = response.status_code

    # Debug
    print("http call response: ", response_body)
    print("http response status: ", response_status)
    print("request url: ", request_url)
    print("verb: ",request_http_method)

    if response_status >=202 and response_status<300:
      return {
        'statusCode': 200
      }
    else:
      raise Exception("Event delivery fail")

def send_request(http_method, resquest_url, event):
    response = requests.request(http_method,url=request_url, json=event)
    return response
