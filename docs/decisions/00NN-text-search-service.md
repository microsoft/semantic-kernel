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
- Application developers must to be able to override the semantic descriptions of the search function(s) per instance registered via settings / inputs.
- Application developers must be able to optionally define the execution settings of an embedding service with a default being provided by the Kernel.
- Application developers must be able to support custom schemas for search connectors. No fields should be required.
- Search service developers must be able to easily create a new search service that returns type `T`.
- Search service developers must be able to easily create a new search connector return type that inherits from `SearchResultContent`.
- Search service developers must be able to define the attributes of the search method (e.g., name, description, input names, input descriptions, return description).
- Application developers must be ab able to import a vector DB search connection using an ML index file.
- The design must be flexible to support future requirements and different search modalities.

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

<img src="./diagrams/text-search-service-imemorystore.png" alt="Current Memory Design" width="80%"/>

#### Web Search Engine Integration

The diagram below shows the layers in the current design of the Web Search Engine integration.

<img src="./diagrams/text-search-service-iwebsearchengineconnector.png" alt="Current Web Search Design" width="80%"/>

The Semantic Kernel currently includes experimental support for a `WebSearchEnginePlugin` which can be configured via a `IWebSearchEngineConnector` to integrate with a Web Search Services such as Bing or Google. The search results can be returned as a collection of string values or a collection of `WebPage` instances.

- The `string` values returned from the plugin represent a snippet of the search result in plain text.
- The `WebPage` instances returned from the plugin are a normalized subset of a complete search result. Each `WebPage` incudes:
  - `name` The name of the search result web page
  - `url` The url of the search result web page
  - `snippet` A snippet of the search result in plain text

The current design doesn't support break glass scenario's or using custom types for the response values.

## Considered Options

- Option 1
- {title of option 2}
- {title of option 3}
- … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
- … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

<!-- This is an optional element. Feel free to remove. -->

## Pros and Cons of the Options

### Option 1

The class diagram below shows the first option.
<img src="./diagrams/text-search-service-option-1.png" alt="Current Memory Design" width="80%"/>

- `IISearchService` is the base interface for all search services and just stores attributes for the service
- `ITextSearchService` is the interface for text based search services. This cna be invoked with a text query to return a collection of search results.
- `SearchExecutionSettings` provides execution settings for a search service. Some common settings e.g. `IndexName`, `Count`, `Offset` are defined.
- `KernelSearchResults` represents the search results returned from a `ISearchService` service. This provides access to the individual search results, underlying search result, metadata, ... This supports generics but an implementation can restrict the supported types. All implementations must support `string`, `TextSearchResult` and whatever native types the connector implementation supports. Some implementations will also support custom types.

- An AI must be able to perform searches with a search plugin and get back “results” of type `T`.
  - 1
  - 2
  - 3
- Application developers should be able to easily add a search plugin using a search connector with minimal lines of code (ideally one).
  - 1
  - 2
  - 3
- Application developers must be able to provide connector specific settings.
  - 1
  - 2
  - 3
- Application developers must be able to set required information e.g. `IndexName` for search providers.
  - 1
  - 2
  - 3
- Application developers must to be able to override the semantic descriptions of the search function(s) per instance registered via settings / inputs.
  - 1
  - 2
  - 3
- Application developers must be able to optionally define the execution settings of an embedding service with a default being provided by the Kernel.
  - 1
  - 2
  - 3
- Application developers must be able to support custom schemas for search connectors. No fields should be required.
  - 1
  - 2
  - 3
- Search service developers must be able to easily create a new search service that returns type `T`.
  - 1
  - 2
  - 3
- Search service developers must be able to easily create a new search connector return type that inherits from `SearchResultContent`.
  - 1
  - 2
  - 3
- Search service developers must be able to define the attributes of the search method (e.g., name, description, input names, input descriptions, return description).
  - 1
  - 2
  - 3
- Application developers must be ab able to import a vector DB search connection using an ML index file.
  - 1
  - 2
  - 3
- The design must be flexible to support future requirements and different search modalities.
  - 1
  - 2
  - 3

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
