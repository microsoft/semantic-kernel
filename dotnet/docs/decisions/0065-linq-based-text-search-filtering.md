---
status: accepted
contact: alzarei
date: 2025-10-25
deciders: roji, westey-m, markwallace-microsoft
consulted:
informed:
---

# Migrate ITextSearch from Clause-Based to LINQ-Based Filtering

## Context and Problem Statement

**The Challenge**: The existing `ITextSearch` interface uses clause-based `TextSearchFilter` for filtering, which creates runtime errors from property name typos, lacks IntelliSense support, and depends on obsolete `VectorSearchFilter` APIs. Modern .NET practices favor LINQ expressions for type safety and compile-time validation.

**The Constraint**: We cannot introduce breaking changes. Existing code using `TextSearchFilter` must continue working.

**The Question**: How do we migrate ITextSearch to modern LINQ-based filtering (`Expression<Func<TRecord, bool>>`) while maintaining backward compatibility?

Issue: https://github.com/microsoft/semantic-kernel/issues/10456

## Decision Drivers

- **Type Safety**: Eliminate runtime errors from property name typos and type mismatches
- **Developer Experience**: Enable IntelliSense and compile-time validation
- **Technical Debt**: Remove dependency on obsolete VectorSearchFilter API
- **Performance**: Eliminate unnecessary conversion overhead
- **Consistency**: Align with Microsoft.Extensions.VectorData LINQ filtering patterns
- **Backward Compatibility**: Maintain existing functionality for consumers
- **AOT Compatibility**: Support ahead-of-time compilation scenarios
- **Migration Path**: Establish clear path for eventual removal of legacy interface

## Decision Outcome

**Chosen Option**: "Dual Interface Pattern". Introduce generic `ITextSearch<TRecord>` with LINQ filtering alongside existing `ITextSearch` marked `[Obsolete]`.

We introduce **`ITextSearch<TRecord>`** (modern, LINQ-based) alongside the existing **`ITextSearch`** (legacy, marked `[Obsolete]`). Both interfaces coexist temporarily to provide:

- ✅ **Zero breaking changes**: Existing code continues working unchanged
- ✅ **Clear migration signal**: Deprecation warnings guide developers to modern interface
- ✅ **Type safety for new code**: LINQ expressions provide compile-time validation
- ✅ **Clean separation**: Legacy and modern paths are completely independent
- ✅ **Future removal path**: Establishes timeline for eventual legacy interface elimination

This is explicitly a **temporary architectural state**, not a permanent design. The dual interface pattern enables non-breaking migration while establishing a clear path to remove technical debt in a future major version.

### Pros and Cons of the Decision

**Good, because**:

- **Zero breaking changes**: Existing code continues working unchanged
- **Clean separation**: Legacy and modern paths completely independent (no translation overhead)
- **Type safety**: Generic interface provides compile-time validation and IntelliSense
- **AOT compatibility**: Both interfaces are AOT-compatible (no blocking attributes)
- **Clear migration path**: `[Obsolete]` attribute signals deprecation and guides users to modern interface
- **Future-ready**: Establishes clear path for eventual removal of legacy interface in future major version
- **Ecosystem alignment**: Gives consumers time to migrate before breaking change
- **Phased implementation**: Reduces risk and enables focused code review

**Bad, because**:

- **Dual code paths**: Maintains two implementations per class (**temporary** during transition period)
- **Obsolete API usage**: Non-generic path uses deprecated `VectorSearchFilter.OldFilter` with pragma suppressions (**temporary**)
- **Documentation burden**: Must explain when to use which interface during transition period
- **Temporary complexity**: Additional maintenance burden until legacy interface removal

**Key Insight**: The "bad" aspects are explicitly **temporary**. They exist only during the migration period and will be eliminated when the legacy interface is removed in a future major version.

## Implementation Sub-Decisions

This section documents specific implementation choices required to realize the dual interface pattern.

### Sub-Decision 1: Architecture Overview

