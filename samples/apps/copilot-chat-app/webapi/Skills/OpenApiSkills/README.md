# OpenAPI Skills

## GitHubSkill
The OpenAPI spec at `./GitHubSkill/openapi.json` defines the APIs for GitHub operations 
[List Pull Requests](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests) and 
[Get Pull Request](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request). 
This description is extracted from GitHub's official OpenAPI descriptions for their REST APIs, which can be found in 
[this repository](https://github.com/github/rest-api-description/blob/main/descriptions/ghec/ghec.2022-11-28.json).

## KlarnaSkill
The OpenAPI spec at `./KlarnaSkill/openapi.json` defines the APIs for Klarna Shopping's ChatGPT AI plugin operations.
This definition was retrieved using Klarna's official ChatGPT plugin hosted at https://www.klarna.com/.well-known/ai-plugin.json.
Serving the OpenAPI definition from the repo is a workaround for Klarna's ChatGPT plugin sometimes returning a 403 when requested from CopilotChat. 

## JiraSkill
The Power Platform Connector/OpenAPI spec at `./JiraSkill/openapi.json` defines the APIs for Jira's operations.
This definition was retrieved using the Jira Power Platform Certified Connector OpenAPI definition, version 2.0 (not version 3.0), hosted at https://github.com/microsoft/PowerPlatformConnectors/blob/dev/certified-connectors/JIRA/apiDefinition.swagger.json .
Serving the OpenAPI definition from the repo is a workaround to use version 2.0 for the swagger document which is the version currently supported by the semantic kernel. 
This version however doesn't follow OpenAPI specification for all of its operations. 
For example CreateIssueV2, its body param does not describe properties and so we can't build the body automatically.
Version 3.0 of jira's swagger document is hosted at https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json.

# Model Classes

OpenApi skills return responses as json structures, these responses can vary based on the functions that are eventually invoked. Some responses are very big and go over the token limit of the underlying language model. To work around the token limit we can specifically prune the json response before passing that information back to the language model.
The Model classes under `.\webapi\Skills\OpenApiSkills\<SkillName>\Model\` determine which json properties are picked for deserializing the json response; Only the json properties defined via the Model classes remain in the trimmed response passed back to the language model.