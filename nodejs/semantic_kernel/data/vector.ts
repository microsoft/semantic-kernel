import { SearchOptions } from './_shared'

/**
 * Default description for vector search functions.
 */
export const DEFAULT_DESCRIPTION =
  'Perform a vector search for data in a vector store, using the provided search options.'

/**
 * Enumeration for field types in vector store models.
 * @releaseCandidate
 */
export enum FieldTypes {
  KEY = 'key',
  VECTOR = 'vector',
  DATA = 'data',
}

/**
 * Index kinds for similarity search.
 * @releaseCandidate
 */
export enum IndexKind {
  /**
   * Hierarchical Navigable Small World which performs an approximate nearest neighbor (ANN) search.
   */
  HNSW = 'hnsw',
  /**
   * Does a brute force search to find the nearest neighbors.
   */
  Flat = 'flat',
  /**
   * Inverted File with Flat Compression.
   */
  IVFFlat = 'ivf_flat',
  /**
   * Disk-based Approximate Nearest Neighbor algorithm.
   */
  DiskANN = 'disk_ann',
  /**
   * Quantized Flat index.
   */
  QuantizedFlat = 'quantized_flat',
  /**
   * Dynamic index.
   */
  Dynamic = 'dynamic',
  /**
   * Default index type.
   * Used when no index type is specified.
   * Will differ per vector store.
   */
  DEFAULT = 'default',
}

/**
 * Distance functions for similarity search.
 * @releaseCandidate
 */
export enum DistanceFunction {
  /**
   * Cosine similarity.
   */
  CosineSimilarity = 'cosine_similarity',
  /**
   * Cosine distance.
   */
  CosineDistance = 'cosine_distance',
  /**
   * Dot product.
   */
  DotProduct = 'dot_product',
  /**
   * Euclidean distance.
   */
  EuclideanDistance = 'euclidean_distance',
  /**
   * Euclidean squared distance.
   */
  EuclideanSquaredDistance = 'euclidean_squared_distance',
  /**
   * Hamming distance.
   */
  HammingDistance = 'hamming_distance',
  /**
   * Manhattan distance.
   */
  ManhattanDistance = 'manhattan_distance',
  /**
   * Default distance function.
   * Used when no distance function is specified.
   * Will differ per vector store.
   */
  DEFAULT = 'DEFAULT',
}

/**
 * Helper object mapping distance functions to comparison operators.
 *
 * Determines whether higher scores (true = greater than) or lower scores (false = less than or equal)
 * indicate better similarity for each distance function.
 * @releaseCandidate
 */
export const DISTANCE_FUNCTION_DIRECTION_HELPER: Record<DistanceFunction, (a: number, b: number) => boolean> = {
  [DistanceFunction.CosineSimilarity]: (a, b) => a > b,
  [DistanceFunction.CosineDistance]: (a, b) => a <= b,
  [DistanceFunction.DotProduct]: (a, b) => a > b,
  [DistanceFunction.EuclideanDistance]: (a, b) => a <= b,
  [DistanceFunction.EuclideanSquaredDistance]: (a, b) => a <= b,
  [DistanceFunction.HammingDistance]: (a, b) => a <= b,
  [DistanceFunction.ManhattanDistance]: (a, b) => a <= b,
  [DistanceFunction.DEFAULT]: (a, b) => a > b,
}

/**
 * Data model serialization protocol.
 * @releaseCandidate
 */
export interface SerializeMethodProtocol {
  /**
   * Serialize the object to the format required by the data store.
   */
  serialize(kwargs?: Record<string, any>): any
}

/**
 * Protocol for to_dict function.
 * @releaseCandidate
 */
export type ToDictFunctionProtocol = (record: any, kwargs?: Record<string, any>) => Record<string, any>[]

/**
 * Protocol for from_dict function.
 * @releaseCandidate
 */
export type FromDictFunctionProtocol = (records: Record<string, any>[], kwargs?: Record<string, any>) => any

/**
 * Protocol for serialize function.
 * @releaseCandidate
 */
export type SerializeFunctionProtocol = (record: any, kwargs?: Record<string, any>) => any

/**
 * Protocol for deserialize function.
 * @releaseCandidate
 */
export type DeserializeFunctionProtocol = (records: any, kwargs?: Record<string, any>) => any

/**
 * Protocol for to_dict method on models.
 * @releaseCandidate
 */
export interface ToDictMethodProtocol {
  /**
   * Serialize the object to the format required by the data store.
   */
  toDict(...args: any[]): Record<string, any>
}

/**
 * Type variable for model types.
 */
export type TModel = any

/**
 * Type variable for key types.
 */
export type TKey = any

/**
 * Type for one or many items.
 */
export type OneOrMany<T> = T | T[]

/**
 * Vector Store Record Handler class.
 *
 * This class is used to serialize and deserialize records to and from a vector store.
 * As well as validating the data model against the vector store.
 * It is subclassed by VectorStoreRecordCollection and VectorSearchBase.
 *
 * @releaseCandidate
 */
export abstract class VectorStoreRecordHandler<_TKey = any, TModel = any> {
  recordType: new (...args: any[]) => TModel
  definition: VectorStoreCollectionDefinition
  supportedKeyTypes: Set<string> | null = null
  supportedVectorTypes: Set<string> | null = null
  embeddingGenerator: EmbeddingGeneratorBase | null = null

  constructor(params: {
    recordType: new (...args: any[]) => TModel
    definition?: VectorStoreCollectionDefinition | null
    embeddingGenerator?: EmbeddingGeneratorBase | null
  }) {
    this.recordType = params.recordType

    // Ensure there is a data model definition, if it isn't passed, try to get it from the data model type
    this.definition =
      params.definition ??
      (this.recordType as any).__kernel_vectorstoremodel_definition__ ??
      (() => {
        throw new Error('No definition provided and recordType does not have __kernel_vectorstoremodel_definition__')
      })()

    this.embeddingGenerator = params.embeddingGenerator ?? null

    // Post-init: validate the data model
    this._validateDataModel()
  }

  /**
   * Get the key field name.
   */
  get _keyFieldName(): string {
    return this.definition.keyName
  }

  /**
   * Get the key field storage name.
   */
  get _keyFieldStorageName(): string {
    return this.definition.keyField.storageName || this.definition.keyName
  }

  /**
   * Get the container mode.
   */
  get _containerMode(): boolean {
    return this.definition.containerMode
  }

  /**
   * Internal function that can be overloaded by child classes to validate datatypes, etc.
   *
   * This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.
   *
   * Checks can include, allowed naming of parameters, allowed data types, allowed vector dimensions.
   *
   * Default checks are that the key field is in the allowed key types and the vector fields
   * are in the allowed vector types.
   *
   * @throws Error if the key field is not in the allowed key types.
   * @throws Error if the vector fields are not in the allowed vector types.
   */
  protected _validateDataModel(): void {
    if (
      this.supportedKeyTypes &&
      this.definition.keyField.type_ &&
      !this.supportedKeyTypes.has(this.definition.keyField.type_)
    ) {
      throw new Error(
        `Key field must be one of ${Array.from(this.supportedKeyTypes).join(', ')}, got ${this.definition.keyField.type_}`
      )
    }
    if (!this.supportedVectorTypes) {
      return
    }
    for (const field of this.definition.vectorFields) {
      if (field.type_ && !this.supportedVectorTypes.has(field.type_)) {
        throw new Error(
          `Vector field ${field.name} must be one of ${Array.from(this.supportedVectorTypes).join(', ')}, got ${field.type_}`
        )
      }
    }
  }

  /**
   * Serialize a list of dicts of the data to the store model.
   *
   * This method should be overridden by the child class to convert the dict to the store model.
   */
  protected abstract _serializeDictsToStoreModels(
    records: Array<Record<string, any>>,
    kwargs?: Record<string, any>
  ): any[]

  /**
   * Deserialize the store models to a list of dicts.
   *
   * This method should be overridden by the child class to convert the store model to a list of dicts.
   */
  protected abstract _deserializeStoreModelsToDicts(
    records: any[],
    kwargs?: Record<string, any>
  ): Array<Record<string, any>>

