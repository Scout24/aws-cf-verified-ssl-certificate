#!/usr/bin/env bash

set -x -e

python test/python/process_cert_manager_test.py



S3_URL=${1:-s3://is24-infrastructure-public/cloudformation/verified-ssl-certificate}
TMP_ZIP=$TMPDIR/lambda_functions.zip

cd lambda/

# if tmp file exists, delete it
if [ -e $TMP_ZIP ]; then rm $TMP_ZIP; fi

# create zip
pip install requests
zip -v -r $TMP_ZIP .

# get current git commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# upload zip file
aws s3 cp $TMP_ZIP $S3_URL/
aws s3 cp $TMP_ZIP $S3_URL/$COMMIT_HASH/

# upload template file
aws s3 cp ../ssl-certificate.template.yaml $S3_URL/
aws s3 cp ../ssl-certificate.template.yaml $S3_URL/$COMMIT_HASH/

