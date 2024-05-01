---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: markwallace
date: {YYYY-MM-DD when the decision was last updated}
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk, westey
consulted: 
informed: stephentoub, matthewbolanos
---

# Text Search Service 

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

## Decision Drivers

- An AI must be able to perform searches with a search plugin and get back “results” of type `T`.
- Application developers should be able to easily add a search plugin using a search connector with minimal lines of code (ideally one).
- Application developers must be able to provide connector specific settings.
- Application developers must be able to set required information e.g. `IndexName` for search providers.
- Application developers must be able to support custom schemas for search connectors. No fields should be required.
- Search service developers must be able to easily create a new search service that returns type `T`.
- Search service developers must be able to easily create a new search connector return type that inherits from `SearchResultContent`.
- Search service developers must be able to define the attributes of the search method (e.g., name, description, input names, input descriptions, return description).
- Application developers must be ab able to import a vector DB search connection using an ML index file.
- The design must be flexible to support future requirements and different search modalities.

- Application developers must to be able to override the semantic descriptions of the search function(s) per instance registered via settings / inputs.
- Application developers must be able to optionally define the execution settings of an embedding service with a default being provided by the Kernel.

### Future Requirements

- An AI can perform search with filters using a search plugin to get back “results” of type T. This will require a Connector Dev to implement a search interface that accepts a Filter object.
- Connector developers can decide which search filters are given to the AI by “default”.
- Application developers can override which filters the AI can use via search settings.
- Application developers can set the filters when they create the connection.

### Current Design

The current design for search is divided into two implementations:

1. Search using a Memory Store i.e. Vector Database
1. Search using a Web Search Engine

In each case a plugin implementation is provided which allows the search to be integrated into prompts e.g. to provide additional context or to be called from a planner or using auto function calling with a LLM.

#### Memory Store Search

The diagram below shows the layers in the current design of the Memory Store search functionality.

<img src="./diagrams/text-search-service-imemorystore.png" alt="Current Memory Design" width="40%"/>

#### Web Search Engine Integration

The diagram below shows the layers in the current design of the Web Search Engine integration.

<img src="./diagrams/text-search-service-iwebsearchengineconnector.png" alt="Current Web Search Design" width="40%"/>

The Semantic Kernel currently includes experimental support for a `WebSearchEnginePlugin` which can be configured via a `IWebSearchEngineConnector` to integrate with a Web Search Services such as Bing or Google. The search results can be returned as a collection of string values or a collection of `WebPage` instances.

- The `string` values returned from the plugin represent a snippet of the search result in plain text.
- The `WebPage` instances returned from the plugin are a normalized subset of a complete search result. Each `WebPage` incudes:
  - `name` The name of the search result web page
  - `url` The url of the search result web page
  - `snippet` A snippet of the search result in plain text

The current design doesn't support break glass scenario's or using custom types for the response values.

## Considered Options

- Define `ITextSearchService` abstraction specifically for text search
- {title of option 2}
- {title of option 3}
- … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

## Pros and Cons of the Options

### Define `ITextSearchService` Abstraction

A new `ITextSearchService` abstraction is used to define the contract to perform a text based search.
`ITextSearchService` uses generics are each implementation is required to support returning search values as:

- `string` values, this will typically be the snippet or chunk associated with the search result.
- instances of `TextSearchResult`, this is a normalized result that has name, value and link properties.
- instances of the implementation specific result types e.g. Azure AI Search uses `SearchDocument` to represent search results.
- optionally instances of a specific type, although there may be limitations to this approach or or it may not be supported at all.

The class diagram below shows the class hierarchy.

<img src="./diagrams/text-search-service-abstraction.png" alt="ITextSearchService Abstraction" width="80%"/>

The abstraction contains the following interfaces and classes:

- `ITextSearchService` is the interface for text based search services. This cna be invoked with a text query to return a collection of search results.
- `SearchExecutionSettings` provides execution settings for a search service. Some common settings e.g. `IndexName`, `Count`, `Offset` are defined.
- `KernelSearchResults` represents the search results returned from a `ISearchService` service. This provides access to the individual search results, underlying search result, metadata, ... This supports generics but an implementation can restrict the supported types. All implementations must support `string`, `TextSearchResult` and whatever native types the connector implementation supports. Some implementations will also support custom types.
- `TextSearchResult` represents a normalized text search result. All implementations must be able to return results using this type.

#### Return Results of Type `T`


```csharp
var searchService = new AzureAITextSearchService(
    endpoint: TestConfiguration.AzureAISearch.Endpoint,
    adminKey: TestConfiguration.AzureAISearch.ApiKey);

AzureAISearchExecutionSettings settings = new() { Index = IndexName, Count = 2, Offset = 2, ValueField = "chunk" };
KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>("What is the Semantic Kernel?", settings);
await foreach (string result in summaryResults.Results)
{
    Console.WriteLine(result);
}
```

```csharp
var searchService = new BingTextSearchService(
    endpoint: TestConfiguration.Bing.Endpoint,
    apiKey: TestConfiguration.Bing.ApiKey);

KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>("What is the Semantic Kernel?", new() { Count = 2, Offset = 2 });
await foreach (string result in summaryResults.Results)
{
    Console.WriteLine(result);
}
```

```csharp
AzureAISearchExecutionSettings settings = new() { Index = IndexName, Count = 2, Offset = 2, NameField = "title", ValueField = "chunk", LinkField = "metadata_spo_item_weburi" };
KernelSearchResults<TextSearchResult> textResults = await searchService.SearchAsync<TextSearchResult>("What is the Semantic Kernel?", settings);
await foreach (TextSearchResult result in textResults.Results)
{
    Console.WriteLine(result.Name);
    Console.WriteLine(result.Value);
    Console.WriteLine(result.Link);
}
```

```csharp
var searchService = new BingTextSearchService(
    endpoint: TestConfiguration.Bing.Endpoint,
    apiKey: TestConfiguration.Bing.ApiKey);

KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>("What is the Semantic Kernel?", new() { Count = 2 });
await foreach (CustomSearchResult result in searchResults.Results)
{
    Console.WriteLine(result.Name);
    Console.WriteLine(result.Snippet);
    Console.WriteLine(result.Url);
}
```

```csharp
KernelSearchResults<SearchDocument> fullResults = await searchService.SearchAsync<SearchDocument>("What is the Semantic Kernel?", new() { Index = IndexName, Count = 2, Offset = 6 });
await foreach (SearchDocument result in fullResults.Results)
{
    Console.WriteLine(result.GetString("title"));
    Console.WriteLine(result.GetString("chunk_id"));
    Console.WriteLine(result.GetString("chunk"));
}
```


#### Perform Search using Plugin

```csharp
var searchService = new BingTextSearchService(
    endpoint: TestConfiguration.Bing.Endpoint,
    apiKey: TestConfiguration.Bing.ApiKey);

Kernel kernel = new();
var searchPlugin = new TextSearchPlugin(searchService);
kernel.ImportPluginFromObject(searchPlugin, "TextSearch");

var function = kernel.Plugins["TextSearch"]["Search"];
var result = await kernel.InvokeAsync(function, new() { ["query"] = "What is the Semantic Kernel?" });
```


#### Support ML Index File Format


Evaluation

- Good, because {argument a}
- Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
- Neutral, because {argument c}
- Bad, because {argument d}
- … <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | …}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- …

<!-- This is an optional element. Feel free to remove. -->

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
