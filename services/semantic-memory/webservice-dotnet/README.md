This folder contains SK Memory web service, used to manage memory settings,
ingest data and query for answers.

# ⚙️ Dependencies

The service depends on three main components:

* **Content storage**: this is where content like files, chats, emails are saved
  and transformed when uploaded.
* **Vector storage**: service used to persist embeddings.
* **Data ingestion orchestration**: this can run in memory and in the same
  process, e.g. when working with small files, or run as a service, in which
  case it requires a persistent queue.

# ⚙️ Configuration files and Environment variables

Configuration settings can be saved in 3 places:

1. `appsettings.json`: although it's possible, it's not recommended, to avoid
   risks of leaking secrets in source code repositories.
2. `appsettings.Development.json`: this works only when `ASPNETCORE_ENVIRONMENT`
   is set to `Development`
3. using **env vars**: preferred method for credentials. Any setting in
   appsettings.json can be overridden by env vars. The env var name correspond
   to the configuration key name, using `__` (double underscore) as a separator.

# ⚙️ Setup Content storage

Currently, content can be stored only locally in the filesystem. Soon support
for Azure Blobs, OneDrive, SharePoint and more will be added.

Choose the type of storage:

- `AzureBlob`: store files using Azure Storage blobs. Each upload is tracked
  on a dedicated container, including original files, artifacts and state.
- `FileSystem`: storing files locally, mostly for development scenarios
  or apps that run only locally. Each upload is tracked on a dedicated folder,
  including original files, artifacts and state.

To set the value, either

- set `SKMemory.ContentStorage.Type` in the config file
- or set `SKMemory__ContentStorage__Type` env var in your app/system.

## Store content in Azure Blobs

- Create an Azure storage account, set blobs to private access only.
- Copy the **connection string**.

Settings:

* `SKMemory.ContentStorage.Type`: `AzureBlobs`
* `SKMemory.ContentStorage.AzureBlobs.Auth`: `ConnectionString`
* Env var: `SKMemory__ContentStorage__AzureBlobs__ConnectionString`: `<...your account connection string...>`

## Store content locally in the file system:

* Create a directory on your drive and copy the path.

Settings:

* `SKMemory.ContentStorage.Type`: `FileSystem`
* `SKMemory.ContentStorage.FileSystem.Directory`: `...<path>...`

# ⚙️ Setup Data ingestion Orchestrator

Choose the type of data ingestion orchestration:

- `InProcess`: every file uploaded is immediately processed and saved to memory.
  Works well with small files and logic that requires only C#.
- `Distributed`: every file uploaded is queued and processed by separate processes.
  Works well with large files and allows to process the upload with multiple
  applications written in different programming languages.

To set the value, either
- set `SKMemory.Orchestration.Type` in the config file
- or set `SKMemory__Orchestration__Type` env var in your app/system.

## Queue

If you choose the `Distributed` orchestrator you will need a persistent queue,
such as Azure Queue or RabbitMQ. The system will create multiple queues, to
track the progress of individual tasks. The orchestrator uses also poison messages,
to discard tasks blocked and failing after multiple attempts.

### To use Azure Queue with a Connection String

- Create an Azure storage account.
- Copy the **connection string**.

Settings:

* `SKMemory.Orchestration.DistributedPipeline.QueueType`: `AzureQueue`
* `SKMemory.Orchestration.DistributedPipeline.AzureQueue.Auth`: `ConnectionString`
* Env var: `SKMemory__Orchestration__DistributedPipeline__AzureQueue__ConnectionString`: `<...your account connection string...>`
 
### To use Azure Queue with Azure Identity

- Create an Azure storage account, and copy the **account name**.
- Create a Service Principal and grant access to the queue.
- For local development, you can set these env vars:
  - AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET

Settings:

* `SKMemory.Orchestration.DistributedPipeline.QueueType`: `AzureQueue`
* `SKMemory.Orchestration.DistributedPipeline.AzureQueue.Auth`: `AzureIdentity`
* `SKMemory.Orchestration.DistributedPipeline.AzureQueue.Account`: `<...your account name...>`

### To use RabbitMQ locally

- Install docker and launch RabbitMQ with:

      docker run -it --rm --name rabbitmq \
         -p 5672:5672 -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password \
         rabbitmq:3

Settings:

* `SKMemory.Orchestration.DistributedPipeline.QueueType`: `RabbitMQ`
* `SKMemory.Orchestration.DistributedPipeline.RabbitMq.Host`: `127.0.0.1`
* `SKMemory.Orchestration.DistributedPipeline.RabbitMq.Port`: `5672`
* `SKMemory.Orchestration.DistributedPipeline.RabbitMq.Username`: `user`
* Env var: `SKMemory__Orchestration__DistributedPipeline__RabbitMq__Password`: `password`