  /**
   * Serialize the data model to the store model.
   *
   * This method follows the following steps:
   * 1. Check if the data model has a serialize method.
   *    Use that method to serialize and return the result.
   * 2. Serialize the records into a dict, using the data model specific method.
   * 3. Convert the dict to the store model, using the store specific method.
   *
   * If overriding this method, make sure to first try to serialize the data model to the store model,
   * before doing the store specific version,
   * the user supplied version should have precedence.
   *
   * @throws Error if an error occurs during serialization.
   */
  async serialize(records: OneOrMany<TModel>, kwargs?: Record<string, any>): Promise<OneOrMany<any>> {
    try {
      const serialized = this._serializeDataModelToStoreModel(records, kwargs)
      if (serialized !== null) {
        return serialized
      }
    } catch (error) {
      throw new Error('Error serializing records', { cause: error })
    }

    let dictRecords: Array<Record<string, any>> = []
    try {
      const recordsArray = Array.isArray(records) ? records : [records]
      for (const rec of recordsArray) {
        const dictRec = this._serializeDataModelToDict(rec, kwargs)
        if (Array.isArray(dictRec)) {
          dictRecords.push(...dictRec)
        } else {
          dictRecords.push(dictRec)
        }
      }
    } catch (error) {
      throw new Error('Error serializing records', { cause: error })
    }

    // Add vectors
    try {
      dictRecords = await this._addVectorsToRecords(dictRecords)
    } catch (error) {
      throw new Error('Exception occurred while trying to add the vectors to the records', { cause: error })
    }

    try {
      return this._serializeDictsToStoreModels(dictRecords, kwargs)
    } catch (error) {
      throw new Error('Error serializing records', { cause: error })
    }
  }

  /**
   * Serialize the data model to the store model.
   *
   * This works when the data model has supplied a serialize method, specific to a data source.
   * This is a method called 'serialize()' on the data model or part of the vector store record definition.
   *
   * The developer is responsible for correctly serializing for the specific data source.
   */
  protected _serializeDataModelToStoreModel(
    record: OneOrMany<TModel>,
    kwargs?: Record<string, any>
  ): OneOrMany<any> | null {
    if (Array.isArray(record)) {
      const result = record.map((rec) => this._serializeDataModelToStoreModel(rec, kwargs))
      if (!result.every((r) => r !== null)) {
        return null
      }
      return result
    }
    if (this.definition.serialize) {
      return this.definition.serialize(record, kwargs)
    }
    if (typeof (record as any).serialize === 'function') {
      return (record as any).serialize(kwargs)
    }
    return null
  }

  /**
   * This function is used if no serialize method is found on the data model.
   *
   * This will generally serialize the data model to a dict, should not be overridden by child classes.
   *
   * The output of this should be passed to the serialize_dict_to_store_model method.
   */
  protected _serializeDataModelToDict(
    record: TModel,
    kwargs?: Record<string, any>
  ): Record<string, any> | Array<Record<string, any>> {
    if (this.definition.toDict) {
      return this.definition.toDict(record, kwargs)
    }

    const storeModel: Record<string, any> = {}
    for (const field of this.definition.fields) {
      const key = field.storageName || field.name
      storeModel[key] =
        typeof (record as any).get === 'function' ? (record as any).get(field.name, null) : (record as any)[field.name]
    }
    return storeModel
  }

  /**
   * Deserialize the store model to the data model.
   *
   * This method follows the following steps:
   * 1. Check if the data model has a deserialize method.
   *    Use that method to deserialize and return the result.
   * 2. Deserialize the store model to a dict, using the store specific method.
   * 3. Convert the dict to the data model, using the data model specific method.
   *
   * @throws Error if an error occurs during deserialization.
   */
  deserialize(records: OneOrMany<any | Record<string, any>>, kwargs?: Record<string, any>): OneOrMany<TModel> | null {
    try {
      if (!records) {
        return null
      }
      const deserialized = this._deserializeStoreModelToDataModel(records, kwargs)
      if (deserialized !== null) {
        return deserialized
      }

      if (Array.isArray(records)) {
        const dictRecords = this._deserializeStoreModelsToDicts(records, kwargs)
        return this._containerMode
          ? this._deserializeDictToDataModel(dictRecords, kwargs)
          : dictRecords.map((rec) => this._deserializeDictToDataModel(rec, kwargs))
      }

      const dictRecord = this._deserializeStoreModelsToDicts([records], kwargs)[0]
      // regardless of mode, only 1 object is returned.
      return this._deserializeDictToDataModel(dictRecord, kwargs)
    } catch (error) {
      throw new Error('Error deserializing records', { cause: error })
    }
  }

  /**
   * Deserialize the store model to the data model.
   *
   * This works when the data model has supplied a deserialize method, specific to a data source.
   * This uses a method called 'deserialize()' on the data model or part of the vector store record definition.
   *
   * The developer is responsible for correctly deserializing for the specific data source.
   */
  protected _deserializeStoreModelToDataModel(
    record: OneOrMany<any>,
    kwargs?: Record<string, any>
  ): OneOrMany<TModel> | null {
    if (this.definition.deserialize) {
      if (Array.isArray(record)) {
        return this.definition.deserialize(record, kwargs)
      }
      return this.definition.deserialize([record], kwargs)
    }
    const func = (this.recordType as any).deserialize
    if (func) {
      if (Array.isArray(record)) {
        return record.map((rec) => func(rec, kwargs))
      }
      return func(record, kwargs)
    }
    return null
  }

  /**
   * This function is used if no deserialize method is found on the data model.
   *
   * This method is the second step and will deserialize a dict to the data model,
   * should not be overridden by child classes.
   *
   * The input of this should come from the _deserialized_store_model_to_dict function.
   */
  protected _deserializeDictToDataModel(record: OneOrMany<Record<string, any>>, kwargs?: Record<string, any>): TModel {
    if (this.definition.fromDict) {
      if (Array.isArray(record)) {
        return this.definition.fromDict(record, kwargs)
      }
      const ret = this.definition.fromDict([record], kwargs)
      return this._containerMode ? ret : ret[0]
    }

    let recordObj: Record<string, any> = record as Record<string, any>
    if (Array.isArray(record)) {
      if (record.length > 1) {
        throw new Error('Cannot deserialize multiple records to a single record unless you are using a container.')
      }
      recordObj = record[0]
    }

    const func = (this.recordType as any).from_dict
    if (func) {
      return func(recordObj)
    }

    // Handle storage name mapping
    for (const field of this.definition.fields) {
      if (field.storageName && field.storageName in recordObj) {
        recordObj[field.name] = recordObj[field.storageName]
        delete recordObj[field.storageName]
      }
    }

    const dataModelDict: Record<string, any> = {}
    for (const field of this.definition.fields) {
      const value = recordObj[field.storageName || field.name]
      if (field.fieldType === FieldTypes.VECTOR && !kwargs?.include_vectors) {
        continue
      }
      dataModelDict[field.name] = value ?? null
    }

    if (this.recordType === (Object as any) || this.recordType === (Object as any).constructor) {
      return dataModelDict as TModel
    }
    return new this.recordType(dataModelDict)
  }

  /**
   * Vectorize the vector record.
   *
   * This function can be passed to upsert or upsert batch of a VectorStoreRecordCollection.
   *
   * Loops through the fields of the data model definition,
   * looks at data fields, if they have a vector field,
   * looks up that vector field and checks if is a local embedding.
   *
   * If so adds that to a list of embeddings to make.
   *
   * Finally calls Kernel add_embedding_to_object with the list of embeddings to make.
   *
   * Optional arguments are passed onto the Kernel add_embedding_to_object call.
   */
  protected async _addVectorsToRecords(records: OneOrMany<Record<string, any>>): Promise<Array<Record<string, any>>> {
    // List of tuples: [field_name, dimensions, embedding_generator]
    const embeddingsToMake: Array<[string, number, EmbeddingGeneratorBase]> = []

    for (const field of this.definition.vectorFields) {
      const embeddingGenerator = field.embeddingGenerator || this.embeddingGenerator
      if (!embeddingGenerator) {
        continue
      }
      if (field.dimensions === null) {
        throw new Error(`Field ${field.name} has no dimensions, cannot create embedding for field.`)
      }
      embeddingsToMake.push([field.storageName || field.name, field.dimensions, embeddingGenerator])
    }

    const recordsArray = Array.isArray(records) ? records : [records]

    for (const [fieldName, dimensions, embedder] of embeddingsToMake) {
      await this._addEmbeddingToObject(recordsArray, fieldName, dimensions, embedder)
    }

    return recordsArray
  }