The dual interface pattern creates two parallel execution paths:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          ITextSearch Modernization                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ Interface Layer                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Obsolete]                              [Modern]                            │
│  ITextSearch                             ITextSearch<TRecord>                │
│  ├─ TextSearchOptions                    ├─ TextSearchOptions<TRecord>       │
│  │  └─ TextSearchFilter                  │  └─ Expression<Func<T, bool>>     │
│  └─ No RequiresDynamicCode               └─ No RequiresDynamicCode           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ Implementation Layer: Two Patterns                                           │
└──────────────────────────────────────────────────────────────────────────────┘

Pattern A: Direct LINQ Passthrough          Pattern B: LINQ-to-Legacy Conversion
(VectorStoreTextSearch)                     (BingTextSearch, GoogleTextSearch, etc.)

┌──────────────────────────────┐           ┌──────────────────────────────────┐
│ VectorStoreTextSearch        │           │ BingTextSearch                   │
│ : ITextSearch                │           │ : ITextSearch                    │
│ : ITextSearch<TRecord>       │           │ : ITextSearch<BingWebPage>       │
├──────────────────────────────┤           ├──────────────────────────────────┤
│ Legacy Path:                 │           │ Legacy Path:                     │
│  TextSearchFilter            │           │  TextSearchFilter                │
│       ↓                      │           │       ↓                          │
│  VectorSearchFilter.OldFilter│           │  Bing API parameters             │
│  (obsolete, pragma)          │           │       ↓                          │
│       ↓                      │           │  HTTP GET request                │
│  Vector Store                │           │                                  │
│                              │           │ Modern Path:                     │
│ Modern Path:                 │           │  Expression<Func<T, bool>>       │
│  Expression<Func<T, bool>>   │           │       ↓                          │
│       ↓                      │           │  LINQ tree analysis              │
│  VectorSearchOptions.Filter  │           │       ↓                          │
│  (direct passthrough)        │           │  TextSearchFilter (conversion)   │
│       ↓                      │           │       ↓                          │
│  Vector Store                │           │  Delegate to legacy path         │
└──────────────────────────────┘           └──────────────────────────────────┘

Key: Two INDEPENDENT paths             Key: Modern converts to legacy
     NO translation between them             Reuses existing implementation
