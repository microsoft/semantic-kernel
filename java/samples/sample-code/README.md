# Java Samples

## TL;DR

Run with:

```shell
# AZURE:
OPENAI_CLIENT_TYPE=AZURE_OPEN_AI \
AZURE_OPEN_AI_KEY="my-key" \
AZURE_OPEN_AI_ENDPOINT="endpoint url" \
../../mvnw clean package exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode

# OPENAI:
OPENAI_CLIENT_TYPE=OPENAI \
OPEN_AI_KEY="my-key" \
OPEN_AI_ORGANIZATION_ID="organisation id" \
../../mvnw clean package exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode
```

# Compile

These samples can be compiled via:

```shell
 ../../mvnw clean package
```

They can then be run by:

```shell
../../mvnw exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode
```

# Configuration

You can define the provider of Open AI by setting the `OPENAI_CLIENT_TYPE`
property or environment variable to either [`OPENAI`](https://openai.com/api/)
or [`AZURE_OPEN_AI`](https://learn.microsoft.com/azure/cognitive-services/openai/).
By default, the samples will use the Open AI client.

```shell
OPENAI_CLIENT_TYPE=OPENAI ../../mvnw exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode

OR

 ../../mvnw exec:java -DOPENAI_CLIENT_TYPE=AZURE_OPEN_AI -Dsample=Example04_CombineLLMPromptsAndNativeCode
```

## Client Settings
The samples search for the client settings in the following order:
1. Properties file whose location is defined by the `CONF_PROPERTIES` property or environment variable.
1. System properties defined on the command line.
1. Environment variables.
1. Properties file at `java/samples/conf.properties`.
1. Properties file at `~/.sk/conf.properties`.


## Properties File

You can set the location of a properties file, by setting the `CONF_PROPERTIES` property or environment variable, ie:

```shell
CONF_PROPERTIES=my.properties \
OPENAI_CLIENT_TYPE=OPENAI \
../../mvnw exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode

OR

../../mvnw exec:java \
-DCONF_PROPERTIES=my.properties \
-DOPENAI_CLIENT_TYPE=AZURE_OPEN_AI \
-Dsample=Example04_CombineLLMPromptsAndNativeCode
```

A properties file looks as follows:

```properties
# If using openai.com
client.openai.key:"my-key"
client.openai.organizationid:"my-org-id"
# if using Azure Open AI
client.azureopenai.key:"my-key"
client.azureopenai.endpoint:"url of azure openai endpoint"
client.azureopenai.deploymentname:"deployment name"
```

## System Properties

As an alternative to providing the key/endpoint properties via a file, you can set them directly via system properties,
ie:

```shell
# OpenAI
../../mvnw exec:java \
-DOPENAI_CLIENT_TYPE=AZURE_OPEN_AI \
-Dclient.openai.key="my-key" \
-Dclient.openai.organizationid="my-org-id" \
-Dsample=Example04_CombineLLMPromptsAndNativeCode

# Azure
../../mvnw exec:java \
-DOPENAI_CLIENT_TYPE=AZURE_OPEN_AI \
-Dclient.azureopenai.key="my-key" \
-Dclient.azureopenai.endpoint="url of azure openai endpoint" \
-Dsample=Example04_CombineLLMPromptsAndNativeCode
```

## Environment variables

Alternative to properties, you can set environment variables as follows:

```shell
# AZURE:
OPENAI_CLIENT_TYPE=AZURE_OPEN_AI \
AZURE_OPEN_AI_KEY="my-key" \
AZURE_OPEN_AI_ENDPOINT="endpoint url" \
../../mvnw clean package exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode

# OPENAI:
OPENAI_CLIENT_TYPE=OPENAI \
OPEN_AI_KEY="my-key" \
OPEN_AI_ORGANIZATION_ID="organisation id" \
../../mvnw clean package exec:java -Dsample=Example04_CombineLLMPromptsAndNativeCode
```