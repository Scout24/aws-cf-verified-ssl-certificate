import boto3
import cfnresponse
import time
import traceback

from datetime import datetime


class DomainVerifierAndRuleSetCreator:

    def __init__(self, event, context):
        self.event = event
        self.context = context

        print('Event: ')
        print(str(self.event))
        print('Context: ')
        print(str(self.context))

        try:
            self.request_type = self.event['RequestType']
            print('Type: ' + self.request_type)

            self.stack_id = self.event['StackId']
            self.stack_name = self.stack_id.split('/')[1]
            print('Stack: ' + self.stack_name)

            self.logical_resource_id = self.event['LogicalResourceId']
            print('LogicalResourceId: ' + self.logical_resource_id)

            self.domain = self.event['ResourceProperties']['Domain']
            self.region = self.event['ResourceProperties']['Region']
            self.certificate_verification_sns_topic_arn = self.event['ResourceProperties'][
                'CertificateVerificationSNSTopicArn']

            print('Domain: ' + self.domain)
            print('Region: ' + self.region)

            if self.certificate_verification_sns_topic_arn:
                print('CertificateVerificationSNSTopicArn: ' + self.certificate_verification_sns_topic_arn)

            self.rule_set_name = self.create_valid_name(self.stack_name + '-admin-email')
            self.rule_name = self.create_valid_name(self.stack_name + '-admin-email-rule')

            print('RuleSetName: ' + self.rule_set_name)

            self.ses = boto3.client('ses', region_name=self.region)
        except Exception as e:
            print('Exception occured: ' + str(e))
            cfnresponse.send(self.event, self.context, cfnresponse.FAILED, {})
            raise e

    def execute(self):
        response_data = {}
        try:
            if self.request_type in ['Create', 'Update']:
                self.wait_for_ses_domain_verification()

                email_address = 'admin@' + self.domain
                response_data['EmailAddress'] = email_address
                response_data['Domain'] = self.domain

                if self.request_type == 'Create':
                    result = self.ses.describe_active_receipt_rule_set()
                    rule_exists = False
                    rule_names = []

                    if 'Metadata' in result and 'Name' in result['Metadata']:
                        self.rule_set_name = result['Metadata']['Name']
                        rule_names = list(map(lambda rule: rule['Name'], result['Rules']))
                        rule_exists = self.rule_name in rule_names
                    else:
                        self.ses.create_receipt_rule_set(RuleSetName=self.rule_set_name)
                        self.ses.set_active_receipt_rule_set(RuleSetName=self.rule_set_name)

                    if not rule_exists:
                        self.create_rule(email_address, rule_names)

            elif self.request_type == 'Delete':
                result = self.ses.describe_active_receipt_rule_set()
                if 'Metadata' in result and 'Name' in result['Metadata']:
                    print('Active rule set exists')
                    active_rule_set_name = result['Metadata']['Name']
                    rule_names = list(map(lambda rule: rule['Name'], result['Rules']))
                    rule_exists = self.rule_name in rule_names
                    if rule_exists:
                        print('Rule ' + self.rule_name + ' exists. Deleting it...')
                        self.ses.delete_receipt_rule(RuleSetName=active_rule_set_name, RuleName=self.rule_name)

                    if active_rule_set_name == self.rule_set_name:
                        print('RuleSet was created by stack. Deleting it...')
                        self.ses.set_active_receipt_rule_set()
                        self.ses.delete_receipt_rule_set(RuleSetName=active_rule_set_name)

            cfnresponse.send(self.event, self.context, cfnresponse.SUCCESS, response_data)
        except Exception as e:
            traceback.print_exc()
            cfnresponse.send(self.event, self.context, cfnresponse.FAILED, response_data)
            raise e

    def create_rule(self, email_address, rule_names):
        self.ses.create_receipt_rule(RuleSetName=self.rule_set_name, Rule={
            'Name': self.rule_name,
            'Enabled': True,
            'TlsPolicy': 'Require',
            'Recipients': [email_address],
            'Actions': [
                {
                    'AddHeaderAction': {
                        'HeaderName': 'StackName',
                        'HeaderValue': self.stack_name
                    }
                },
                {
                    'AddHeaderAction': {
                        'HeaderName': 'Domain',
                        'HeaderValue': self.domain
                    }
                },
                {
                    'SNSAction': {
                        'TopicArn': self.certificate_verification_sns_topic_arn,
                    }
                }
            ],
            'ScanEnabled': True
        })
        rule_names.insert(0, self.rule_name)
        self.ses.reorder_receipt_rule_set(RuleSetName=self.rule_set_name, RuleNames=rule_names)

    def wait_for_ses_domain_verification(self):
        start = datetime.now()
        status = 'Failed'
        while (datetime.now() - start).total_seconds() < 240:
            result = self.ses.get_identity_verification_attributes(Identities=[self.domain])['VerificationAttributes']
            if self.domain in result:
                status = result[self.domain]['VerificationStatus']
                print('Status: ' + status)
                if status == 'Success':
                    break
                time.sleep(5)
        if status != 'Success':
            raise Exception('Verification took to long. Aborting...')

    @staticmethod
    def create_valid_name(name):
        # fixes problem rule set name is too long
        valid_name = name[0:62]

        # fixed problem with dashes as last character
        while not valid_name[-1].isalnum():
            valid_name = valid_name[0:-1]

        return valid_name


def lambda_handler(event, context):
    handler = DomainVerifierAndRuleSetCreator(event, context)
    handler.execute()