  /**
   * Gather all fields to embed, batch the embedding generation and store.
   */
  protected async _addEmbeddingToObject(
    inputs: Array<any>,
    fieldName: string,
    dimensions: number,
    embeddingGenerator: EmbeddingGeneratorBase
  ): Promise<void> {
    const contents: any[] = []

    for (const record of inputs) {
      if (typeof record.get === 'function') {
        contents.push(record.get(fieldName))
      } else {
        contents.push(record[fieldName])
      }
    }

    const vectors = await embeddingGenerator.generateRawEmbeddings(contents, { dimensions })
    if (!vectors) {
      throw new Error('No vectors were generated.')
    }

    for (let i = 0; i < inputs.length; i++) {
      const record = inputs[i]
      if (typeof record.set === 'function') {
        record.set(fieldName, vectors[i])
      } else {
        record[fieldName] = vectors[i]
      }
    }
  }
}

/**
 * Forward declaration for VectorStoreCollection.
 */

/**
 * Base class for a vector store record collection.
 * @releaseCandidate
 */
export abstract class VectorStoreCollection<TKey = any, TModel = any> extends VectorStoreRecordHandler<TKey, TModel> {
  collectionName: string = ''
  managedClient: boolean = true

  constructor(params: {
    recordType: new (...args: any[]) => TModel
    collectionName?: string | null
    definition?: VectorStoreCollectionDefinition | null
    embeddingGenerator?: EmbeddingGeneratorBase | null
    managedClient?: boolean
  }) {
    super({
      recordType: params.recordType,
      definition: params.definition ?? null,
      embeddingGenerator: params.embeddingGenerator,
    })

    // Ensure there is a collection name
    this.collectionName = params.collectionName ?? this._getCollectionNameFromModel() ?? ''
    this.managedClient = params.managedClient ?? true
  }

  /**
   * Get collection name from the model type if available.
   */
  private _getCollectionNameFromModel(): string | null {
    return (this.recordType as any).__kernel_vectorstoremodel_collection_name__ ?? null
  }

  /**
   * Enter the context manager.
   */
  async __aenter__(): Promise<this> {
    return this
  }

  /**
   * Exit the context manager.
   *
   * Should be overridden by subclasses, if necessary.
   *
   * If the client is passed in the constructor, it should not be closed,
   * in that case the managed_client should be set to false.
   *
   * If the store supplied the managed client, it is responsible for closing it,
   * and it should not be closed here and so managed_client should be false.
   *
   * Some services use two clients, one for the store and one for the collection,
   * in that case, the collection client should be closed here,
   * but the store client should only be closed when it is created in the collection.
   * A additional flag might be needed for that.
   */
  async __aexit__(_excType?: any, _excValue?: any, _traceback?: any): Promise<void> {
    // Default implementation does nothing
  }

  /**
   * Upsert the records, this should be overridden by the child class.
   *
   * @param records - The records, the format is specific to the store.
   * @param kwargs - Additional arguments, to be passed to the store.
   * @returns The keys of the upserted records.
   * @throws Error if an error occurs during the upsert.
   */
  protected abstract _innerUpsert(records: any[], kwargs?: Record<string, any>): Promise<TKey[]>

  /**
   * Get the records, this should be overridden by the child class.
   *
   * @param keys - The keys to get.
   * @param options - The options to use for the get.
   * @param kwargs - Additional arguments.
   * @returns The records from the store, not deserialized.
   * @throws Error if an error occurs during the get.
   */
  protected abstract _innerGet(
    keys?: TKey[] | null,
    options?: GetFilteredRecordOptions | null,
    kwargs?: Record<string, any>
  ): Promise<OneOrMany<any> | null>

  /**
   * Delete the records, this should be overridden by the child class.
   *
   * @param keys - The keys.
   * @param kwargs - Additional arguments.
   * @throws Error if an error occurs during the delete.
   */
  protected abstract _innerDelete(keys: TKey[], kwargs?: Record<string, any>): Promise<void>

  /**
   * Create the collection in the service.
   *
   * This should be overridden by the child class. Should first check if the collection exists,
   * if it does not, it should create the collection.
   *
   * @throws Error with good description.
   */
  abstract ensureCollectionExists(kwargs?: Record<string, any>): Promise<void>

  /**
   * Check if the collection exists.
   *
   * This should be overridden by the child class.
   *
   * @throws Error with good description.
   */
  abstract collectionExists(kwargs?: Record<string, any>): Promise<boolean>

  /**
   * Delete the collection.
   *
   * This should be overridden by the child class.
   *
   * @throws Error with good description.
   */
  abstract ensureCollectionDeleted(kwargs?: Record<string, any>): Promise<void>

  /**
   * Upsert one or more records.
   *
   * If the key of the record already exists, the existing record will be updated.
   * If the key does not exist, a new record will be created.
   *
   * @param records - The records to upsert, can be a single record, a list of records, or a single container.
   *                  If a single record is passed, a single key is returned, instead of a list of keys.
   * @param kwargs - Additional arguments.
   * @returns The keys of the upserted records.
   * @throws Error if an error occurs during serialization or upserting.
   */
  async upsert(records: OneOrMany<TModel>, kwargs?: Record<string, any>): Promise<OneOrMany<TKey>> {
    const batch = Array.isArray(records) || this._containerMode

    if (records === null || records === undefined) {
      throw new Error('Either record or records must be provided.')
    }

    let data: any
    try {
      data = await this.serialize(records)
    } catch (error) {
      throw new Error('Error serializing records', { cause: error })
    }

    let results: TKey[]
    try {
      results = await this._innerUpsert(Array.isArray(data) ? data : [data], kwargs)
    } catch (error) {
      throw new Error(`Error upserting record(s) into collection '${this.collectionName}'`, { cause: error })
    }

    if (batch || this._containerMode) {
      return results
    }
    return results[0]
  }