```

**Key Architectural Characteristics**:

1. **Interface Layer**: Two separate interfaces: legacy (`ITextSearch`) and modern (`ITextSearch<TRecord>`)
2. **Pattern A (VectorStoreTextSearch)**: Two completely independent code paths - NO translation, NO conversion overhead
3. **Pattern B (Web Connectors)**: LINQ expressions converted to legacy `TextSearchFilter`, then delegated to existing implementation
4. **RequiresDynamicCode**: NONE - No `[RequiresDynamicCode]` attributes on either interface or implementations
5. **AOT Compatibility**: Both interfaces are AOT-compatible (no attributes blocking compilation or runtime)

### Sub-Decision 2: Two Implementation Patterns

All implementations follow the dual interface pattern, but with **two different execution strategies** based on underlying service capabilities:

#### Pattern A: Direct LINQ Passthrough (VectorStoreTextSearch)

VectorStoreTextSearch has two **completely independent** code paths with NO conversion:

```csharp
#pragma warning disable CS0618 // ITextSearch is obsolete - backward compatibility
public sealed class VectorStoreTextSearch<TRecord> : ITextSearch, ITextSearch<TRecord>
#pragma warning restore CS0618
{
    // ===== LEGACY PATH (Non-Generic Interface) =====
    public Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default)
    {
        var searchResponse = ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);
        return Task.FromResult(CreateStringSearchResponse(searchResponse));
    }

    // ===== MODERN PATH (Generic Interface) =====
    Task<KernelSearchResults<string>> ITextSearch<TRecord>.SearchAsync(
        string query,
        TextSearchOptions<TRecord>? searchOptions,
        CancellationToken cancellationToken)
    {
        var searchResponse = ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);
        return Task.FromResult(CreateStringSearchResponse(searchResponse));
    }

    // Legacy path: Uses obsolete VectorSearchFilter.OldFilter
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteVectorSearchAsync(
        string query, TextSearchOptions? searchOptions, ...)
    {
        var vectorSearchOptions = new VectorSearchOptions<TRecord> {
            #pragma warning disable CS0618
            OldFilter = searchOptions.Filter?.FilterClauses is not null
                ? new VectorSearchFilter(searchOptions.Filter.FilterClauses)
                : null,
            #pragma warning restore CS0618
        };
        // ... execute
    }

    // Modern path: Direct LINQ passthrough - no obsolete API
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteVectorSearchAsync(
        string query, TextSearchOptions<TRecord>? searchOptions, ...)
    {
        var vectorSearchOptions = new VectorSearchOptions<TRecord> {
            Filter = searchOptions.Filter,  // Direct LINQ - no conversion
        };
        // ... execute
    }
}
```

#### Pattern B: LINQ-to-Legacy Conversion (Web Search Connectors)

BingTextSearch, GoogleTextSearch, TavilyTextSearch, BraveTextSearch convert generic interface calls to legacy format:

```csharp
#pragma warning disable CS0618 // ITextSearch is obsolete
public sealed class BingTextSearch : ITextSearch, ITextSearch<BingWebPage>
#pragma warning restore CS0618
{
    // ===== LEGACY PATH (Non-Generic Interface) =====
    public Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default)
    {
        // Direct Bing API call with TextSearchFilter
        // ... existing logic
    }

    // ===== MODERN PATH (Generic Interface) =====
    Task<KernelSearchResults<string>> ITextSearch<BingWebPage>.SearchAsync(
        string query,
        TextSearchOptions<BingWebPage>? searchOptions,
        CancellationToken cancellationToken)
    {
        // Convert generic options to legacy format
        var legacyOptions = searchOptions != null
            ? ConvertToLegacyOptions(searchOptions)
            : new TextSearchOptions();

        // Delegate to existing legacy implementation
        return this.SearchAsync(query, legacyOptions, cancellationToken);
    }

    // LINQ-to-TextSearchFilter conversion
    private static TextSearchOptions ConvertToLegacyOptions<TRecord>(
        TextSearchOptions<TRecord> genericOptions)
    {
        return new TextSearchOptions
        {
            Top = genericOptions.Top,
            Skip = genericOptions.Skip,
            Filter = genericOptions.Filter != null
                ? ConvertLinqExpressionToBingFilter(genericOptions.Filter)
                : null
        };
    }

    // Expression tree analysis and mapping to Bing API syntax
    private static TextSearchFilter ConvertLinqExpressionToBingFilter<TRecord>(
        Expression<Func<TRecord, bool>> linqExpression)
    {
        var filter = new TextSearchFilter();
        // Recursively process expression tree:
        // - Equality (==) → language:en
        // - Inequality (!=) → -language:fr
        // - Contains() → intitle:"AI" or inbody:"term"
        // - AND (&&) → multiple filter clauses
        ProcessExpression(linqExpression.Body, filter);
        return filter;
    }
}
```

**Key Differences**:

| Aspect                 | Pattern A (VectorStoreTextSearch)            | Pattern B (Web Connectors)                   |
| ---------------------- | -------------------------------------------- | -------------------------------------------- |
| **Execution Paths**    | Two independent paths                        | Modern converts to legacy                    |
| **Conversion Layer**   | NO conversion                                | LINQ → TextSearchFilter                      |
| **Legacy Path**        | Uses obsolete `VectorSearchFilter.OldFilter` | Uses existing `TextSearchFilter` directly    |
| **Modern Path**        | Uses `VectorSearchOptions.Filter` directly   | Converts LINQ then delegates to legacy path  |
| **Performance**        | Zero overhead (direct passthrough)           | Conversion overhead acceptable (network I/O) |
| **Underlying Support** | Native LINQ support                          | API-specific parameter mapping               |

**Why Two Patterns?**

1. **VectorStoreTextSearch**: Underlying vector store natively supports LINQ expressions via `VectorSearchOptions<TRecord>.Filter`. Direct passthrough eliminates overhead.
2. **Web Connectors**: Underlying APIs (Bing, Google) don't accept LINQ. Conversion to TextSearchFilter then to API parameters maintains compatibility.

**Note**: Both patterns maintain dual code paths (legacy + modern) as a **temporary migration strategy**. Once the obsolete `ITextSearch` interface is removed in a future major version, only the modern LINQ path will remain, eliminating the dual implementation complexity.

### Sub-Decision 3: AOT Compatibility Strategy

Both interfaces are designed to be AOT-compatible with **no `[RequiresDynamicCode]` attributes**:

**Non-Generic Interface (`ITextSearch`)**:

- ✅ Fully AOT-compatible
- Uses `TextSearchFilter` (clause-based, no LINQ)
- No dynamic code generation required

**Generic Interface (`ITextSearch<TRecord>`)**:

- ✅ AOT-compatible
- Uses LINQ expressions
- Processed via **expression tree analysis**, not dynamic code generation
- No `[RequiresDynamicCode]` attribute required

**LINQ Expression Processing**:

```csharp
// Simple equality - AOT-compatible
filter = doc => doc.Department == "HR" && doc.IsActive

