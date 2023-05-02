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