  /**
   * Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.
   *
   * @param params - Get parameters
   * @param params.key - The key to get (single record)
   * @param params.keys - The keys to get (batch)
   * @param params.includeVectors - Include the vectors in the response. Default is false.
   * @param params.top - The number of records to return (when using filter)
   * @param params.skip - The number of records to skip (when using filter)
   * @param params.orderBy - The order by clause
   * @param kwargs - Additional arguments.
   * @returns The records, either a list of TModel or the container type.
   * @throws Error if an error occurs during the get or deserialization.
   */
  async get(
    params?: {
      key?: TKey
      keys?: TKey[]
      includeVectors?: boolean
      top?: number
      skip?: number
      orderBy?: string | string[] | Record<string, boolean>
    },
    kwargs?: Record<string, any>
  ): Promise<OneOrMany<TModel> | null> {
    let batch = true
    let options: GetFilteredRecordOptions | null = null
    let keys: TKey[] | undefined

    const includeVectors = params?.includeVectors ?? false

    // Determine keys
    if (params?.keys) {
      keys = params.keys
    } else if (params?.key !== undefined) {
      if (!Array.isArray(params.key)) {
        keys = [params.key]
        batch = false
      } else {
        keys = params.key
      }
    }

    // If no keys, check for filter options
    if (!keys) {
      if (params && (params.top !== undefined || params.skip !== undefined || params.orderBy !== undefined)) {
        const getArgs: { top?: number; skip?: number; orderBy?: Map<string, boolean> } = {}

        if (params.top !== undefined) {
          getArgs.top = params.top
        }
        if (params.skip !== undefined) {
          getArgs.skip = params.skip
        }

        if (params.orderBy !== undefined) {
          const orderBy = new Map<string, boolean>()
          if (typeof params.orderBy === 'string') {
            orderBy.set(params.orderBy, true)
          } else if (Array.isArray(params.orderBy)) {
            for (const item of params.orderBy) {
              if (typeof item === 'string') {
                orderBy.set(item, true)
              } else {
                for (const [key, value] of Object.entries(item)) {
                  orderBy.set(key, value as boolean)
                }
              }
            }
          } else {
            for (const [key, value] of Object.entries(params.orderBy)) {
              orderBy.set(key, value as boolean)
            }
          }
          getArgs.orderBy = orderBy
        }

        try {
          options = new GetFilteredRecordOptions(getArgs)
        } catch (error) {
          throw new Error('Error creating options', { cause: error })
        }
      } else {
        throw new Error('Either key, keys or options must be provided.')
      }
    }

    let records: OneOrMany<any> | null
    try {
      records = await this._innerGet(keys, options, { ...kwargs, includeVectors })
    } catch (error) {
      throw new Error('Error getting record(s)', { cause: error })
    }

    if (!records) {
      return null
    }

    let modelRecords: OneOrMany<TModel> | null
    try {
      modelRecords = this.deserialize(batch ? records : Array.isArray(records) ? records[0] : records, {
        ...kwargs,
        include_vectors: includeVectors,
      })
    } catch (error) {
      throw new Error('Error deserializing records', { cause: error })
    }

    if (batch) {
      return modelRecords
    }
    if (!Array.isArray(modelRecords)) {
      return modelRecords
    }
    if (modelRecords.length === 1) {
      return modelRecords[0]
    }
    throw new Error('Error deserializing record, multiple records returned', { cause: modelRecords })
  }

  /**
   * Delete one or more records by key.
   *
   * An exception will be raised at the end if any record does not exist.
   *
   * @param keys - The key or keys to be deleted.
   * @param kwargs - Additional arguments.
   * @throws Error if an error occurs during deletion or a record does not exist.
   */
  async delete(keys: OneOrMany<TKey>, kwargs?: Record<string, any>): Promise<void> {
    const keysArray = Array.isArray(keys) ? keys : [keys]
    try {
      await this._innerDelete(keysArray, kwargs)
    } catch (error) {
      throw new Error('Error deleting record(s)', { cause: error })
    }
  }
}

/**
 * Collection definition for vector stores.
 * @releaseCandidate
 */
export class VectorStoreCollectionDefinition {
  fields: VectorStoreField[]
  keyName: string = ''
  containerMode: boolean = false
  collectionName: string | null = null
  toDict: ToDictFunctionProtocol | null = null
  fromDict: FromDictFunctionProtocol | null = null
  serialize: SerializeFunctionProtocol | null = null
  deserialize: DeserializeFunctionProtocol | null = null

  constructor(params: {
    fields: VectorStoreField[]
    containerMode?: boolean
    collectionName?: string | null
    toDict?: ToDictFunctionProtocol | null
    fromDict?: FromDictFunctionProtocol | null
    serialize?: SerializeFunctionProtocol | null
    deserialize?: DeserializeFunctionProtocol | null
  }) {
    this.fields = params.fields
    this.containerMode = params.containerMode ?? false
    this.collectionName = params.collectionName ?? null
    this.toDict = params.toDict ?? null
    this.fromDict = params.fromDict ?? null
    this.serialize = params.serialize ?? null
    this.deserialize = params.deserialize ?? null

    // Validate and set key name
    this.validate()
  }

  /**
   * Get the names of the fields.
   */
  get names(): string[] {
    return this.fields.map((field) => field.name)
  }

  /**
   * Get the names of the fields for storage.
   */
  get storageNames(): string[] {
    return this.fields.map((field) => field.storageName || field.name)
  }

  /**
   * Get the key field.
   */
  get keyField(): VectorStoreField {
    const field = this.fields.find((f) => f.name === this.keyName)
    if (!field) {
      throw new Error(`Key field ${this.keyName} not found`)
    }
    return field
  }

  /**
   * Get the key field storage name.
   */
  get keyFieldStorageName(): string {
    return this.keyField.storageName || this.keyField.name
  }

  /**
   * Get the vector fields.
   */
  get vectorFields(): VectorStoreField[] {
    return this.fields.filter((field) => field.fieldType === FieldTypes.VECTOR)
  }

  /**
   * Get the data fields.
   */
  get dataFields(): VectorStoreField[] {
    return this.fields.filter((field) => field.fieldType === FieldTypes.DATA)
  }

  /**
   * Get the names of the vector fields.
   */
  get vectorFieldNames(): string[] {
    return this.fields.filter((field) => field.fieldType === FieldTypes.VECTOR).map((field) => field.name)
  }

  /**
   * Get the names of all the data fields.
   */
  get dataFieldNames(): string[] {
    return this.fields.filter((field) => field.fieldType === FieldTypes.DATA).map((field) => field.name)
  }

  /**
   * Try to get the vector field.
   *
   * If the field_name is null, then the first vector field is returned.
   * If no vector fields are present null is returned.
   *
   * @param fieldName - The field name.
   * @returns The vector field or null.
   */
  tryGetVectorField(fieldName: string | null = null): VectorStoreField | null {
    if (fieldName === null) {
      if (this.vectorFields.length === 0) {
        return null
      }
      return this.vectorFields[0]
    }
    for (const field of this.fields) {
      if (field.name === fieldName || field.storageName === fieldName) {
        if (field.fieldType === FieldTypes.VECTOR) {
          return field
        }
        throw new Error(`Field ${fieldName} is not a vector field, it is of type ${field.fieldType}.`)
      }
    }
    throw new Error(`Field ${fieldName} not found.`)
  }

  /**
   * Get the names of the fields for the storage.
   *
   * @param includeVectorFields - Whether to include vector fields.
   * @param includeKeyField - Whether to include the key field.
   * @returns The names of the fields.
   */
  getStorageNames(includeVectorFields: boolean = true, includeKeyField: boolean = true): string[] {
    return this.fields
      .filter(
        (field) =>
          field.fieldType === FieldTypes.DATA ||
          (field.fieldType === FieldTypes.VECTOR && includeVectorFields) ||
          (field.fieldType === FieldTypes.KEY && includeKeyField)
      )
      .map((field) => field.storageName || field.name)
  }

  /**
   * Get the names of the fields.
   *
   * @param includeVectorFields - Whether to include vector fields.
   * @param includeKeyField - Whether to include the key field.
   * @returns The names of the fields.
   */
  getNames(includeVectorFields: boolean = true, includeKeyField: boolean = true): string[] {
    return this.fields
      .filter(
        (field) =>
          field.fieldType === FieldTypes.DATA ||
          (field.fieldType === FieldTypes.VECTOR && includeVectorFields) ||
          (field.fieldType === FieldTypes.KEY && includeKeyField)
      )
      .map((field) => field.name)
  }

  /**
   * Validate the fields.
   *
   * @throws Error if validation fails.
   */
  private validate(): void {
    if (this.fields.length === 0) {
      throw new Error('There must be at least one field with a VectorStoreRecordField annotation.')
    }
    for (const field of this.fields) {
      if (!field.name || field.name === '') {
        throw new Error('Field names must not be empty.')
      }
      if (field.fieldType === FieldTypes.KEY) {
        if (this.keyName !== '') {
          throw new Error('Memory record definition must have exactly one key field.')
        }
        this.keyName = field.name
      }
    }
    if (!this.keyName) {
      throw new Error('Memory record definition must have exactly one key field.')
    }
  }
}

/**
 * Embedding generator base interface.
 */
export interface EmbeddingGeneratorBase {
  generateRawEmbeddings(texts: string[], settings?: any, ...kwargs: any[]): Promise<number[][]>
}

/**
 * Vector store field options for key fields.
 */
