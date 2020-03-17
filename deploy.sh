#!/usr/bin/env bash

set -x -e

python test/python/process_cert_manager_test.py


S3_BUCKET=${1:-is24-infrastructure-public}
CREATE_INFRASTRUCTURE=${2:-true}
S3_URL=s3://${S3_BUCKET}/cloudformation/verified-ssl-certificate
TMP_ZIP=lambda_functions.zip

cd lambda/

# if tmp file exists, delete it
if [ -e "$TMP_ZIP" ]; then rm "$TMP_ZIP"; fi

# create zip
pip install -t . requests
zip -v -r "$TMP_ZIP" .

# get current git commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# upload zip file
aws s3 cp $TMP_ZIP $S3_URL/
aws s3 cp $TMP_ZIP $S3_URL/"$COMMIT_HASH"/

# upload template file
aws s3 cp ../ssl-certificate.template.yaml "$S3_URL"/
aws s3 cp ../ssl-certificate.template.yaml "$S3_URL"/"$COMMIT_HASH"/


if [ "${CREATE_INFRASTRUCTURE}" == "true" ]
then
  aws cloudformation deploy --template global-hosting.template.yaml --parameter-overrides S3BucketName="${S3_BUCKET}" \
    --tags segment=infrastructure usecase=cf-verified-ssl-certificate \
    --stack-name global-cf-verified-ssl-certificate-hosting
fi
