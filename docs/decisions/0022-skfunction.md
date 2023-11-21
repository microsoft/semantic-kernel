---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: markwallace-microsoft
date: 2023-11-21
deciders: SergeyMenshykh, markwallace, rbarreto, mabolan, stephentoub
consulted: 
informed: 
---

# Semantic Kernel Functions are defined using Interface or Abstract Base Class

## Context and Problem Statement

The Semantic Kernel must define an abstraction to represent a Function i.e. a method that can be called as part of an AI orchestration.
Currently this abstraction is the `ISKFunction` interface.
The goal of the ADR is decide if this is the best abstraction to use to meet the long term goals of Semantic Kernel.

## Decision Drivers

- The abstraction **must** extensible so that new functionality can be added later.
- Changes to the abstraction **must not** result in breaking changes for consumers.
- It is not clear at this time if we need to allow consumers to provide their own `SKFunction` implementations. If we do we this may cause problems as we add new functionality to the Semantic Kernel e.g. what if we define a new hook type?

## Considered Options

- `ISKFunction` interface
- `SKFunction` base class

### `ISKFunction` Interface

- Good, because implementations can extend any arbitrary class
- Bad, because we can only change the default behavior of our implementations and customer implementations may become incompatible.
- Bad, because we cannot prevent customers for implementing this interface.
- Bad, because changes to the interface are breaking changes for consumers.

### `SKFunction` Case Class

- Good, because the changes to the interface are **not** breaking changes for consumers.
- Good, because class constructor can be made `internal` so we can prevent extensions until we know there are valid use cases.
- Good, because we can change the default implementation easily in future.
- Bad, because implementations can only extend `SKFunction`.

## Decision Outcome

Chosen option: "`SKFunction` base class", because we can provide some default implementation and we can restrict creation of new SKFunctions until we better understand those use cases.