// Complex expressions - AOT-compatible (expression tree analysis)
filter = doc => doc.Tags.Any(tag => tag.Contains("urgent"))
```

**AOT Compatibility Matrix**:

| Scenario                       | ITextSearch       | ITextSearch&lt;TRecord&gt; | Notes                         |
| ------------------------------ | ----------------- | -------------------------- | ----------------------------- |
| Simple searches (no filtering) | ✅ AOT-compatible | ✅ AOT-compatible          | No dynamic code needed        |
| TextSearchFilter-based         | ✅ AOT-compatible | N/A                        | Legacy clause-based filtering |
| Simple LINQ (equality)         | N/A               | ✅ AOT-compatible          | Expression tree analysis      |
| Complex LINQ (Contains, Any)   | N/A               | ✅ AOT-compatible          | Expression tree analysis      |

### Sub-Decision 4: Contains() Support for Web Search Connectors

**Context**: The `ITextSearch<TRecord>` interface supports LINQ expressions, including `Title.Contains("value")` patterns. Different search engine APIs have varying capabilities:

- **Bing**: Native advanced search operators (`intitle:`, `inbody:`, `url:`)
- **Google**: Specialized API parameters (`orTerms` for additional search terms)
- **Brave/Tavily**: General search APIs without field-specific operators

**Decision**: Implement `Title.Contains()` support using **query enhancement** for Brave and Tavily search engines:

1. **SearchQueryFilterClause**: New filter clause type that adds terms to the search query rather than filtering results
2. **Query Enhancement Pattern**: Extract terms from `SearchQueryFilterClause` instances and append to base search query
3. **Dual Processing**: Handle `SearchQueryFilterClause` differently from regular filter clauses

**Implementation Pattern**:

```csharp
// LINQ Expression: results.Where(r => r.Title.Contains("AI"))
// Converts to: new SearchQueryFilterClause("AI")
// Query Enhancement: "original query" + " AI"
```

**Alternatives Considered**:

1. **Direct API Parameters**: Not available in Brave/Tavily APIs
2. **Post-Search Filtering**: Would reduce result relevance and performance
3. **NotSupportedException**: Would limit LINQ expression capabilities

**Consequences**:

- ✅ Consistent LINQ expression support across search engines
- ✅ Enhanced search relevance by modifying query rather than filtering results
- ✅ Extensible pattern for future Contains() implementations
- ⚠️ Different implementation approaches across search engines (consistency concern)
- ⚠️ Additional complexity in filter clause processing

### Sub-Decision 5: SearchQueryFilterClause Location and FilterClause Constructor Visibility

**Context**: `SearchQueryFilterClause` is used only by web search connectors (Brave, Tavily) in `Plugins.Web`. To minimize public API surface, it should reside in the same assembly as its consumers.

**Problem**: `FilterClause` base class originally had an **internal constructor**, preventing inheritance outside the `VectorData.Abstractions` assembly:

```csharp
public abstract class FilterClause
{
    internal FilterClause()  // ← Blocked external inheritance
}
```

Moving `SearchQueryFilterClause` to `Plugins.Web` failed with:

```
error CS0122: 'FilterClause.FilterClause()' is inaccessible due to its protection level
```

**Decision**: Make `FilterClause` constructor **`protected`** and move `SearchQueryFilterClause` to `Plugins.Web` as **`internal sealed`**.

```csharp
// In VectorData.Abstractions
public abstract class FilterClause
{
    protected FilterClause()  // internal → protected
}

