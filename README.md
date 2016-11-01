# Get verified SSL certificate via CloudFormation

Right now, it's hard to automcatically get a verified SSL/TLS certificate from AWS Certificate Manager, 
because you need have a admin email address on one of the super domains. The solution provided here automates
this process by managed the cloudformation-unfriendly SES related stuff.

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