export interface VectorStoreKeyFieldOptions {
  fieldType?: FieldTypes.KEY | 'key'
  name?: string
  type?: string | null
  storageName?: string | null
}

/**
 * Vector store field options for data fields.
 */
export interface VectorStoreDataFieldOptions {
  fieldType?: FieldTypes.DATA | 'data'
  name?: string
  type?: string | null
  storageName?: string | null
  isIndexed?: boolean | null
  isFullTextIndexed?: boolean | null
}

/**
 * Vector store field options for vector fields.
 */
export interface VectorStoreVectorFieldOptions {
  fieldType?: FieldTypes.VECTOR | 'vector'
  name?: string
  type?: string | null
  dimensions: number
  storageName?: string | null
  indexKind?: IndexKind | null
  distanceFunction?: DistanceFunction | null
  embeddingGenerator?: EmbeddingGeneratorBase | null
}

/**
 * Vector store field.
 * @releaseCandidate
 */
export class VectorStoreField {
  fieldType: FieldTypes
  name: string = ''
  storageName: string | null = null
  type_: string | null = null
  // data specific fields (all optional)
  isIndexed: boolean | null = null
  isFullTextIndexed: boolean | null = null
  // vector specific fields (dimensions is mandatory for vector types)
  dimensions: number | null = null
  embeddingGenerator: EmbeddingGeneratorBase | null = null
  // defaults for these fields are not set here, because they are not relevant for data and key types
  indexKind: IndexKind | null = null
  distanceFunction: DistanceFunction | null = null

  /**
   * Creates a key field of the record.
   * When the key will be auto-generated by the store, make sure it has a default, usually null.
   */
  constructor(options: VectorStoreKeyFieldOptions)
  /**
   * Creates a data field in the record.
   */
  constructor(options: VectorStoreDataFieldOptions)
  /**
   * Creates a vector field in the record.
   *
   * This field should contain the value you want to use for the vector.
   * When passing in the embedding generator, the embedding will be
   * generated locally before upserting.
   * If this is not set, the store should support generating the embedding for you.
   * If you want to retrieve the original content of the vector,
   * make sure to set this field twice,
   * once with the VectorStoreRecordDataField and once with the VectorStoreRecordVectorField.
   */
  constructor(options: VectorStoreVectorFieldOptions)
  constructor(
    options: VectorStoreKeyFieldOptions | VectorStoreDataFieldOptions | VectorStoreVectorFieldOptions = {
      fieldType: FieldTypes.DATA,
    }
  ) {
    // Normalize field_type to FieldTypes enum
    const fieldTypeValue = options.fieldType ?? FieldTypes.DATA
    this.fieldType =
      typeof fieldTypeValue === 'string'
        ? FieldTypes[fieldTypeValue.toUpperCase() as keyof typeof FieldTypes]
        : fieldTypeValue

    // Set common properties
    if (options.name) {
      this.name = options.name
    }
    this.storageName = options.storageName ?? null
    this.type_ = options.type ?? null

    // Set data-specific properties
    if ('isIndexed' in options) {
      this.isIndexed = options.isIndexed ?? null
    }
    if ('isFullTextIndexed' in options) {
      this.isFullTextIndexed = options.isFullTextIndexed ?? null
    }

    // Set vector-specific properties
    if (this.fieldType === FieldTypes.VECTOR) {
      if (!('dimensions' in options) || options.dimensions === undefined) {
        throw new Error("Vector fields must specify 'dimensions'")
      }
      this.dimensions = options.dimensions
      this.indexKind = ('indexKind' in options ? options.indexKind : null) ?? IndexKind.DEFAULT
      this.distanceFunction =
        ('distanceFunction' in options ? options.distanceFunction : null) ?? DistanceFunction.DEFAULT
      this.embeddingGenerator = ('embeddingGenerator' in options ? options.embeddingGenerator : null) ?? null
    }
  }
}

/**
 * Base class for vector stores.
 * @releaseCandidate
 */
export abstract class VectorStore {
  /**
   * Whether the client is managed by this instance.
   */
  managedClient: boolean = true

  /**
   * The embedding generator to use.
   */
  embeddingGenerator?: EmbeddingGeneratorBase | null = null

  constructor(params?: { managedClient?: boolean; embeddingGenerator?: EmbeddingGeneratorBase | null }) {
    if (params) {
      if (params.managedClient !== undefined) {
        this.managedClient = params.managedClient
      }
      if (params.embeddingGenerator !== undefined) {
        this.embeddingGenerator = params.embeddingGenerator
      }
    }
  }

  /**
   * Get a vector store record collection instance tied to this store.
   * @param params - The parameters
   * @param params.recordType - The type of the records that will be used
   * @param params.definition - The data model definition
   * @param params.collectionName - The name of the collection
   * @param params.embeddingGenerator - The embedding generator to use
   * @param params.kwargs - Additional arguments
   * @returns A vector store record collection instance tied to this store
   */
  abstract getCollection<TKey = any, TModel = any>(params: {
    recordType: new (...args: any[]) => TModel
    definition?: VectorStoreCollectionDefinition | null
    collectionName?: string | null
    embeddingGenerator?: EmbeddingGeneratorBase | null
    [key: string]: any
  }): VectorStoreCollection<TKey, TModel>

  /**
   * Get the names of all collections.
   * @param kwargs - Additional arguments
   * @returns The names of all collections
   */
  abstract listCollectionNames(kwargs?: Record<string, any>): Promise<string[]>

  /**
   * Check if a collection exists.
   *
   * This is a wrapper around the get_collection method of a collection,
   * to check if the collection exists.
   * @param collectionName - The name of the collection
   * @returns True if the collection exists, false otherwise
   */
  async collectionExists(collectionName: string): Promise<boolean> {
    try {
      const dataModel = new VectorStoreCollectionDefinition({
        fields: [
          new VectorStoreField({
            fieldType: FieldTypes.KEY,
            name: 'id',
          }),
        ],
      })
      const collection = this.getCollection({
        recordType: Object as any,
        definition: dataModel,
        collectionName,
      })
      return await collection.collectionExists()
    } catch {
      return false
    }
  }

  /**
   * Delete a collection.
   *
   * This is a wrapper around the get_collection method of a collection,
   * to delete the collection.
   * @param collectionName - The name of the collection
   */
  async ensureCollectionDeleted(collectionName: string): Promise<void> {
    try {
      const dataModel = new VectorStoreCollectionDefinition({
        fields: [
          new VectorStoreField({
            fieldType: FieldTypes.KEY,
            name: 'id',
          }),
        ],
      })
      const collection = this.getCollection({
        recordType: Object as any,
        definition: dataModel,
        collectionName,
      })
      await collection.ensureCollectionDeleted()
    } catch {
      // Ignore errors
    }
  }

  /**
   * Enter the context manager (for async with support).
   * @returns This instance
   */
  async __aenter__(): Promise<this> {
    return this
  }

  /**
   * Exit the context manager.
   *
   * Should be overridden by subclasses, if necessary.
   *
   * If the client is passed in the constructor, it should not be closed,
   * in that case the managed_client should be set to false.
   */
  async __aexit__(_excType?: any, _excValue?: any, _traceback?: any): Promise<void> {
    // Default implementation does nothing
  }
}

/**
 * Options for filtering records.
 * @releaseCandidate
 */
export class GetFilteredRecordOptions {
  /**
   * The maximum number of records to return.
   */
  top: number = 10

  /**
   * The number of records to skip.
   */
  skip: number = 0

  /**
   * A map with field names and a boolean.
   * True means ascending, False means descending.
   */
  orderBy: Map<string, boolean> | null = null

  constructor(params?: { top?: number; skip?: number; orderBy?: Map<string, boolean> | null }) {
    if (params) {
      if (params.top !== undefined) {
        this.top = params.top
      }
      if (params.skip !== undefined) {
        this.skip = params.skip
      }
      if (params.orderBy !== undefined) {
        this.orderBy = params.orderBy
      }
    }
  }
}

/**
 * Type variable for filter types.
 */
export type TFilters = any

