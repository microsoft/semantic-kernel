---
status: accepted
contact: alzarei
date: 2025-10-25
deciders: roji, westey-m, markwallace-microsoft
consulted: moonbox3
informed:
---

# LINQ-Based Filtering for ITextSearch Interface

## Context and Problem Statement

The ITextSearch interface uses a clause-based TextSearchFilter approach for expressing filter predicates. This design creates runtime errors from property name typos, lacks type safety, and requires conversion to obsolete VectorSearchFilter APIs internally. The interface needs modernization to provide compile-time safety, IntelliSense support, and alignment with Microsoft.Extensions.VectorData LINQ-based filtering patterns.

Issue: https://github.com/microsoft/semantic-kernel/issues/10456

## Decision Drivers

- Type safety: Eliminate runtime errors from property name typos and type mismatches
- Developer experience: Enable IntelliSense and compile-time validation
- Technical debt: Remove dependency on obsolete VectorSearchFilter API
- Performance: Eliminate unnecessary conversion overhead
- Consistency: Align with Microsoft.Extensions.VectorData LINQ filtering patterns
- Backward compatibility: Maintain existing functionality for consumers
- AOT compatibility: Support ahead-of-time compilation scenarios

## Considered Options

1. Direct LINQ replacement: Replace TextSearchFilter with Expression<Func<T, bool>> everywhere
2. Dual interface pattern: Separate generic and non-generic interfaces with different implementations
3. Adapter pattern: Implement generic interface as wrapper over existing implementations
4. Gradual migration: Deprecate TextSearchFilter and introduce LINQ alongside

## Decision Outcome

Chosen option: "Dual Interface Pattern" with clean architectural separation between legacy and modern paths, because it provides type safety benefits while maintaining 100% backward compatibility and avoids breaking changes.

### Migration Strategy

This decision implements a **deliberate migration path** from the legacy clause-based filtering to modern LINQ-based filtering:

1. **Current State (Pre-ADR)**: Single `ITextSearch` interface using `TextSearchFilter` (clause-based)
2. **Transition State (This ADR)**:
   - **NEW**: `ITextSearch<TRecord>` with LINQ filtering (modern, recommended)
   - **LEGACY**: `ITextSearch` marked `[Obsolete]` with deprecation warnings
   - Both interfaces coexist to prevent breaking changes
3. **Future State**: Remove `ITextSearch` and `TextSearchFilter` entirely, leaving only LINQ-based interface

**Key Point**: Marking the original `ITextSearch` as `[Obsolete]` serves dual purposes:

- **Immediate**: Signals to developers that this interface is deprecated and should not be used in new code
- **Long-term**: Establishes clear path for eventual removal, allowing ecosystem to migrate before breaking change

The dual interface pattern is explicitly a **temporary architectural state** - not a permanent design. It provides:

- Zero-disruption migration for existing consumers
- Clear migration signals via deprecation warnings
- Time for ecosystem adoption before removal
- Ability to remove technical debt in future major version

### Architecture Overview

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

### Key Architectural Decisions:

1. **Pattern A (VectorStoreTextSearch)**: Two completely independent code paths - NO translation layer, NO conversion overhead
2. **Pattern B (Web Connectors)**: LINQ expressions converted to legacy `TextSearchFilter`, then delegated to existing implementation
3. **RequiresDynamicCode**: NONE - No `[RequiresDynamicCode]` attributes on either interface or implementations
4. **AOT Compatibility**: Both interfaces are AOT-compatible (no attributes blocking compilation or runtime)

### Architecture: Dual Interface Pattern

**Generic Interface (ITextSearch<TRecord>)**: Modern LINQ Path

- Uses `TextSearchOptions<TRecord>` with `Expression<Func<TRecord, bool>>? Filter`
- Direct LINQ passthrough to underlying services
- NO `[RequiresDynamicCode]` attribute
- Provides compile-time type safety and IntelliSense

**Non-Generic Interface (ITextSearch)**: Legacy Compatibility Path

- Uses `TextSearchOptions` with `TextSearchFilter` (clause-based)
- Marked as `[Obsolete]` to guide migration
- NO RequiresDynamicCode - AOT compatible
- Preserves backward compatibility for existing code

### Consequences

Good, because:

