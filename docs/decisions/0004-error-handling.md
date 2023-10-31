---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: semenshi
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

- **Exception hierarchy**. Half of the custom SK exceptions are derived from SKException, while the other half are directly derived from Exception. This inconsistency in the exception hierarchy does not contribute to a cohesive exception model.

- **Unnecessary and verbose exceptions** A few SK components, such as the Kernel or Planner, have exceptions at their level, namely PlanningException or KernelException, that are not truly necessary and can be easily replaced by SKException and a few of its derivatives. SK clients might become dependent on them, making it challenging to remove them later if SK needs to discontinue their usage. Additionally, SK has an exception type for each SK memory connector - PineconeMemoryException, QdrantMemoryException that does not add any additional information and only differs by name while having the same member signatures. This makes it impossible for SK client code to handle them in a consolidated manner. Instead of having a single catch block, SK client code needs to include a catch block for each component implementation. Moreover, SK client code needs to be updated every time a new component implementation is added or removed.

- **Missing original exception details**. Certain SK exceptions do not preserve the original failure or exception details and do not expose them through their properties. This omission prevents SK client code from understanding the problem and handling it properly.

## Decision Drivers

- Exceptions should be propagated to the SK client code instead of being stored in the SKContext. This adjustment will bring SK error handling in line with the .NET approach.
- The SK exception hierarchy should be designed following the principle of "less is more." It is easier to add new exceptions later, but removing them can be challenging.
- .NET standard exception types should be preferred over SK custom ones because they are easily recognizable, do not require any maintenance, can cover common error scenarios, and provide meaningful and standardized error messages.
- Exceptions should not be wrapped in SK exceptions when passing them up to a caller, unless it helps in constructing actionable logic for either SK or SK client code.

## Considered Options

- Simplify existing SK exception hierarchy by removing all custom exceptions types except the SKException one and any other type that is actionable. Use SKException type instead of the removed ones unless more details need to be conveyed in which case create a derived specific exception.
- Modify SK code to throw .NET standard exceptions, such as ArgumentOutOfRangeException or ArgumentNullException, when class argument values are not provided or are invalid, instead of throwing custom SK exceptions. Analyze SK exception usage to identify and fix other potential areas where standard .NET exceptions can be used instead.
- Remove any code that wraps unhandled exceptions into AIException or any other SK exception solely for the purpose of wrapping. In most cases, this code does not provide useful information to action on it, apart from a generic and uninformative "Something went wrong" message.
- Identify all cases where the original exception is not preserved as an inner exception of the rethrown SK exception, and address them.
- Create a new exception HttpOperationException, which includes a StatusCode property, and implement the necessary logic to map the exception from HttpStatusCode, HttpRequestException, or Azure.RequestFailedException. Update existing SK code that interacts with the HTTP stack to throw HttpOperationException in case of a failed HTTP request and assign the original exception as its inner exception.
- Modify all SK components that currently store exceptions to SK context to rethrow them instead.
- Simplify the SK critical exception handling functionality by modifying the IsCriticalException extension method to exclude handling of StackOverflowException and OutOfMemoryException exceptions. This is because the former exception is not thrown, so the calling code won't be executed, while the latter exception doesn't necessarily prevent the execution of recovery code.