/**
 * Visitor class to visit AST nodes for lambda expressions.
 *
 * Note: This is a simplified TypeScript implementation. The Python version uses Python's built-in
 * AST module to parse lambda expressions. In TypeScript/JavaScript, you would typically need to use
 * a JavaScript parser library (like acorn, esprima, or @babel/parser) to achieve similar functionality,
 * or use string-based filter expressions instead of actual lambda functions.
 *
 * @releaseCandidate
 */
export class LambdaVisitor<TFilters = any> {
  lambdaParser: (node: any) => TFilters
  outputFilters: TFilters[]

  /**
   * Initialize the visitor with a lambda parser and output filters.
   *
   * @param lambdaParser - Function to parse AST nodes into filter objects
   * @param outputFilters - Optional initial list of filters
   */
  constructor(lambdaParser: (node: any) => TFilters, outputFilters?: TFilters[] | null) {
    this.lambdaParser = lambdaParser
    this.outputFilters = outputFilters ?? []
  }

  /**
   * Visit a lambda/arrow function node.
   *
   * This method is called when a lambda expression is found.
   * In a full implementation, this would be called by an AST walker.
   *
   * @param node - The AST node representing the lambda function body
   */
  visitLambda(node: any): void {
    this.outputFilters.push(this.lambdaParser(node))
  }

  /**
   * Visit an AST tree.
   *
   * This is a simplified version. In Python, this would use the ast.NodeVisitor.visit() method
   * to walk the entire AST tree. In TypeScript, you would need to use a JavaScript parser
   * to get the AST first.
   *
   * @param tree - The AST tree to visit
   */
  visit(tree: any): void {
    // In a full implementation, this would recursively walk the AST
    // For now, this is a placeholder that assumes the tree has already been parsed
    if (tree && typeof tree === 'object') {
      // Check if this is a lambda/arrow function node
      // The exact structure depends on the parser used (acorn, babel, etc.)
      if (tree.type === 'ArrowFunctionExpression' || tree.type === 'FunctionExpression') {
        this.visitLambda(tree.body)
      } else if (tree.body) {
        // Recursively visit nested structures
        this.visit(tree.body)
      }
    }
  }
}

/**
 * Enumeration for search types.
 * @releaseCandidate
 */
export enum SearchType {
  /**
   * Vector search type.
   */
  VECTOR = 'vector',
  /**
   * Keyword hybrid search type.
   */
  KEYWORD_HYBRID = 'keyword_hybrid',
}

/**
 * Options for vector search, builds on SearchOptions.
 *
 * When multiple filters are used, they are combined with an AND operator.
 * @releaseCandidate
 */
export class VectorSearchOptions extends SearchOptions {
  vectorPropertyName: string | null = null
  additionalPropertyName: string | null = null
  includeVectors: boolean = false

  constructor(params?: {
    filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
    skip?: number
    top?: number
    includeTotalCount?: boolean
    vectorPropertyName?: string | null
    additionalPropertyName?: string | null
    includeVectors?: boolean
    [key: string]: any
  }) {
    super(params)
    if (params) {
      if (params.vectorPropertyName !== undefined) {
        this.vectorPropertyName = params.vectorPropertyName
      }
      if (params.additionalPropertyName !== undefined) {
        this.additionalPropertyName = params.additionalPropertyName
      }
      if (params.includeVectors !== undefined) {
        this.includeVectors = params.includeVectors
      }
    }
  }
}

/**
 * The result of a vector search.
 * @releaseCandidate
 */
export class VectorSearchResult<TModel = any> {
  record: TModel
  score: number | null = null

  constructor(params: { record: TModel; score?: number | null }) {
    this.record = params.record
    this.score = params.score ?? null
  }
}

/**
 * Base class for searching vectors.
 * @releaseCandidate
 */
export abstract class VectorSearch<TKey = any, TModel = any> extends VectorStoreRecordHandler<TKey, TModel> {
  supportedSearchTypes: Set<SearchType> = new Set()

  /**
   * The options class for the search.
   */
  get optionsClass(): typeof SearchOptions {
    return VectorSearchOptions
  }

  /**
   * Inner search method.
   *
   * This is the main search method that should be implemented, and will be called by the public search methods.
   * Currently, at least one of the three search contents will be provided
   * (through the public interface mixin functions), in the future, this may be expanded to allow multiple of them.
   *
   * This method should return a KernelSearchResults object with the results of the search.
   * The inner "results" object of the KernelSearchResults should be an async iterator that yields the search results,
   * this allows things like paging to be implemented.
   *
   * Options might be an object of type VectorSearchOptions, or a subclass of it.
   *
   * The implementation of this method must deal with the possibility that multiple search contents are provided,
   * and should handle them in a way that makes sense for that particular store.
   *
   * @param searchType - The type of search to perform.
   * @param options - The search options, can be null.
   * @param values - The values to search for, optional.
   * @param vector - The vector to search for, optional.
   * @param kwargs - Additional arguments that might be needed.
   * @returns The search results, wrapped in a KernelSearchResults object.
   * @throws Error if an error occurs during the search, deserialization, or if options are invalid.
   */
  protected abstract _innerSearch(
    searchType: SearchType,
    options: VectorSearchOptions,
    values?: any | null,
    vector?: number[] | null,
    kwargs?: Record<string, any>
  ): Promise<any>

  /**
   * Get the record from the returned search result.
   *
   * Does any unpacking or processing of the result to get just the record.
   *
   * If the underlying SDK of the store returns a particular type that might include something
   * like a score or other metadata, this method should be overridden to extract just the record.
   *
   * Likely returns a dict, but in some cases could return the record in the form of a SDK specific object.
   *
   * This method is used as part of the _getVectorSearchResultsFromResults method,
   * the output of it is passed to the deserializer.
   */
  protected abstract _getRecordFromResult(result: any): any

  /**
   * Get the score from the result.
   *
   * Does any unpacking or processing of the result to get just the score.
   *
   * If the underlying SDK of the store returns a particular type with a score or other metadata,
   * this method extracts it.
   */
  protected abstract _getScoreFromResult(result: any): number | null

  /**
   * Convert results to vector search results.
   */
  protected async *_getVectorSearchResultsFromResults(
    results: AsyncIterable<any> | any[],
    options?: VectorSearchOptions | null
  ): AsyncIterable<VectorSearchResult<TModel>> {
    const resultsIterable = Array.isArray(results)
      ? (async function* () {
          for (const r of results) yield r
        })()
      : results

    for await (const result of resultsIterable) {
      if (!result) {
        continue
      }
      try {
        const record = this.deserialize(this._getRecordFromResult(result), {
          include_vectors: options?.includeVectors ?? true,
        })
        const score = this._getScoreFromResult(result)
        if (record !== null) {
          yield new VectorSearchResult({ record: record as TModel, score })
        }
      } catch (error) {
        throw new Error('An error occurred while deserializing the record', { cause: error })
      }
    }
  }

  /**
   * Search the vector store for records that match the given value and filter.
   *
   * @param params - Search parameters
   * @param params.values - The values to search for. These will be vectorized.
   * @param params.vector - The vector to search for
   * @param params.vectorFieldName - The name of the vector field to use for the search.
   * @param params.filter - The filter to apply to the search.
   * @param params.top - The number of results to return.
   * @param params.skip - The number of results to skip.
   * @param params.includeTotalCount - Whether to include the total count of results.
   * @param params.includeVectors - Whether to include the vectors in the results.
   * @param kwargs - Additional arguments.
   * @returns The search results.
   * @throws Error if an error occurs during the search.
   */
  async search(
    params?: {
      values?: any
      vector?: number[]
      vectorFieldName?: string | null
      filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
      top?: number
      skip?: number
      includeTotalCount?: boolean
      includeVectors?: boolean
    },
    kwargs?: Record<string, any>
  ): Promise<any> {
    if (!this.supportedSearchTypes.has(SearchType.VECTOR)) {
      throw new Error(`Vector search is not supported by this vector store: ${this.constructor.name}`)
    }
    const options = new VectorSearchOptions({
      filter: params?.filter ?? null,
      vectorPropertyName: params?.vectorFieldName ?? null,
      top: params?.top ?? 3,
      skip: params?.skip ?? 0,
      includeTotalCount: params?.includeTotalCount ?? false,
      includeVectors: params?.includeVectors ?? false,
    })
    try {
      return await this._innerSearch(SearchType.VECTOR, options, params?.values, params?.vector, kwargs)
    } catch (error) {
      throw new Error('An error occurred during the search', { cause: error })
    }
  }