- **Zero breaking changes**: Existing code continues working unchanged
- **Clean separation**: Legacy and modern paths completely independent
- **No translation overhead**: Each interface uses its optimal processing path
- **Type safety**: Generic interface provides compile-time validation and IntelliSense
- **AOT compatibility**: Both interfaces are AOT-compatible (no blocking attributes)
- **Clear migration path**: `[Obsolete]` attribute on legacy interface signals deprecation and guides users to modern interface
- **Phased implementation**: Reduces risk and enables focused code review
- **Future-ready**: Establishes clear path for eventual removal of legacy interface in future major version
- **Ecosystem alignment**: Gives consumers time to migrate before breaking change

Bad, because:

- **Dual code paths**: Maintains two implementations per class (temporary during transition period)
- **Obsolete API usage**: Non-generic path uses deprecated `VectorSearchFilter.OldFilter` with pragma suppressions
- **Documentation burden**: Must explain when to use which interface during transition period
- **Temporary complexity**: Additional maintenance burden until legacy interface removal

## Implementation Details

### Dual Interface Implementation Pattern

**All implementations** follow the same dual interface pattern but with **two different approaches** based on service characteristics:

#### Pattern A: Direct LINQ Passthrough (VectorStoreTextSearch)

VectorStoreTextSearch has two completely independent code paths with NO conversion:

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

### Key Differences Between Patterns:

**VectorStoreTextSearch (Pattern A)**:

- Two independent code paths
- NO conversion layer
- Legacy uses obsolete `VectorSearchFilter.OldFilter`
- Modern uses `VectorSearchOptions.Filter` directly

**Web Connectors (Pattern B)**:

- Generic interface converts to legacy
- Reuses existing legacy implementation
- LINQ expression tree analysis
- Maps to API-specific syntax (Bing operators, Google parameters, etc.)

### Why Two Patterns?

1. **VectorStoreTextSearch**: Underlying vector store natively supports LINQ expressions via `VectorSearchOptions<TRecord>.Filter` - direct passthrough eliminates overhead

2. **Web Connectors**: Underlying APIs (Bing, Google) don't accept LINQ - conversion to TextSearchFilter then to API parameters maintains compatibility

**Note**: Both patterns maintain dual code paths (legacy + modern) as a **temporary migration strategy**. Once the obsolete `ITextSearch` interface is removed in a future major version, only the modern LINQ path will remain, eliminating the dual implementation complexity.

### Common Characteristics:

**AOT Compatibility** (both patterns):

- Non-generic interface: ✅ Fully AOT-compatible (uses TextSearchFilter, no LINQ)
- Generic interface: ✅ AOT-compatible (no RequiresDynamicCode attributes)
- LINQ expression processing: ✅ Compatible (expression tree analysis, no dynamic code generation)

### Unified Implementation Pattern

**All implementations** follow the **same dual interface pattern**:

1. Implement both `ITextSearch` (legacy, obsolete) and `ITextSearch<TRecord>` (modern, generic)
2. Two independent code paths - no translation between them
3. Legacy path uses `TextSearchFilter` → service-specific API
4. Modern path uses LINQ expressions → service-specific API
5. Pragma warnings suppress obsolete interface usage

**Service Capability Considerations**:

| Capability      | Vector Stores                                 | Web APIs (Bing/Google/Tavily/Brave)     |
| --------------- | --------------------------------------------- | --------------------------------------- |
| LINQ Support    | Native                                        | Limited (basic equality/AND operations) |
| Filter Approach | Direct passthrough                            | Service-specific parameter mapping      |
| Legacy Path     | VectorSearchFilter.OldFilter                  | TextSearchFilter → API parameters       |
| Modern Path     | LINQ expressions → VectorSearchOptions.Filter | LINQ expressions → API parameters       |

**Key Insight**: Web search connectors implement both interfaces but handle LINQ expressions according to their API capabilities. Unsupported operations throw clear exceptions with guidance, rather than silently degrading.

### Obsolete Marking Strategy

**Immediate Effect (This ADR)**: The original `ITextSearch` interface is marked with `[Obsolete]` attribute:

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

### Migration Path

**Phase 1 (Current - Implemented in This ADR)**:

- ✅ `ITextSearch<TRecord>` introduced with LINQ filtering (modern, recommended)
- ✅ `ITextSearch` marked `[Obsolete]` with deprecation warning
- ✅ Both interfaces coexist for backward compatibility
- ✅ All implementations support both interfaces
- ✅ Documentation updated to recommend generic interface

**Phase 2 (Future - Next Major Version)**:

- Increase obsolete warning severity (ObsoleteAttribute with `error: true`)
- Add removal timeline to documentation
- Final migration period for stragglers
- Communication campaign to ecosystem

**Phase 3 (Eventually - Future Major Version)**:

- **BREAKING CHANGE**: Remove `ITextSearch` interface entirely
- Remove `TextSearchFilter` class
- Remove `VectorSearchFilter.OldFilter`
- Remove all legacy code paths
- Single modern interface with LINQ expressions remains

**Estimated Timeline**: Phase 2 in next major version (e.g., SK 2.0), Phase 3 in subsequent major version (e.g., SK 3.0). This gives ecosystem minimum 1-2 years to migrate.

### Text Search Contains() Support Implementation

The `ITextSearch<TRecord>` interface supports LINQ expressions, including `Title.Contains("value")` patterns. Different search engine APIs have varying capabilities for handling text matching within specific fields:

- **Bing**: Native advanced search operators (`intitle:`, `inbody:`, `url:`)
- **Google**: Specialized API parameters (`orTerms` for additional search terms)
- **Brave/Tavily**: General search APIs without field-specific operators

**Decision**: Implement `Title.Contains()` support using **query enhancement** for Brave and Tavily search engines:

1. **SearchQueryFilterClause**: New filter clause type that adds terms to the search query rather than filtering results
2. **Query Enhancement Pattern**: Extract terms from `SearchQueryFilterClause` instances and append to base search query
3. **Dual Processing**: Handle `SearchQueryFilterClause` differently from regular filter clauses in `ConvertToLegacyOptionsWithQuery`

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
- ✅ Maintains backward compatibility with legacy `ITextSearch` interface
- ⚠️ Different implementation approaches across search engines (consistency concern)
- ⚠️ Additional complexity in filter clause processing
- ⚠️ Query enhancement may affect search precision in some cases

### SearchQueryFilterClause Public Visibility

**Context**: Reviewer feedback requested moving `SearchQueryFilterClause` from `VectorData.Abstractions` to `Plugins.Web` to reduce public API surface. Investigation revealed architectural constraint preventing this move.

**Problem**: `FilterClause` base class has an **internal constructor**, preventing inheritance outside the `VectorData.Abstractions` assembly:

```csharp
public abstract class FilterClause
{
    internal FilterClause()  // ← Blocks external inheritance
}
```

Attempted move to `Plugins.Web` fails with:
```
error CS0122: 'FilterClause.FilterClause()' is inaccessible due to its protection level
```

**Decision**: Make `SearchQueryFilterClause` **public** and keep it in `VectorData.Abstractions`.

```csharp
public sealed class SearchQueryFilterClause : FilterClause
```

**Rationale**:

- **Why public**: Respects existing `FilterClause` architecture (internal constructor is intentional design)
- Legitimate reusable abstraction for text search scenarios
- Consistent with precedent: `EqualToFilterClause`, `AnyTagEqualToFilterClause` are public
- Cleanest solution with no workarounds

**Alternatives Considered**:

1. **Move to Plugins.Web**: Impossible due to internal constructor
2. **Internal + InternalsVisibleTo**: Causes 200 CS0436 type conflict errors in CI
3. **Make FilterClause constructor public**: Too broad, opens VectorData to external filter types
4. **Don't inherit from FilterClause**: Breaks established pattern, loses type safety

**Consequences**:

- ✅ Respects intentional `FilterClause` architecture
- ✅ Maintains consistency with other public filter clause types
- ✅ Clean implementation with no workarounds
- ✅ Reusable for future text search scenarios
- ⚠️ Adds to public API surface (minimal impact - single sealed class)

## Pros and Cons of the Options

### Option 1: Native LINQ Only

Replace TextSearchFilter entirely with Expression<Func<T, bool>> - remove non-generic interface completely.

- Good, because uniform API design with maximum type safety
- Good, because eliminates all technical debt immediately
- Good, because best long-term architecture and unlimited expressiveness
- Good, because aligns with Microsoft.Extensions.VectorData patterns
- Bad, because **BREAKING CHANGE** - requires all consumers to migrate
- Bad, because high disruption cost for transitive dependencies

### Option 2: Native LINQ + Translation Layer

Keep both interfaces but convert TextSearchFilter to LINQ internally.

- Good, because avoids obsolete API usage (no VectorSearchFilter dependency)
- Good, because reuses single implementation path
- Bad, because **BREAKING CHANGE** - RequiresDynamicCode cascades to ALL TextSearch APIs
- Bad, because makes entire TextSearch plugin ecosystem AOT-incompatible
- Bad, because introduces unnecessary conversion overhead
- Bad, because complex exception handling for translation failures