// In Plugins.Web
internal sealed class SearchQueryFilterClause : FilterClause
```

**Rationale**:

- **Minimal API surface**: `SearchQueryFilterClause` stays internal (not public)
- **Controlled extensibility**: `protected` allows inheritance but maintains encapsulation
- **Correct location**: Class lives in `Plugins.Web` where it's actually used
- **Standard pattern**: `protected` constructors are common for abstract base classes

**Alternatives Considered**:

1. **Keep internal constructor + public SearchQueryFilterClause in VectorData**: Adds unnecessary public API
2. **Internal + InternalsVisibleTo**: Causes 200 CS0436 type conflict errors in CI
3. **Public constructor**: Too permissive, allows unrestricted external filter types
4. **Don't inherit from FilterClause**: Breaks established pattern, loses type safety

**Consequences**:

- ✅ Minimal public API impact (only constructor visibility change on existing abstract class)
- ✅ `SearchQueryFilterClause` remains internal implementation detail
- ✅ Enables future filter clause implementations outside VectorData assembly
- ✅ Clean implementation with no workarounds

### Sub-Decision 6: Obsolete Marking Strategy

**Decision**: Mark the original `ITextSearch` interface with `[Obsolete]` attribute immediately:

```csharp
[Obsolete("ITextSearch is deprecated. Use ITextSearch<TRecord> with LINQ filtering instead.")]
public interface ITextSearch
{
    // Legacy implementation
}
```

**Purpose of Obsolete Marking**:

1. **Developer Guidance**: Compile-time warnings inform developers that this API should not be used in new code
2. **Migration Signal**: Clear indication that this interface will be removed in a future major version
3. **Ecosystem Preparation**: Gives library consumers advance notice to plan migration work
4. **IDE Support**: Modern IDEs display deprecation warnings and suggest alternatives

**Why Mark as Obsolete Now** (rather than waiting):

- Prevents new code from adopting legacy patterns
- Starts ecosystem migration clock immediately
- Aligns with .NET best practices for API evolution
- Allows sufficient migration period before actual removal (typically 1-2 major versions)

## Migration Strategy

This decision implements a **deliberate three-phase migration path** from legacy clause-based filtering to modern LINQ-based filtering:

### Phase 1: Transition State (Current - Implemented in This ADR)

- ✅ `ITextSearch<TRecord>` introduced with LINQ filtering (modern, recommended)
- ✅ `ITextSearch` marked `[Obsolete]` with deprecation warning
- ✅ Both interfaces coexist for backward compatibility
- ✅ All implementations support both interfaces
- ✅ Documentation updated to recommend generic interface

**Key Point**: Marking `ITextSearch` as `[Obsolete]` serves dual purposes:

- **Immediate**: Signals to developers that this interface is deprecated and should not be used in new code
- **Long-term**: Establishes clear path for eventual removal, allowing ecosystem to migrate before breaking change

### Phase 2: Increased Deprecation (Future - Next Major Version)

- Increase obsolete warning severity (`ObsoleteAttribute` with `error: true`)
- Add removal timeline to documentation
- Final migration period for stragglers
- Communication campaign to ecosystem

### Phase 3: Legacy Removal (Eventually - Future Major Version)

- **BREAKING CHANGE**: Remove `ITextSearch` interface entirely
- Remove public API usage of `TextSearchFilter` in `TextSearchOptions`
- Remove `VectorSearchFilter.OldFilter`
- Remove all legacy public API code paths
- Single modern interface with LINQ expressions remains
- **Note**: `TextSearchFilter` and `FilterClause` types retained internally as LINQ translation layer for web plugins only; vector stores use LINQ expressions directly via `VectorSearchOptions<TRecord>.Filter`

**Estimated Timeline**: Phase 2 in next major version (e.g., SK 2.0), Phase 3 in subsequent major version (e.g., SK 3.0). This gives ecosystem minimum 1-2 years to migrate.

### Migration Path Diagram

```
Phase 1 (Current):
├─ Both interfaces coexist
├─ Legacy ITextSearch marked [Obsolete]
├─ Deprecation warnings guide users to ITextSearch<TRecord>
└─ All implementations support both interfaces