  /**
   * Search the vector store for records that match the given values and filter using hybrid search.
   *
   * @param params - Search parameters
   * @param params.values - The values to search for.
   * @param params.vector - The vector to search for, if not provided, the values will be used to generate a vector.
   * @param params.vectorFieldName - The name of the vector field to use for the search.
   * @param params.additionalPropertyName - The name of the additional property field to use for the search.
   * @param params.filter - The filter to apply to the search.
   * @param params.top - The number of results to return.
   * @param params.skip - The number of results to skip.
   * @param params.includeTotalCount - Whether to include the total count of results.
   * @param params.includeVectors - Whether to include the vectors in the results.
   * @param kwargs - Additional arguments.
   * @returns The search results.
   * @throws Error if an error occurs during the search.
   */
  async hybridSearch(
    params: {
      values: any
      vector?: number[] | null
      vectorFieldName?: string | null
      additionalPropertyName?: string | null
      filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
      top?: number
      skip?: number
      includeTotalCount?: boolean
      includeVectors?: boolean
    },
    kwargs?: Record<string, any>
  ): Promise<any> {
    if (!this.supportedSearchTypes.has(SearchType.KEYWORD_HYBRID)) {
      throw new Error(`Keyword hybrid search is not supported by this vector store: ${this.constructor.name}`)
    }
    const options = new VectorSearchOptions({
      filter: params.filter ?? null,
      vectorPropertyName: params.vectorFieldName ?? null,
      additionalPropertyName: params.additionalPropertyName ?? null,
      top: params.top ?? 3,
      skip: params.skip ?? 0,
      includeTotalCount: params.includeTotalCount ?? false,
      includeVectors: params.includeVectors ?? false,
    })
    try {
      return await this._innerSearch(SearchType.KEYWORD_HYBRID, options, params.values, params.vector, kwargs)
    } catch (error) {
      throw new Error('An error occurred during the search', { cause: error })
    }
  }

  /**
   * Generate a vector from the given keywords.
   */
  protected async _generateVectorFromValues(
    values: any | null,
    options: VectorSearchOptions
  ): Promise<number[] | null> {
    if (values === null) {
      return null
    }
    const vectorField = this.definition.tryGetVectorField(options.vectorPropertyName)
    if (!vectorField) {
      throw new Error(`Vector field '${options.vectorPropertyName}' not found in data model definition.`)
    }
    const embeddingGenerator = vectorField.embeddingGenerator || this.embeddingGenerator
    if (!embeddingGenerator) {
      throw new Error(`Embedding generator not found for vector field '${options.vectorPropertyName}'.`)
    }

    const embeddings = await embeddingGenerator.generateRawEmbeddings(
      [typeof values === 'string' ? values : JSON.stringify(values)],
      { dimensions: vectorField.dimensions }
    )
    return embeddings[0]
  }

  /**
   * Create the filter based on the filters.
   *
   * This function returns null, a single filter, or a list of filters.
   * If a single filter is passed, a single filter is returned.
   *
   * It takes the filters, which can be a Callable (function) or a string, and parses them into a filter object,
   * using the _lambdaParser method that is specific to each vector store.
   *
   * If a list of filters is passed, the parsed filters are also returned as a list, so the caller needs to
   * combine them in the appropriate way.
   *
   * @param searchFilter - The filter or filters to build
   * @returns null, a single filter, or an array of filters
   */
  protected _buildFilter(
    searchFilter:
      | string
      | ((options: SearchOptions) => void)
      | Array<string | ((options: SearchOptions) => void)>
      | null
  ): any | any[] | null {
    if (!searchFilter) {
      return null
    }

    const filters = Array.isArray(searchFilter) ? searchFilter : [searchFilter]

    const visitor = new LambdaVisitor(this._lambdaParser.bind(this))
    for (const filter of filters) {
      if (typeof filter === 'string') {
        // For string filters, just parse them directly
        visitor.outputFilters.push(this._lambdaParser(filter))
      } else {
        // For function filters, in a full implementation you would parse the function AST
        // For now, we'll convert to string and parse
        visitor.outputFilters.push(this._lambdaParser(filter.toString()))
      }
    }

    if (visitor.outputFilters.length === 0) {
      throw new Error('No filter strings found.')
    }
    if (visitor.outputFilters.length === 1) {
      return visitor.outputFilters[0]
    }
    return visitor.outputFilters
  }

  /**
   * Parse the lambda/filter expression and return the filter string or object.
   *
   * This method should be implemented in the derived class to parse filter expressions
   * and return the store-specific filter format.
   *
   * @param node - The AST node or filter string to parse
   * @returns The store-specific filter
   */
  protected abstract _lambdaParser(node: any): any

  /**
   * Create a kernel function from a search function.
   *
   * @param params - Function creation parameters
   * @param params.functionName - The name of the function (default: "search")
   * @param params.description - The description of the function
   * @param params.searchType - The type of search to perform ('vector' or 'keyword_hybrid')
   * @param params.parameters - The parameters for the function (null for default set)
   * @param params.returnParameter - The return parameter for the function
   * @param params.filter - The filter to apply to the search
   * @param params.top - The number of results to return
   * @param params.skip - The number of results to skip
   * @param params.vectorPropertyName - The name of the vector property
   * @param params.additionalPropertyName - The name of the additional property field
   * @param params.includeVectors - Whether to include the vectors in the results
   * @param params.includeTotalCount - Whether to include the total count
   * @param params.filterUpdateFunction - A function to update the filters
   * @param params.stringMapper - Function to map search results to strings
   * @returns A KernelFunction that can be used in the kernel
   */
  createSearchFunction(params?: {
    functionName?: string
    description?: string
    searchType?: 'vector' | 'keyword_hybrid'
    parameters?: any[] | null
    returnParameter?: any | null
    filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
    top?: number
    skip?: number
    vectorPropertyName?: string | null
    additionalPropertyName?: string | null
    includeVectors?: boolean
    includeTotalCount?: boolean
    filterUpdateFunction?: ((filter: any, parameters?: any[], kwargs?: Record<string, any>) => any) | null
    stringMapper?: ((result: VectorSearchResult<TModel>) => string) | null
  }): any {
    const functionName = params?.functionName ?? 'search'
    const description = params?.description ?? DEFAULT_DESCRIPTION
    const searchType = params?.searchType === 'keyword_hybrid' ? SearchType.KEYWORD_HYBRID : SearchType.VECTOR

    if (!this.supportedSearchTypes.has(searchType)) {
      throw new Error(`Search type '${searchType}' is not supported by this vector store: ${this.constructor.name}`)
    }

    const options = new VectorSearchOptions({
      filter: params?.filter ?? null,
      skip: params?.skip ?? 0,
      top: params?.top ?? 5,
      includeTotalCount: params?.includeTotalCount ?? false,
      includeVectors: params?.includeVectors ?? false,
      vectorPropertyName: params?.vectorPropertyName ?? null,
      additionalPropertyName: params?.additionalPropertyName ?? null,
    })

    return this._createKernelFunction({
      searchType,
      options,
      parameters: params?.parameters,
      filterUpdateFunction: params?.filterUpdateFunction,
      returnParameter: params?.returnParameter,
      functionName,
      description,
      stringMapper: params?.stringMapper,
    })
  }

