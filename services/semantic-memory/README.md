# Semantic Memory Service

Semantic Memory service allows to index/store and query your data using natural language.

The solution is divided in two main areas: **Encoding** and **Retrieval**.

# Encoding

The encoding phase allows to ingest data and index it, using Embeddings and LLMs.

Documents are encoded using one or more "data pipelines" where consecutive
"handlers" take the input and process it, turning raw data into memories.

Pipelines can be customized, and they typically consist of:

* **storage**: store a copy of the document (if necessary, copies can be deleted
  after processing).
* text **extraction**: extract text from documents, presentations, etc.
* text **partitioning**: chunk the text in small blocks.
* text **indexing**: calculate embedding for each text block, store the embedding
  with a reference to the original document.

## Runtime mode

Encoding can run **in process**, e.g. running all the handlers synchronously,
in real time, as soon as some content is loaded/uploaded.
In this case the upload process and handlers must be written in the same
language, e.g. C#.

Encoding can also run **as a distributed service**, deployed locally or in
the cloud. This mode provides some important benefits:

* **Handlers can be written in different languages**, e.g. extract
  data using Python libraries, index using C#, etc. This can be useful when
  working with file types supported better by specific libraries available
  only in some programming language like Python.
* Content ingestion can be started using a **web service**. The repository
  contains a web service ready to use in C# and Python (work in progress).
  The web service can also be used by Copilot Chat, to store data and
  search for answers.
* Content processing runs **asynchronously** in the background, allowing
  to process several files in parallel, with support for retry logic.

# Retrieval

Memories can be retrieved using natural language queries. The service
supports also RAG, generating answers using prompts, relevant memories,
and plugins.

Similar to the encoding process, retrieval is available as a library and
as a web service.

# Folder structure

* `handlers-dotnet`: set of reusable .NET handlers for typical data pipelines.
  You can use these in production, or use them as a starting point for your
  custom business logic.
* `handlers-python`: set of reusable Python handlers for typical data pipelines.
  You can use these in production, or use them as a starting point for your
  custom business logic.
* `webservice-dotnet`: C# web service to upload documents and search memories.
* `webservice-python`: Python web service to upload documents and search memories.
* `lib-dotnet`: reusable libraries for C# webservices and handlers.
* `lib-python`: reusable libraries for python webservices and handlers.
* `tools`: command line tools, e.g. scripts to start RabbitMQ locally.
* `samples`: samples showing how to upload files, how to use encoder/retrieval, etc.
  * `upload-one-file.sh`: Bash command line tool to upload one document to the
    memory web service.
  * `FileImportExamples`: C# examples showing how to upload multiple files to the
    memory web service, using different approaches: 
    * **in process**, synchronously, without asynchronous distributed queues
    * **multipart form** upload to web service
    * **Semantic Memory client** (work in progress)
  * `CustomHandlerSample`: C# example of a console app running a custom pipeline handler.
  * `TextExtractionFromDocsExamples`: simple C# console app to test text
    extraction from PDF and MSWord files.