Phase 2 (Future):
├─ Increase deprecation severity
├─ Add removal timeline to warnings
└─ Documentation emphasizes migration

Phase 3 (Eventually):
├─ Remove ITextSearch interface
├─ Remove TextSearchFilter class
├─ Remove VectorSearchFilter.OldFilter
└─ Single interface with LINQ expressions
```

The dual interface pattern is explicitly a **temporary architectural state**, not a permanent design. It provides:

- Non-breaking migration for existing consumers
- Clear migration signals via deprecation warnings
- Time for ecosystem adoption before removal
- Ability to remove technical debt in future major version

## Appendix: Alternative Options Considered

This section documents alternative approaches that were evaluated but not selected.

### Option 1: Direct LINQ Replacement (Native LINQ Only)

Replace TextSearchFilter entirely with Expression<Func<T, bool>>. Remove non-generic interface completely.

**Evaluation**:

- Good, because uniform API design with strong type safety
- Good, because eliminates all technical debt immediately
- Good, because best long-term architecture with full expression support
- Good, because aligns with Microsoft.Extensions.VectorData patterns
- Bad, because **BREAKING CHANGE**: requires all consumers to migrate
- Bad, because high disruption cost for transitive dependencies

**Why Not Chosen**: Breaking change unacceptable for stable API.

### Option 2: Native LINQ + Translation Layer

Keep both interfaces but convert TextSearchFilter to LINQ internally.

**Evaluation**:

- Good, because avoids obsolete API usage (no VectorSearchFilter dependency)
- Good, because reuses single implementation path
- Bad, because **BREAKING CHANGE**: RequiresDynamicCode cascades to ALL TextSearch APIs
- Bad, because makes entire TextSearch plugin ecosystem AOT-incompatible
- Bad, because introduces unnecessary conversion overhead
- Bad, because complex exception handling for translation failures

**Why Not Chosen**: AOT incompatibility and breaking changes unacceptable.

### Option 3: Adapter Pattern

Implement generic interface as wrapper over existing implementations.

**Evaluation**:

- Good, because minimal code changes to existing implementations
- Good, because clear separation of concerns
- Bad, because adds unnecessary abstraction layer
- Bad, because conversion overhead for every operation
- Bad, because doesn't address underlying technical debt

**Why Not Chosen**: Doesn't solve the core problem of obsolete API dependency.

### Option 4: Gradual Migration (Deprecate and Introduce)

Deprecate TextSearchFilter and introduce LINQ alongside within same interface.

**Evaluation**:

- Good, because single interface to maintain
- Bad, because creates ambiguity about which filter mechanism to use
- Bad, because requires complex runtime type checking
- Bad, because doesn't provide clear migration path

**Why Not Chosen**: Ambiguous API design and poor developer experience.

## More Information

### Related Decisions

- ADR-0058: Updated Vector Search Design (establishes LINQ-based filtering foundation)
- ADR-0059: Text Search Abstraction (defines ITextSearch interface requirements)

### Security Considerations

LINQ expressions processed on server side only. No user-supplied expression execution. Expression tree analysis validates supported operations before execution. Unsupported operations throw ArgumentException with clear error messages.

### Breaking Change Analysis

No immediate breaking changes:

- Existing TextSearchFilter-based code continues working
- New generic interface additive only
- Migration path documented
- Deprecation warnings guide future migration
