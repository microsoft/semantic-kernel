# Unity Compatibility for Semantic Kernel

## Status

Implemented

## Context

The Microsoft.Extensions.AI package brings in Microsoft.Bcl.Numerics which conflicts with Unity's built-in math types (Vector2, Vector3, etc.). To make Semantic Kernel compatible with Unity, we need to conditionally exclude Microsoft.Extensions.AI and related code when building for Unity.

## Decision

Use `#if !UNITY` preprocessor guards to exclude Microsoft.Extensions.AI code when the `UNITY` constant is defined. The UNITY constant is automatically defined for `netstandard2.0` builds in the csproj files.

## Implementation

### Pattern for Code Guards

```csharp
#if !UNITY
using Microsoft.Extensions.AI;
#endif

// For properties/methods that use AI types:
#if !UNITY
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
#else
    public object? EmbeddingGenerator { get; set; }
#endif
```

### Pattern for Package References (csproj)

```xml
<PackageReference Include="Microsoft.Extensions.AI" Condition="!$(DefineConstants.Contains('UNITY'))" />
```

### Pattern for File Exclusion (csproj)

For files that cannot be easily guarded (e.g., raw string literals with `##` causing preprocessor issues):

```xml
<ItemGroup Condition="$(DefineConstants.Contains('UNITY'))">
  <Compile Remove="Path\To\File.cs" />
</ItemGroup>
```

## Files Modified

### VectorData.Abstractions

Files with `#if !UNITY` guards for AI types:
- `VectorSearch/IVectorSearchable.cs`
- `VectorSearch/IKeywordHybridSearchable.cs`
- `ProviderServices/CollectionModelBuilder.cs`
- `ProviderServices/CollectionJsonModelBuilder.cs`
- `ProviderServices/VectorPropertyModel.cs`
- `ProviderServices/VectorPropertyModel{TInput}.cs`
- `ProviderServices/VectorDataStrings.cs`
- `RecordDefinition/VectorStoreCollectionDefinition.cs`
- `RecordDefinition/VectorStoreVectorProperty.cs`
- `VectorStorage/VectorStoreCollectionOptions.cs`

### SemanticKernel.Abstractions

Files entirely wrapped with `#if !UNITY`:
- `AI/ChatClient/*.cs` (entire directory)
- `AI/ChatCompletion/AIFunctionKernelFunction.cs`
- `AI/ChatCompletion/ChatClientChatCompletionService.cs`
- `AI/ChatCompletion/ChatCompletionServiceChatClient.cs`
- `Memory/AggregateAIContextProviderExtensions.cs`

Files with partial guards:
- `Functions/KernelFunction.cs` - class inheritance changes, AI-specific methods guarded
- `Functions/KernelArguments.cs` - inherits from `AIFunctionArguments` or `Dictionary`
- `Functions/FunctionResult.cs` - AI type conversions guarded
- `Contents/ChatMessageContentExtensions.cs`
- `Contents/StreamingChatMessageContentExtensions.cs`
- Many others (see git diff for complete list)

### SemanticKernel.Core

Files entirely wrapped with `#if !UNITY`:
- `Memory/Whiteboard/WhiteboardProvider.cs` (excluded via csproj due to `##` preprocessor issue)
- `Functions/ContextualSelection/FunctionStore.cs`
- `Functions/ContextualSelection/FunctionStoreLoggingExtensions.cs`
- `Functions/ContextualSelection/ContextualFunctionProvider.cs`
- `Data/TextSearchBehavior/TextSearchProvider.cs`
- `Memory/Mem0/Mem0Provider.cs`

## Build Command

To build with UNITY compatibility:

```bash
dotnet build --configuration Debug -f netstandard2.0 -p:DefineConstants=UNITY
```

Or for publish:

```bash
dotnet publish --configuration Release -f netstandard2.0 -p:UseAppHost=false -p:DefineConstants=UNITY
```

## Updating After Pulling from Main

When pulling updates from the main fork, new files or changes may introduce Microsoft.Extensions.AI dependencies. To identify and fix them:

1. **Build with UNITY defined:**
   ```bash
   dotnet build src/SemanticKernel.Core -f netstandard2.0 -p:DefineConstants=UNITY
   ```

2. **Look for errors like:**
   - `The type or namespace name 'IEmbeddingGenerator' could not be found`
   - `The type or namespace name 'AIFunction' could not be found`
   - `The type or namespace name 'ChatMessage' could not be found`
   - `The type or namespace name 'Embedding' could not be found`

3. **Apply the appropriate pattern:**
   - For using statements: wrap with `#if !UNITY`
   - For properties/methods using AI types: provide alternative implementation in `#else` block
   - For entire files that only make sense with AI: wrap entire file with `#if !UNITY`
   - For files with preprocessor issues: exclude via csproj

## Key AI Types to Guard

- `IEmbeddingGenerator`, `IEmbeddingGenerator<TInput, TEmbedding>`
- `Embedding`, `Embedding<T>`, `GeneratedEmbeddings<T>`
- `AIFunction`, `AIFunctionArguments`
- `IChatClient`, `ChatMessage`, `ChatCompletion`, `ChatOptions`
- `DataContent`, `AIContent`
- `ChatRole` (from Microsoft.Extensions.AI, not to be confused with SK's AuthorRole)

## Notes

- The `dotnet format` tool runs automatically on Release builds and may make whitespace changes
- Some XML doc comments will show warnings about unresolved cref attributes - this is expected when types are excluded
- The UNITY constant is defined in the csproj for netstandard2.0 builds automatically
