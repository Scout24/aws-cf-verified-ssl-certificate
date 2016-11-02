import boto3
import cfnresponse
import time

from datetime import datetime

def lambda_handler(event, context):

    response_data = {}
    try:
        print 'Event: '
        print str(event)
        print 'Context: '
        print str(context)

        request_type = event['RequestType']
        print 'Type: ' + request_type

        stack_id = event['StackId']
        stack_name = stack_id.split('/')[1]
        print 'Stack: ' + stack_name

        logical_resource_id = event['LogicalResourceId']
        print 'LogicalResourceId: ' + logical_resource_id

        domain = event['ResourceProperties']['Domain']
        region = event['ResourceProperties']['Region']
        certificate_verification_sns_topic_arn = event['ResourceProperties']['CertificateVerificationSNSTopicArn']

        print 'Domain: ' + domain
        print 'Region: ' + region

        if certificate_verification_sns_topic_arn:
            print 'CertificateVerificationSNSTopicArn: ' + certificate_verification_sns_topic_arn

        rule_set_name = (stack_name + '-admin-email')[0:62] # fixes problem rule set name is too long
        rule_name = (stack_name + '-admin-email-rule')[0:62]  # fixes problem rule name is too long

        print 'RuleSetName: ' + rule_set_name

        ses = boto3.client('ses', region_name=region)

        if request_type in ['Create', 'Update']:
            start = datetime.now()
            status = 'Failed'
            while (datetime.now() - start).total_seconds() < 240:
                result = ses.get_identity_verification_attributes(Identities=[domain])['VerificationAttributes']
                if domain in result:
                    status = result[domain]['VerificationStatus']
                    print 'Status: ' + status
                    if status == 'Success':
                        break
                    time.sleep(5)

            if status != 'Success':
                raise Exception('Verification took to long. Aborting...')

            if request_type == 'Create':
                result = ses.describe_active_receipt_rule_set()
                rule_exists = False
                rule_names = []
                email_address = 'admin@' + domain

                if 'Metadata' in result and 'Name' in result['Metadata']:
                    rule_set_name = result['Metadata']['Name']
                    rule_names = map(lambda rule: rule['Name'], result['Rules'])
                    rule_exists = rule_name in rule_names
                else:
                    ses.create_receipt_rule_set(RuleSetName=rule_set_name)

                if not rule_exists:
                    ses.create_receipt_rule(RuleSetName=rule_set_name, Rule={
                        'Name': rule_name,
                        'Enabled': True,
                        'TlsPolicy': 'Require',
                        'Recipients': [email_address],
                        'Actions': [
                            {
                                'AddHeaderAction': {
                                    'HeaderName': 'StackName',
                                    'HeaderValue': stack_name
                                }
                            },
                            {
                                'AddHeaderAction': {
                                    'HeaderName': 'Domain',
                                    'HeaderValue': domain
                                }
                            },
                            {
                                'SNSAction': {
                                    'TopicArn': certificate_verification_sns_topic_arn,
                                }
                            }
                        ],
                        'ScanEnabled': True
                    })

                    rule_names.insert(0, rule_name)
                    ses.reorder_receipt_rule_set(RuleSetName=rule_set_name, RuleNames=rule_names)

                response_data['EmailAddress'] = email_address
                response_data['Domain'] = domain

        elif request_type == 'Delete':
            result = ses.describe_active_receipt_rule_set()
            if 'Metadata' in result and 'Name' in result['Metadata']:
                print 'Active rule set exists'
                rule_set_name = result['Metadata']['Name']
                rule_names = map(lambda rule: rule['Name'], result['Rules'])
                rule_exists = rule_name in rule_names
                if rule_exists:
                    print 'Rule ' + rule_name + ' exists. Deleting it...'
                    ses.delete_receipt_rule(RuleSetName=rule_set_name, RuleName=rule_name)

                if rule_set_name == (stack_name + '-admin-email')[0:62]:
                    print 'RuleSet was created by stack. Deleting it...'
                    ses.delete_receipt_rule_set(RuleSetName=rule_set_name)


        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    except Exception as e:
        print 'Exception occured: ' + str(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        raise e

