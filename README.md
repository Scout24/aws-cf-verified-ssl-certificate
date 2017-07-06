# Get verified SSL certificate via CloudFormation

Right now, it's hard to automcatically retrieve a verified SSL/TLS certificate from AWS Certificate Manager via CloudFormation, 
because you need to have at least a admin email address on one of your super domains. The solution provided here automates
this process by managing the CloudFormation-unfriendly SES related stuff.


## Overview of moving parts

- SES for Identity Management: 
  - A lambda function (calling `ses_domain_identity.py`) creates the subdomain (parameter `domain`) in an existing super-domain (parameter `hostedZoneName)
  - lambda function is returning the verification token for TXT record 
- SNS Topic for receiving approval emails
  - lambda function (`ses_wait_for_verification_and_create_rule_set`) is used to create a SES rule set to forward the certificate approval email to SNS
  - lambda function (`process_cert_manager_mail`) is triggered by SNS events and verifies the certification request by parsing the email to get the approval link and finally "clicking on it" via http post request
  

## Use the template as a nested stack

See [AWS::CloudFormation::Stack](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html)
documentation.

To retrieve a SSL certificate for ```subdomain.mydomain.com``` you have to have a 
[Route53 Hosted Zone](http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingHostedZone.html) for a
super domain (e.g. ```mydomain.com```) which is needed to create DNS records for your domain.

Then you can use the following YAML snippet to retrieve the verified SSL certificate:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  SSLCertificate:
    Type: "AWS::CloudFormation::Stack"
    Properties:
      Parameters:
        domain: subdomain.mydomain.com
        hostedZoneName: mydomain.com.    # your hosted domain
      TemplateURL: "https://s3-eu-west-1.amazonaws.com/is24-infrastructure-public/cloudformation/verified-ssl-certificate/ssl-certificate.template.yaml"
```

Output parameters are:

| Parameter Name | Description |
| -------------- | ----------- |
| Arn | ARN of the verified SSL certificate |
| sslCertificateArn | ARN of the verified SSL certificate |

To reference the SSL certificate you can use the following snippet:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  LoadBalancerListenerHttps:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 443
      Protocol: HTTPS
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      Certificates:
        - CertificateArn: !GetAtt SSLCertificate.Outputs.Arn
```

## Deploying the certificate stack
Deploy the example stack like this
```bash
aws cloudformation create-stack \
  --stack-name my-ssl-stack \
  --template-body file://$(pwd)/ssl-certificate.template.yaml \
  --parameters \
      ParameterKey=domain,ParameterValue=my-domain.example.com \
      ParameterKey=hostedZoneName,ParameterValue=example.com. \
  --capabilities CAPABILITY_IAM
```

Changes to this repo are automatically deployed via [teamcity](https://teamcity.rz.is/viewType.html?buildTypeId=Infrastructure_Aws_AwsCfVerifiedSslCertificateDeployment)
 after push.



## Download URLs

We provide the templates ready for you:

### Latest version:
- Template: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/ssl-certificate.template.yaml```
- Lambda Code: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/labda_functions.zip```

### Specific version of commit ```<commit-hash>```:
- Template: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/<commit-hash>/ssl-certificate.template.yaml```
- Lambda Code: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/<commit-hash>/labda_functions.zip```






