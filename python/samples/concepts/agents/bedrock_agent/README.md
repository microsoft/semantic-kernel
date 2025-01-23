# Concept samples on how to use AWS Bedrock agents


### How to add the `bedrock:InvokeModelWithResponseStream` action to an IAM policy

1. Open the [IAM console](https://console.aws.amazon.com/iam/).
2. On the left navigation pane, choose `Roles` under `Access management`.
3. Find the role you want to edit and click on it.
4. Under the `Permissions policies` tab, click on the policy you want to edit.
5. Under the `Permissions defined in this policy` section, click on the service. You should see **Bedrock** if you already have access to the Bedrock agent service.
6. Click on the service, and then click `Edit`.
7. On the right, you will be able to add an action. Find the service and search for `InvokeModelWithResponseStream`.
8. Check the box next to the action and then sroll all the way down and click `Next`.
9. Follow the prompts to save the changes.