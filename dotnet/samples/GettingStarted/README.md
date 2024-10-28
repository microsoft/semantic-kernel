# Starting With Semantic Kernel

This project contains a step by step guide to get started with the Semantic Kernel.

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Configuring Secrets

Most of the examples will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. We suggest using .NET
[Secret Manager](https://learn.microsoft.com/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd dotnet/samples/Concepts

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ModelId" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:EmbeddingModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

```

To set your secrets with environment variables, use these names:

```
# OpenAI
OpenAI__ModelId
OpenAI__ChatModelId
OpenAI__EmbeddingModelId
OpenAI__ApiKey
```

## Using Automatic Issue Workflows

To manage issues effectively in this repository, we have set up automatic issue workflows using GitHub Actions. These workflows help in labeling issues, closing inactive issues, and adding title prefixes based on labels.

### Issue Templates

We have defined issue templates to standardize the information provided when creating new issues. You can find the templates in the `.github/ISSUE_TEMPLATE` directory:

- [Bug Report](../../.github/ISSUE_TEMPLATE/bug_report.md)
- [Custom Issue](../../.github/ISSUE_TEMPLATE/custom.md)
- [Feature Request](../../.github/ISSUE_TEMPLATE/feature_request.md)

### Labeling Issues Automatically

We use the `.github/labeler.yml` file to define rules for automatically labeling issues based on their content or file changes. You can find the labeler configuration [here](../../.github/labeler.yml).

### Closing Inactive Issues

We have set up a workflow to automatically close inactive issues after a certain period of inactivity using the `actions/stale` action. You can find the workflow configuration [here](../../.github/workflows/close-inactive-issues.yml).

### Adding Labels Based on Issue Content

We have created a workflow to add labels to issues based on their content using the `actions/github-script` action. You can find the workflow configuration [here](../../.github/workflows/label-issues.yml).

### Adding Title Prefixes Based on Labels

We have created a workflow to add title prefixes to issues based on their labels using the `actions/github-script` action. You can find the workflow configuration [here](../../.github/workflows/label-title-prefix.yml).
