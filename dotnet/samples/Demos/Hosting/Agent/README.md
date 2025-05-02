# Agent Hosting

This folder contains a set of Aspire projects that demonstrate how to host a chat completion agent on Azure as a containerized service.

## Provision and Deploy
The following steps will guide you through provisioning, deploying, and cleaning up the resources required for the agent resources on Azure. All the steps below are described in detail here: [Deploy a .NET Aspire project to Azure Container Apps using the Azure Developer CLI (in-depth guide)
](https://learn.microsoft.com/en-us/dotnet/aspire/deployment/azure/aca-deployment-azd-in-depth?tabs=windows).

### Initialize the Project  

1. Open a terminal and navigate to the `Hosting\Agent` directory.
2. Initialize the project by running the `azd init` command. **azd** will inspect the directory structure and determine the type of the app.
3. Select the `Use code in the current directory` option when **azd** prompts you with two app initialization options.
4. Select the `Confirm and continue initializing my app` option to confirm that **azd** found the correct `ChatWithAgent.AppHost` project.
5. Enter an environment name which is used to name provisioned resources.

**azd** generates a number of files and places them into the working directory. These files are:
- `azure.yaml`: Describes the services of the app, such as the `ChatWithAgent.AppHost` project, and maps them to Azure resources.
- `.azure/config.json`: Configuration file that informs **azd** what the current active environment is.
- `.azure/{env-name}/.env`: Contains environment-specific overrides.

### Deploy the project

1. Authenticate with Azure by running the `az login` command.
2. Provision all required resources and deploy the app to Azure by running the `azd up` command.
3. Select the subscription and location of the resources where the app will be deployed when prompted.
4. Copy the app endpoint URL from the output of the `azd up` command and paste it into a browser to see the app dashboard.
5. Click on the web frontend app link on the dashboard to navigate to the app and select the `Chat` tab to start chatting with the agent.

### Clean up the resources

1. To clean up the resources, run the `azd down` command. This command will delete all the resources provisioned for the app.

## Billing

Visit the *Cost Management + Billing* page in Azure Portal to track current spend. For more information about how you're billed, and how you can monitor the costs incurred in your Azure subscriptions, visit [billing overview](https://learn.microsoft.com/azure/developer/intro/azure-developer-billing).

## Troubleshooting

Q: I visited the service endpoint listed, and I'm seeing a blank page, a generic welcome page, or an error page.

A: Your service may have failed to start, or it may be missing some configuration settings. To investigate further:

1. Run `azd show`. Click on the link under "View in Azure Portal" to open the resource group in Azure Portal.
2. Navigate to the specific Container App service that is failing to deploy.
3. Click on the failing revision under "Revisions with Issues".
4. Review "Status details" for more information about the type of failure.
5. Observe the log outputs from Console log stream and System log stream to identify any errors.
6. If logs are written to disk, use *Console* in the navigation to connect to a shell within the running container.

For more troubleshooting information, visit [Container Apps troubleshooting](https://learn.microsoft.com/azure/container-apps/troubleshooting). 

### Additional information

For additional information about setting up your `azd` project, visit our official [docs](https://learn.microsoft.com/azure/developer/azure-developer-cli/make-azd-compatible?pivots=azd-convert).