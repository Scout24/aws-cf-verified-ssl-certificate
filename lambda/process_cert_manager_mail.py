import json
import re
import requests

def get_header(headers, name):
    for header in headers:
        if header['name'] == name:
            return header['value']
    return None

def is_amazon_email(message):
    if 'headers' not in message['mail']:
        print 'headers not found.'
        return False

    headers = message['mail']['headers']

    domain = get_header(headers, 'Domain')
    stackName = get_header(headers, 'StackName')
    subject = get_header(headers, 'Subject')

    if not domain or not stackName:
        print 'ERROR: could not find Domain or StackName header'
        return False

    if not domain in subject:
        print 'ERROR: domain is not in subject'
        return False

    if get_header(headers, 'X-SES-Spam-Verdict') != 'PASS':
        print 'ERROR: message seems to be spam'
        return False

    if get_header(headers, 'X-SES-Virus-Verdict') != 'PASS':
        print 'ERROR: message seems to contain a virus'
        return False

    return True


def lambda_handler(event, context):

    try:
        print 'Event: '
        print str(event)
        print 'Context: '
        print str(context)

        lambda_arn = context.invoked_function_arn
        print 'Function ARN: {}'.format(lambda_arn)

        lambda_arn_parts = lambda_arn.split(':')
        region = lambda_arn_parts[3]
        account_id = lambda_arn_parts[4]

        print 'Region: {}'.format(region)
        print 'Account ID: {}'.format(account_id)


        for record in event['Records']:
            message = json.loads(record['Sns']['Message'])
            if not is_amazon_email(message):
                print 'Found unknown email!'
                continue

            print 'Found Amazon email'
            email_content = message['content']

            pattern = re.compile('https://[0-9a-z-]+\.certificates.amazon.com/approvals[?&0-9a-zA-Z=-]+')
            match = pattern.search(email_content)
            if not match:
                print 'Could not find URL in content!'
                continue

            verification_url = match.group()
            print 'Found verification url: '
            print verification_url

            response = requests.get(verification_url, verify=False)
            if response.status_code != 200:
                raise Exception('Calling verification url failed.')

            page_content = response.content
            print 'Verification URL Content: '
            print page_content

            account_id_formatted = '{}-{}-{}'.format(account_id[0:4], account_id[4:8], account_id[8:12])
            if region not in page_content or account_id_formatted not in page_content:
                print "ERROR: Verification page is not from expected account or region!!!! {} or {} is missing.".format(region, account_id_formatted)
                continue

            print 'Found {} and {} on verification page. It seems to be the right page!'.format(region, account_id_formatted)

            from input_field_parser import InputFieldParser
            parser = InputFieldParser()
            parser.feed(page_content)

            payload = map(lambda entry: (entry['name'], entry['value']), parser.inputs)
            print 'Payload: ', payload

            response = requests.post("https://certificates.amazon.com/approvals", data=payload, verify=False)
            print 'POST response: ', response.status_code
            print 'POST response: ', response.content


    except Exception as e:
        print 'Exception occured: ' + str(e)
        raise Exception('Could not process email.', e)
