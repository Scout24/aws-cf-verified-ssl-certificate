# Get verified SSL certificate via CloudFormation

Right now, it's hard to automcatically get a verified SSL/TLS certificate from AWS Certificate Manager in a CloudFormation stack, 
because you need have a admin email address on one of the super domains. The solution provided here automates
this process by managing the CloudFormation-unfriendly SES related stuff.

## Use the template as a nested stack

See [AWS::CloudFormation::Stack](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html)
documentation.

To retrieve a SSL certificate for ```subdomain.mydomain.com``` you have to have a 
[Route53 Hosted Zone](http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingHostedZone.html) for a
super domain (e.g. ```mydomain.com```) which is needed to create DNS records for your domain.

Then you can use the following YAML snippet to retrieve the verified SSL certificate:

```yaml
Type: "AWS::CloudFormation::Stack"
Properties:
  Parameters:
    domain: subdomain.mydomain.com
    hostedZoneName: mydomain.com    # your hosted domain
  TemplateURL: "s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/ssl-certificate.template.yaml"
```

Output parameters are:
|Parameter Name|Description|
|--------------|-----------|
|sslCertificateArn|ARN of the verified SSL certificate|

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

## Download URLs

We provide the templates ready for you:

### Latest version:
- Template: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/ssl-certificate.template.yaml```
- Lambda Code: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/labda_functions.zip```
### Specific version for commit ```<commit-hash```:
- Template: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/<commit-hash>/ssl-certificate.template.yaml```
- Lambda Code: ```s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate/<commit-hash>/labda_functions.zip```






