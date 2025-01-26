---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: eavanvalkenburg
date: 2024-12-10
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk, westey-m, eavanvalkenburg, bentho
consulted: 
informed: 
---

# Adding list keys method to VectorStoreRecordCollection interface

The new [vector store design](./0050-updated-vector-store-design.md) has been released, but a few users noticed that a method to list all existing keys is missing. This decision proposes a new method to list all keys in the vector store.

## Context and problem statement

Since we support CRUD operations in our data stores we should also provide a way to keep a collection in sync between our code and the backend database. This is currently not easy since it would required either querying every key to see if it exists or maintaining a separate list of keys in the code. Only when you know which keys are in the database and not in your code can you decide to delete them.

## Decision drivers
1. We want to provide a way to list all keys in the vector store
2. We want to provide this in a non-breaking way
3. 

## Considered Options

- Option #1: add a new method to the VectorStoreRecordCollection interface
- Option #2: add a new method to a new separate interface
- Option #3: alter the behavior of the Get/GetBatch methods to allow getting all records (key=None or similar)

## Option 1: add a new method to the VectorStoreRecordCollection interface

We can add a new method to the VectorStoreRecordCollection interface to list all keys in the vector store. This method will return a list of keys.

```csharp
public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorizedSearch<TRecord>
{
    Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    ...
    Task<IEnumerable<TKey>> ListKeysAsync(CancellationToken cancellationToken = default);
}
```
Pros:
- This is a simple and straightforward way to add the functionality
Cons:
- It is a breaking change (at least for csharp, python can do a default implementation that returns None)

## Option 2: add a new method to a new separate interface

We can add a separate interface to list all keys in the vector store. This method will return a list of keys.

```csharp
public interface IVectorStoreRecordCollectionListKeys<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
{
    Task<IEnumerable<TKey>> ListKeysAsync(CancellationToken cancellationToken = default);
}
```
Pros:
- This is a non-breaking change, each vector store record collection must choose to implement this interface.

Cons:
- This is a more complex way to add the functionality

## Option 3: alter the behavior of the Get/GetBatch methods to allow getting all records (key=None or similar)

This options alters the behavior of the Get methods to allow getting all records, this can be done by passing a special key value (e.g. None) to the Get method.

```csharp

public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorizedSearch<TRecord>
{
    Task<TRecord?> GetAsync(TKey? key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey>? keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}

```
Pros:
- This allows the other options to be used in concert with getting all records
- This is a non-breaking change
Cons:
- This returns the full records instead of just the keys, which can be useful in some cases, but can be overhead in others.
- It is not immediately clear that passing a special key value will return all records, a dedicated method would be more clear.

## Options 3b: alter the behavior of the Get/GetBatch methods to allow getting all keys

This options alters the behavior of the Get methods to allow getting all keys, this can be done by passing a special key value (e.g. None) to the Get method, combined with a change in the GetRecordOptions, to specify Keys only.

```csharp
public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorizedSearch<TRecord>
{
    Task<TRecord?> GetAsync(TKey? key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey>? keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}
public class GetRecordOptions
{
    public bool IncludeVectors { get; init; } = false;
    public bool KeysOnly { get; init; } = false;
}

```
Pros:
- This allows the other options to be used in concert with getting all keys
- This is a non-breaking change
- This allows the user to choose if they want the full records or just the keys
Cons:
- This is a more complex way to add the functionality
- It is not immediately clear that passing a special key value will return all records, a dedicated method would be more clear.

## Naming of the method

In the examples above the term ListKeys is used, but other terms could be used as well, such as GetKeys, Keys, etc. The term ListKeys is chosen because it is clear that this method will return a list of keys.

## Decision
Option 1: add a new method to the VectorStoreRecordCollection interface

This is the cleanest approach, and for Python, the breaking change can be mitigated by providing a default implementation in the interface that returns an empty list.


