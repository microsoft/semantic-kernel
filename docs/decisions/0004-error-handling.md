---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-06-23
deciders: shawncal
consulted: stephentoub
informed:
---
# Error handling improvements

## Disclaimer
This ADR describes problems and their solutions for improving the error handling aspect of SK. It does not address logging, resiliency, or observability aspects.

## Context and Problem Statement

Currently, there are several aspects of error handling in SK that can be enhanced to simplify SK code and SK client code, while also ensuring consistency and maintainability:

- **Exception propagation**. SK has a few public methods, like Kernel.RunAsync and SKFunction.InvokeAsync, that handle exceptions in a non-standard way. Instead of throwing exceptions, they catch and store them within the SKContext. This deviates from the standard error handling approach in .NET, which expects a method to either execute successfully if its contract is fulfilled or throw an exception if the contract is violated. Consequently, when working with the .NET version of the SK SDK, it becomes challenging to determine whether a method executed successfully or failed without analyzing specific properties of the SKContext instance. This can lead to a frustrating experience for developers using the .NET SK SDK.

- **Improper exception usage**. Some SK components use custom SK exceptions instead of standard .NET exceptions to indicate invalid arguments, configuration issues, and so on. This deviates from the standard approach for error handling in .NET and may frustrate SK client code developers.

- **Exception hierarchy inconsistency**. Half of the custom SK exceptions are derived from SKException, while the other half are directly derived from Exception. This inconsistency in the exception hierarchy does not contribute to a cohesive exception model.

- **Missing original exception details**. Certain SK exceptions do not preserve the original failure or exception details and do not expose them through their properties. This omission prevents SK client code from understanding the problem and handling it properly.

- **No consolidated way for exception handling**. In some cases, SK has an exception type per component implementation, making it impossible for SK client code to handle them in a consolidated manner. Instead of having a single catch block, SK client code needs to include a catch block for each component implementation. Moreover, SK client code needs to be updated every time a new component implementation is added or removed.

## Solution

To address the identified issues, the following steps can be taken:

- **Exception propagation**: To enable SK exceptions to propagate to SK client code, all SK components that currently do not do so should be modified to rethrow the exception instead of suppressing it. This allows SK client code to use try/catch blocks for handling and catching exceptions.

- **Improper exception usage**: Modify SK code to throw .NET standard exceptions, such as ArgumentOutOfRangeException or ArgumentNullException, when class argument values are not provided or are invalid, instead of throwing custom SK exceptions. Analyze SK exception usage to identify other potential areas where standard .NET exceptions can be used instead.

- **Exception hierarchy inconsistency**: Refactor SK custom exceptions that are not derived from SKException to derive from SKException. This ensures consistency in the SK exception hierarchy.

- **Missing original exception details**: Identify all cases where the original exception or failure is not preserved either as an inner exception or as a property/message of the rethrown exception, and address them. For example, AI service connectors that use HttpClient should preserve the original status code by either setting it as an inner exception or including it as part of the rethrown exception's property.

- **No consolidated way for exception handling**:
  - [Memory connectors]: Introduce a new exception called VectorDbStorageException, along with derived exceptions like UpsertRecordException and RemoveRecordException, if additional details need to be captured and propagated to SK client code. Refactor all SK memory component implementations to use these exceptions instead of implementation-specific memory storage exceptions.
  - [AI service connectors]: Restrict the usage of AIException to AI service connectors only and replace its usage in other SK components with more relevant exceptions. For cases where AIException is thrown, use HttpOperationException describved below as an inner exception to allow SK client code to access the original status code and exception/error details, if necessary.
  - [HttpOperationException]: Create a new exception called HttpOperationException, which includes a StatusCode property, and implement the necessary logic to map the exception from HttpStatusCode, HttpRequestException, or Azure.RequestFailedException. Update existing SK code that interacts with the HTTP stack to throw HttpOperationException in case of a failed HTTP request and assign the original exception as its inner exception.

- **Other**:
  - Remove any code that wraps unhandled exceptions into AIException or any other SK exception solely for the purpose of wrapping. In most cases, this code does not provide useful information to help SK client code handle the exception, apart from a generic and uninformative "Something went wrong" message. Regardless of whether the unhandled exception is wrapped or not, SK client code cannot handle or recover from it without prior knowledge of the exception and proper exception handling logic.

## Questions and consideration

- Should the exception hierarchy follow the SK components hierarchy? For example, should there be a PlanningException for planners and a MemoryStorageException for memory storage connectors? What are the benefits for SK client code? Can the SK client code operate on the exception?  
  In order to handle an exception successfully, the client code needs to know as many details as possible about the failed operation, such as exception type, status code, and some other operation related properties. This suggests that specific exception types with strongly typed properties should be preferred over generic/common exception types. If that's the case, what is the purpose of having base generic exceptions?  
  On the other hand, having base exception types per component or set of related operations can be convenient from a code reusability perspective because derived types can inherit common component exception properties relevant to that component.
- Should all custom SK exceptions be derived from the SKException type?  Currently, SKException derives from the Exception type and does not add any additional information. What value can SK client code get from catching these exceptions compared to catching them as Exception types? Should SKException be used in all cases when SK needs to indicate that something went wrong without providing details through strongly typed properties, and neither custom nor standard exception types exist that could be used for that purpose?
- Should we keep the IsCriticalException functionality that SK currently has to avoid handling several system/critical exceptions such as OutOfMemoryException and StackOverflowException? Some of them cannot be intercepted.
- An idea has been proposed to add SK wide error codes to exceptions in order to identify and locate the source of the exception. The question is, is it necessary? Aren't the exception type, message, values of its properties, and stack trace enough to precisely identify the exception and locate its source?

## Decision Outcome

TBD