  /**
   * Create a kernel function from a search function.
   * Internal helper method.
   *
   * @param params - Function creation parameters
   * @returns A function that can be registered as a kernel function
   */
  protected _createKernelFunction(params: {
    searchType: SearchType
    options?: VectorSearchOptions | null
    parameters?: any[] | null
    filterUpdateFunction?: ((filter: any, parameters?: any[], kwargs?: Record<string, any>) => any) | null
    returnParameter?: any | null
    functionName?: string
    description?: string
    stringMapper?: ((result: VectorSearchResult<TModel>) => string) | null
  }): any {
    const updateFunc = params.filterUpdateFunction ?? ((filter: any) => filter)
    const functionName = params.functionName ?? 'search'
    const description = params.description ?? DEFAULT_DESCRIPTION

    // Create the search wrapper function
    const searchWrapper = async (kwargs: Record<string, any> = {}): Promise<string[]> => {
      const query = kwargs.query ?? ''
      delete kwargs.query

      const innerOptions = params.options ? { ...params.options } : new VectorSearchOptions()

      // Apply filter update function
      innerOptions.filter = updateFunc(innerOptions.filter, params.parameters as any[] | undefined, kwargs)

      try {
        let results: any
        if (params.searchType === SearchType.VECTOR) {
          results = await this.search(
            {
              values: query,
              filter: innerOptions.filter,
              top: innerOptions.top,
              skip: innerOptions.skip,
              includeTotalCount: innerOptions.includeTotalCount,
              includeVectors: innerOptions.includeVectors,
              vectorFieldName: innerOptions.vectorPropertyName ?? undefined,
            },
            kwargs
          )
        } else if (params.searchType === SearchType.KEYWORD_HYBRID) {
          results = await this.hybridSearch(
            {
              values: query,
              filter: innerOptions.filter,
              top: innerOptions.top,
              skip: innerOptions.skip,
              includeTotalCount: innerOptions.includeTotalCount,
              includeVectors: innerOptions.includeVectors,
              vectorFieldName: innerOptions.vectorPropertyName ?? undefined,
              additionalPropertyName: innerOptions.additionalPropertyName ?? undefined,
            },
            kwargs
          )
        } else {
          throw new Error(
            `Search type '${params.searchType}' is not supported by this vector store: ${this.constructor.name}`
          )
        }

        // Map results to strings
        if (params.stringMapper && results?.results) {
          const mappedResults: string[] = []
          for await (const result of results.results) {
            mappedResults.push(params.stringMapper(result))
          }
          return mappedResults
        }

        // Default: return JSON strings
        if (results?.results) {
          const jsonResults: string[] = []
          for await (const result of results.results) {
            jsonResults.push(JSON.stringify(result))
          }
          return jsonResults
        }

        return []
      } catch (error) {
        throw new Error('Exception in search function', { cause: error })
      }
    }

    // Return an object with the function and metadata
    return {
      name: functionName,
      description,
      invoke: searchWrapper,
      parameters: params.parameters,
      returnParameter: params.returnParameter,
    }
  }
}

/**
 * Protocol interface for vector store collections.
 * @releaseCandidate
 */
export interface VectorStoreCollectionProtocol<TKey = any, TModel = any> {
  collectionName: string
  recordType: new (...args: any[]) => TModel
  definition: VectorStoreCollectionDefinition
  supportedKeyTypes: Set<string> | null
  supportedVectorTypes: Set<string> | null
  embeddingGenerator?: EmbeddingGeneratorBase | null

  /**
   * Create the collection in the service if it does not exist.
   *
   * First uses collectionExists to check if it exists, if it does returns false.
   * Otherwise, creates the collection and returns true.
   *
   * @param kwargs - Additional arguments.
   * @returns True if the collection was created, false if it already exists.
   */
  ensureCollectionExists(kwargs?: Record<string, any>): Promise<boolean>

  /**
   * Check if the collection exists.
   *
   * @param kwargs - Additional arguments.
   * @returns True if the collection exists, false otherwise.
   * @throws Error with relevant description.
   */
  collectionExists(kwargs?: Record<string, any>): Promise<boolean>

  /**
   * Delete the collection.
   *
   * @param kwargs - Additional arguments.
   */
  ensureCollectionDeleted(kwargs?: Record<string, any>): Promise<void>

  /**
   * Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.
   *
   * @param params - Get parameters
   * @param params.key - The key to get
   * @param params.keys - The keys to get, if keys are provided, key is ignored
   * @param params.includeVectors - Include the vectors in the response. Default is false.
   * @param params.top - The number of records to return (only used if keys are not provided)
   * @param params.skip - The number of records to skip (only used if keys are not provided)
   * @param params.orderBy - The order by clause
   * @param kwargs - Additional arguments
   * @returns The records, either a list of TModel or the container type.
   * @throws Error if an error occurs during the get or deserialization.
   */
  get(
    params?: {
      key?: TKey
      keys?: TKey[]
      includeVectors?: boolean
      top?: number
      skip?: number
      orderBy?: string | string[] | Record<string, boolean>
    },
    kwargs?: Record<string, any>
  ): Promise<OneOrMany<TModel> | null>

  /**
   * Upsert one or more records.
   *
   * If the key of the record already exists, the existing record will be updated.
   * If the key does not exist, a new record will be created.
   *
   * @param records - The records to upsert, can be a single record, a list of records, or a single container.
   * @param kwargs - Additional arguments.
   * @returns The keys of the upserted records.
   * @throws Error if an error occurs during serialization or upserting.
   */
  upsert(records: OneOrMany<TModel>, kwargs?: Record<string, any>): Promise<OneOrMany<TKey>>

  /**
   * Delete one or more records by key.
   *
   * An exception will be raised at the end if any record does not exist.
   *
   * @param keys - The key or keys to be deleted.
   * @param kwargs - Additional arguments.
   * @throws Error if an error occurs during deletion or a record does not exist.
   */
  delete(keys: OneOrMany<TKey>, kwargs?: Record<string, any>): Promise<void>
}

/**
 * Protocol interface for vector search collections.
 * Extends VectorStoreCollectionProtocol with search capabilities.
 * @releaseCandidate
 */
export interface VectorSearchProtocol<TKey = any, TModel = any> extends VectorStoreCollectionProtocol<TKey, TModel> {
  supportedSearchTypes: Set<SearchType>

  /**
   * Search the vector store for records that match the given value and filter.
   *
   * @param params - Search parameters
   * @param params.values - The values to search for. These will be vectorized.
   * @param params.vector - The vector to search for
   * @param params.vectorPropertyName - The name of the vector property to use for the search.
   * @param params.filter - The filter to apply to the search.
   * @param params.top - The number of results to return.
   * @param params.skip - The number of results to skip.
   * @param params.includeTotalCount - Whether to include the total count of results.
   * @param params.includeVectors - Whether to include the vectors in the results.
   * @param kwargs - Additional arguments.
   * @returns The search results.
   * @throws Error if an error occurs during the search, deserialization, or if options are invalid.
   */
  search(
    params?: {
      values?: any
      vector?: number[]
      vectorPropertyName?: string | null
      filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
      top?: number
      skip?: number
      includeTotalCount?: boolean
      includeVectors?: boolean
    },
    kwargs?: Record<string, any>
  ): Promise<any>

  /**
   * Search the vector store for records that match the given values and filter using hybrid search.
   *
   * @param params - Search parameters
   * @param params.values - The values to search for.
   * @param params.vector - The vector to search for
   * @param params.vectorPropertyName - The name of the vector field to use for the search.
   * @param params.additionalPropertyName - The name of the additional property field to use for the search.
   * @param params.filter - The filter to apply to the search.
   * @param params.top - The number of results to return.
   * @param params.skip - The number of results to skip.
   * @param params.includeTotalCount - Whether to include the total count of results.
   * @param params.includeVectors - Whether to include the vectors in the results.
   * @param kwargs - Additional arguments.
   * @returns The search results.
   * @throws Error if an error occurs during the search, deserialization, or if options are invalid.
   */
  hybridSearch(
    params: {
      values: any
      vector?: number[] | null
      vectorPropertyName?: string | null
      additionalPropertyName?: string | null
      filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
      top?: number
      skip?: number
      includeTotalCount?: boolean
      includeVectors?: boolean
    },
    kwargs?: Record<string, any>
  ): Promise<any>
}
