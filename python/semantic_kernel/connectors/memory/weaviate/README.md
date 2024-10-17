# Weaviate Memory Connector

[Weaviate](https://weaviate.io/developers/weaviate) is an open source vector database. Semantic Kernel provides a connector to allow you to store and retrieve information for you AI applications from a Weaviate database.

## Setup

There are a few ways you can deploy your Weaviate database:
- [Weaviate Cloud](https://weaviate.io/developers/weaviate/installation/weaviate-cloud-services)
- [Docker](https://weaviate.io/developers/weaviate/installation/docker-compose)
- [Embedded](https://weaviate.io/developers/weaviate/installation/embedded)
- Other cloud providers such as [Azure](https://azuremarketplace.microsoft.com/en-us/marketplace/apps/weaviatebv1686614539420.weaviate_1?tab=Overview), [AWS](https://weaviate.io/developers/weaviate/installation/aws-marketplace) or [GCP](https://weaviate.io/developers/weaviate/installation/gc-marketplace).

> Note that embedded mode is not supported on Windows yet: [GitHub issue](https://github.com/weaviate/weaviate/issues/3315) and it's still an experimental feature on Linux and MacOS.

## Using the Connector

Once the Weaviate database is up and running, and the environment variables are set, you can use the connector in your Semantic Kernel application. Please refer to this sample to see how to use the connector: [Weaviate Connector Sample](../../../../samples/concepts/memory/new_memory.py)