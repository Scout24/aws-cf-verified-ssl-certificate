import unittest
import sys
import json
sys.path.append("../../lambda/")

from  process_cert_manager_mail  import *

class TestProcessCertManager(unittest.TestCase):

    txt_input = open("../resources/sns_verification_message.txt", "r").read()
    email_parsed = json.loads(txt_input)
    email_message = email_parsed['content']

    def test_is_verification_url(self):
        approval_url = "https://us-west-1.certificates.amazon.com/approvals?code=11e23c40-7a2b-4754-a97c-1607e8e78a6c&context=111a222c-6e1d-4333-bbc4-40b961461df5-65752d776573742d31"
        self.assertEqual ( approval_url, get_verification_url(self.email_message), "function should find approval email in email content.")


if __name__ == "__main__":
    unittest.main()