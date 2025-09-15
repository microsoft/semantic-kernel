---
status: proposed
contact: rogerbarreto
date: 2025-03-07
deciders: rogerbarreto, markwallace, dmytrostruk, westey-m, sergeymenshykh
---

# Structured Data Plugin Implementation in Semantic Kernel

## Context and Problem Statement

Modern AI applications often need to interact with structured data in databases while leveraging LLM capabilities. As Semantic Kernel's core focuses on AI orchestration, we need a standardized approach to integrate database operations with AI capabilities. This ADR proposes an experimental StructuredDataConnector as an initial solution for database-AI integration, focusing on basic CRUD operations and simple querying.

## Decision Drivers

- Need for initial database integration pattern with SK
- Requirement for basic composable AI and database operations
- Alignment with SK's plugin architecture
- Ability to validate the approach through real-world usage
- Support for strongly-typed schema validation
- Consistent JSON formatting for AI interactions

## Key Benefits

1. **Plugin-Based Architecture**

   - Aligns with SK's plugin architecture
   - Supports extension methods for common operations
   - Leverages KernelJsonSchema for type safety

2. **Structured Data Operations**

   - CRUD operations with schema validation
   - JSON-based interactions with proper formatting
   - Type-safe database operations

3. **Integration Features**

   - Built-in JSON schema generation
   - Automatic type conversion
   - Pretty-printed JSON for better AI interactions

## Implementation Details

The implementation includes:

1. Core Components:

   - `StructuredDataService<TContext>`: Base service for database operations
   - `StructuredDataServiceExtensions`: Extension methods for CRUD operations
   - `StructuredDataPluginFactory`: Factory for creating SK plugins
   - Integration with `KernelJsonSchema` for type validation

2. Key Features:

   - Automatic schema generation from entity types
   - Properly formatted JSON responses
   - Extension-based architecture for maintainability
   - Support for Entity Framework Core

3. Usage Example:

```csharp
var service = new StructuredDataService<ApplicationDbContext>(dbContext);
var plugin = StructuredDataPluginFactory.CreateStructuredDataPlugin<ApplicationDbContext, MyEntity>(
    service,
    operations: StructuredDataOperation.Default);
```

## Decision Outcome

Chosen option: TBD:

1. Provides standardized database integration
2. Leverages SK's schema validation capabilities
3. Supports proper JSON formatting for AI interactions
4. Maintains type safety through generated schemas
5. Follows established SK patterns and principles

## More Information

This is an experimental approach that will evolve based on community feedback.
