import boto3
import cfnresponse

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

        domain = event['ResourceProperties']['Domain']
        print 'Domain: ' + domain
        response_data['Domain'] = domain

        region = event['ResourceProperties']['Region']
        print 'Region: ' + region

        ses = boto3.client('ses', region_name=region)

        if request_type == 'Create':

            domain_identity = ses.verify_domain_identity(Domain=domain)
            response_data['VerificationToken'] = domain_identity['VerificationToken']

        elif request_type == 'Update':

            oldDomain = event['OldResourceProperties']['Domain']
            if oldDomain != domain:
                try:
                    ses.delete_identity(Identity=oldDomain)
                except Exception as e:
                    print e

            domain_identity = ses.verify_domain_identity(Domain=domain)
            response_data['VerificationToken'] = domain_identity['VerificationToken']

        elif request_type == 'Delete':
            ses.delete_identity(Identity=domain)

        print response_data

        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    except Exception as e:
        print 'Exception occured: ' + str(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        raise e