### Option 3: Dual Interface Pattern (SELECTED)

Keep both ITextSearch and ITextSearch<TRecord> with separate code paths, with legacy interface marked `[Obsolete]`.

- Good, because **ZERO BREAKING CHANGES** - existing code unaffected
- Good, because clear separation between legacy and modern approaches
- Good, because both paths AOT-compatible (no RequiresDynamicCode on non-generic)
- Good, because no translation layer - zero conversion overhead
- Good, because gradual LINQ adoption without forced migration
- Good, because **establishes clear migration path** - `[Obsolete]` signals deprecation and future removal
- Good, because **future-proof design** - can cleanly remove legacy interface in future major version
- Good, because gives ecosystem sufficient time to migrate (1-2 major versions)
- Good, because can migrate to Option 1 (Native LINQ Only) later with proper planning and advance notice
- Neutral, because maintains obsolete API dependency temporarily (acceptable during transition)
- Bad, because duplicate implementation maintenance (**temporary** - removed when legacy interface eliminated)
- Bad, because technical debt persists in non-generic path (**temporary** - removed in future major version)

## More Information

### Related Decisions

- ADR-0058: Updated Vector Search Design (establishes LINQ-based filtering foundation)
- ADR-0059: Text Search Abstraction (defines ITextSearch interface requirements)

### Pattern Comparison

```
┌───────────────────────────────────────────────────────────────────────┐
│                     Pattern A vs Pattern B                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Pattern A: Direct LINQ Passthrough                                   │
│  Used by: VectorStoreTextSearch                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                                                              │     │
│  │  Legacy: TextSearchFilter → VectorSearchFilter.OldFilter     │     │
│  │          (pragma warnings, temporary during transition)      │     │
│  │                                                              │     │
│  │  Modern: LINQ Expression → VectorSearchOptions.Filter        │     │
│  │          (direct passthrough, no conversion)                 │     │
│  │                                                              │     │
│  │  Result: Two independent paths, zero overhead                │     │
│  │                                                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  Pattern B: LINQ-to-Legacy Conversion                                 │
│  Used by: BingTextSearch, GoogleTextSearch, Tavily, Brave             │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                                                              │     │
│  │  Legacy: TextSearchFilter → API parameters                   │     │
│  │          (existing implementation, unchanged)                │     │
│  │                                                              │     │
│  │  Modern: LINQ Expression → [Analyze] → TextSearchFilter      │     │
│  │          → Delegate to legacy path                           │     │
│  │                                                              │     │
│  │  Result: Suitable for network-bound operations               │     │
│  │                                                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### AOT Compatibility

Both interfaces are AOT-compatible with no `[RequiresDynamicCode]` attributes:

```csharp
// Simple equality - AOT-compatible
filter = doc => doc.Department == "HR" && doc.IsActive

// Complex expressions - AOT-compatible (expression tree analysis)
filter = doc => doc.Tags.Any(tag => tag.Contains("urgent"))
```

LINQ expressions are processed via expression tree inspection, not dynamic code generation. Both interfaces work in AOT compilation scenarios.

### AOT Compatibility Matrix

| Scenario                       | ITextSearch       | ITextSearch&lt;TRecord&gt; | Notes                         |
| ------------------------------ | ----------------- | -------------------------- | ----------------------------- |
| Simple searches (no filtering) | ✅ AOT-compatible | ✅ AOT-compatible          | No dynamic code needed        |
| TextSearchFilter-based         | ✅ AOT-compatible | N/A                        | Legacy clause-based filtering |
| Simple LINQ (equality)         | N/A               | ✅ AOT-compatible          | Expression tree analysis      |
| Complex LINQ (Contains, Any)   | N/A               | ✅ AOT-compatible          | Expression tree analysis      |

**Note**: No `[RequiresDynamicCode]` attributes exist. LINQ expressions are analyzed via expression tree inspection, not dynamic code generation.

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

### Breaking Change Analysis

No immediate breaking changes:

- Existing TextSearchFilter-based code continues working
- New generic interface additive only
- Migration path documented
- Deprecation warnings guide future migration

### Security Considerations

LINQ expressions processed on server side only. No user-supplied expression execution. Expression tree analysis validates supported operations before execution. Unsupported operations throw ArgumentException with clear error messages.
