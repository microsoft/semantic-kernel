// PostgreSQL vector store connector implementation for Semantic Kernel
import { Pool, PoolConfig } from 'pg'
import format from 'pg-format'
import {
  DistanceFunction,
  FieldTypes,
  IndexKind,
  VectorStoreCollectionDefinition,
  VectorStoreField,
} from '../data/vector'
import { MemoryConnectorConnectionException } from '../exceptions/memory-connector-exceptions'
import { VectorStoreModelValidationError, VectorStoreOperationException } from '../exceptions/vector-store-exceptions'
import { createDefaultLogger } from '../utils/logger'

const logger = createDefaultLogger('PostgresConnector')

// region: Constants

export const DEFAULT_SCHEMA = 'public'
export const MAX_DIMENSIONALITY = 2000
export const DISTANCE_COLUMN_NAME = 'sk_pg_distance'

// Environment variables
export const PGHOST_ENV_VAR = 'PGHOST'
export const PGPORT_ENV_VAR = 'PGPORT'
export const PGDATABASE_ENV_VAR = 'PGDATABASE'
export const PGUSER_ENV_VAR = 'PGUSER'
export const PGPASSWORD_ENV_VAR = 'PGPASSWORD'
export const PGSSLMODE_ENV_VAR = 'PGSSLMODE'

export enum SearchType {
  VECTOR = 'vector',
}

const DISTANCE_FUNCTION_MAP_STRING: Record<DistanceFunction, string> = {
  [DistanceFunction.CosineSimilarity]: 'vector_cosine_ops',
  [DistanceFunction.CosineDistance]: 'vector_cosine_ops',
  [DistanceFunction.DotProduct]: 'vector_ip_ops',
  [DistanceFunction.EuclideanDistance]: 'vector_l2_ops',
  [DistanceFunction.EuclideanSquaredDistance]: 'vector_l2_ops',
  [DistanceFunction.ManhattanDistance]: 'vector_l1_ops',
  [DistanceFunction.HammingDistance]: 'bit_hamming_ops',
  [DistanceFunction.DEFAULT]: 'vector_cosine_ops',
}

const DISTANCE_FUNCTION_MAP_OPS: Record<DistanceFunction, string> = {
  [DistanceFunction.CosineDistance]: '<=>',
  [DistanceFunction.CosineSimilarity]: '<=>',
  [DistanceFunction.DotProduct]: '<#>',
  [DistanceFunction.EuclideanDistance]: '<->',
  [DistanceFunction.EuclideanSquaredDistance]: '<->',
  [DistanceFunction.ManhattanDistance]: '<+>',
  [DistanceFunction.DEFAULT]: '<=>',
  [DistanceFunction.HammingDistance]: '',
}

const INDEX_KIND_MAP: Record<IndexKind, string> = {
  [IndexKind.HNSW]: 'hnsw',
  [IndexKind.IVFFlat]: 'ivfflat',
  [IndexKind.Flat]: 'flat',
  [IndexKind.DiskANN]: 'diskann',
  [IndexKind.QuantizedFlat]: 'quantizedflat',
  [IndexKind.Dynamic]: 'dynamic',
  [IndexKind.DEFAULT]: 'hnsw',
}

// region: Helpers

/**
 * Convert a TypeScript type string to PostgreSQL data type
 */
function pythonTypeToPostgres(typeStr: string): string | null {
  const typeMapping: Record<string, string> = {
    string: 'TEXT',
    number: 'DOUBLE PRECISION',
    boolean: 'BOOLEAN',
    object: 'JSONB',
    Date: 'TIMESTAMP',
    Buffer: 'BYTEA',
    null: 'NULL',
  }

  // Check for array types
  const listPattern = /(?:Array<(.+)>|(.+)\[\])/i
  const match = listPattern.exec(typeStr)
  if (match) {
    const elementType = match[1] || match[2]
    const postgresElementType = pythonTypeToPostgres(elementType)
    return postgresElementType ? `${postgresElementType}[]` : null
  }

  // Check for dictionary/object types
  if (typeStr.toLowerCase().includes('record') || typeStr.toLowerCase() === 'object') {
    return 'JSONB'
  }

  return typeMapping[typeStr] || null
}

/**
 * Convert a database row to a dictionary
 */
function convertRowToDict(row: any, fields: Array<[string, VectorStoreField | null]>): Record<string, any> {
  const result: Record<string, any> = {}

  fields.forEach(([fieldName, field]) => {
    const value = row[fieldName]
    if (value === null || value === undefined) {
      result[fieldName] = null
    } else if (field && field.fieldType === FieldTypes.VECTOR && typeof value === 'string') {
      // Parse vector string to array
      result[fieldName] = JSON.parse(value)
    } else {
      result[fieldName] = value
    }
  })

  return result
}

/**
 * Convert a dictionary to a database row
 */
function convertDictToRow(record: Record<string, any>, fields: VectorStoreField[]): any[] {
  return fields.map((field) => {
    const value = record[field.storageName || field.name]
    if (value === null || value === undefined) {
      return null
    }
    if (typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      return JSON.stringify(value)
    }
    return value
  })
}

// region: Embedding Generator Interface

/**
 * Embedding generator interface for generating vector embeddings from text/values
 */
export interface EmbeddingGenerator<TValue = string> {
  /**
   * Generate embeddings from a list of values
   * @param values The values to generate embeddings for
   * @returns Promise of embedding vectors
   */
  generateEmbeddings(values: TValue[]): Promise<number[][]>
}

// endregion

// region: Filter Types

/**
 * Comparison operators for filter expressions
 */
export enum FilterOperator {
  EQUAL = 'eq',
  NOT_EQUAL = 'ne',
  GREATER_THAN = 'gt',
  GREATER_THAN_OR_EQUAL = 'gte',
  LESS_THAN = 'lt',
  LESS_THAN_OR_EQUAL = 'lte',
  IN = 'in',
  NOT_IN = 'nin',
}

/**
 * Logical operators for combining filters
 */
export enum LogicalOperator {
  AND = 'and',
  OR = 'or',
  NOT = 'not',
}

/**
 * Base filter type
 */
export type Filter = ComparisonFilter | LogicalFilter | NotFilter

/**
 * Comparison filter (field op value)
 */
export interface ComparisonFilter {
  field: string
  operator: FilterOperator
  value: any
}

/**
 * Logical filter (AND/OR multiple filters)
 */
export interface LogicalFilter {
  operator: LogicalOperator.AND | LogicalOperator.OR
  filters: Filter[]
}

/**
 * NOT filter (negates a filter)
 */
export interface NotFilter {
  operator: LogicalOperator.NOT
  filter: Filter
}

/**
 * Type guard to check if a filter is a comparison filter
 */
function isComparisonFilter(filter: Filter): filter is ComparisonFilter {
  return 'field' in filter && 'operator' in filter && 'value' in filter
}

/**
 * Type guard to check if a filter is a logical filter
 */
function isLogicalFilter(filter: Filter): filter is LogicalFilter {
  return 'filters' in filter && (filter.operator === LogicalOperator.AND || filter.operator === LogicalOperator.OR)
}

/**
 * Type guard to check if a filter is a NOT filter
 */
function isNotFilter(filter: Filter): filter is NotFilter {
  return 'filter' in filter && filter.operator === LogicalOperator.NOT
}

/**
 * Helper functions to create filters
 */
export const Filters = {
  /**
   * Create an equality filter (field = value)
   */
  eq: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.EQUAL,
    value,
  }),

  /**
   * Create a not-equal filter (field <> value)
   */
  ne: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.NOT_EQUAL,
    value,
  }),

  /**
   * Create a greater-than filter (field > value)
   */
  gt: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.GREATER_THAN,
    value,
  }),

  /**
   * Create a greater-than-or-equal filter (field >= value)
   */
  gte: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.GREATER_THAN_OR_EQUAL,
    value,
  }),

  /**
   * Create a less-than filter (field < value)
   */
  lt: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.LESS_THAN,
    value,
  }),

  /**
   * Create a less-than-or-equal filter (field <= value)
   */
  lte: (field: string, value: any): ComparisonFilter => ({
    field,
    operator: FilterOperator.LESS_THAN_OR_EQUAL,
    value,
  }),

  /**
   * Create an IN filter (field IN values)
   */
  in: (field: string, values: any[]): ComparisonFilter => ({
    field,
    operator: FilterOperator.IN,
    value: values,
  }),

  /**
   * Create a NOT IN filter (field NOT IN values)
   */
  notIn: (field: string, values: any[]): ComparisonFilter => ({
    field,
    operator: FilterOperator.NOT_IN,
    value: values,
  }),

  /**
   * Combine filters with AND
   */
  and: (...filters: Filter[]): LogicalFilter => ({
    operator: LogicalOperator.AND,
    filters,
  }),

  /**
   * Combine filters with OR
   */
  or: (...filters: Filter[]): LogicalFilter => ({
    operator: LogicalOperator.OR,
    filters,
  }),

  /**
   * Negate a filter with NOT
   */
  not: (filter: Filter): NotFilter => ({
    operator: LogicalOperator.NOT,
    filter,
  }),
}

/**
 * Helper class to build and validate filters
 */
class FilterBuilder {
  constructor(private definition: VectorStoreCollectionDefinition) {}

  /**
   * Validate that a field exists in the data model
   */
  private validateField(fieldName: string): string {
    const storageNames = this.definition.fields.map((f) => f.storageName || f.name)
    if (!storageNames.includes(fieldName)) {
      throw new VectorStoreOperationException(
        `Field '${fieldName}' not in data model. Available fields: ${storageNames.join(', ')}`
      )
    }
    return fieldName
  }

  /**
   * Escape a string value for SQL
   */
  private escapeValue(value: any): string {
    if (value === null || value === undefined) {
      return 'NULL'
    }
    if (typeof value === 'string') {
      // Escape single quotes by doubling them
      return "'" + value.replace(/'/g, "''") + "'"
    }
    if (typeof value === 'boolean') {
      return value ? 'TRUE' : 'FALSE'
    }
    if (typeof value === 'number') {
      return String(value)
    }
    if (Array.isArray(value)) {
      return '(' + value.map((v) => this.escapeValue(v)).join(', ') + ')'
    }
    // For objects, convert to JSON string
    return "'" + JSON.stringify(value).replace(/'/g, "''") + "'"
  }

  /**
   * Build WHERE clause from a filter
   */
  buildWhereClause(filter: Filter): string {
    if (isComparisonFilter(filter)) {
      return this.buildComparisonClause(filter)
    } else if (isLogicalFilter(filter)) {
      return this.buildLogicalClause(filter)
    } else if (isNotFilter(filter)) {
      return this.buildNotClause(filter)
    }
    throw new VectorStoreOperationException(`Unsupported filter type: ${JSON.stringify(filter)}`)
  }

  /**
   * Build a comparison clause (field op value)
   */
  private buildComparisonClause(filter: ComparisonFilter): string {
    const field = this.validateField(filter.field)
    const quotedField = format('%I', field)

    switch (filter.operator) {
      case FilterOperator.EQUAL:
        return `${quotedField} = ${this.escapeValue(filter.value)}`
      case FilterOperator.NOT_EQUAL:
        return `${quotedField} <> ${this.escapeValue(filter.value)}`
      case FilterOperator.GREATER_THAN:
        return `${quotedField} > ${this.escapeValue(filter.value)}`
      case FilterOperator.GREATER_THAN_OR_EQUAL:
        return `${quotedField} >= ${this.escapeValue(filter.value)}`
      case FilterOperator.LESS_THAN:
        return `${quotedField} < ${this.escapeValue(filter.value)}`
      case FilterOperator.LESS_THAN_OR_EQUAL:
        return `${quotedField} <= ${this.escapeValue(filter.value)}`
      case FilterOperator.IN:
        if (!Array.isArray(filter.value)) {
          throw new VectorStoreOperationException('IN operator requires an array value')
        }
        return `${quotedField} IN ${this.escapeValue(filter.value)}`
      case FilterOperator.NOT_IN:
        if (!Array.isArray(filter.value)) {
          throw new VectorStoreOperationException('NOT IN operator requires an array value')
        }
        return `${quotedField} NOT IN ${this.escapeValue(filter.value)}`
      default:
        throw new VectorStoreOperationException(`Unsupported operator: ${filter.operator}`)
    }
  }

  /**
   * Build a logical clause (AND/OR multiple filters)
   */
  private buildLogicalClause(filter: LogicalFilter): string {
    if (filter.filters.length === 0) {
      throw new VectorStoreOperationException('Logical filter must have at least one filter')
    }

    const clauses = filter.filters.map((f) => this.buildWhereClause(f))

    if (clauses.length === 1) {
      return clauses[0]
    }

    const operator = filter.operator === LogicalOperator.AND ? ' AND ' : ' OR '
    return '(' + clauses.join(operator) + ')'
  }

  /**
   * Build a NOT clause
   */
  private buildNotClause(filter: NotFilter): string {
    return `NOT (${this.buildWhereClause(filter.filter)})`
  }
}

// region: Interfaces

export interface PostgresSettings {
  connectionString?: string
  host?: string
  port?: number
  database?: string
  user?: string
  password?: string
  sslMode?: string
  minPool?: number
  maxPool?: number
  defaultDimensionality?: number
  maxRowsPerTransaction?: number
}

export interface VectorSearchOptions {
  vectorPropertyName?: string
  includeVectors?: boolean
  top?: number
  skip?: number
  filter?: Filter
  includeTotalCount?: boolean
  /** Use streaming for results (memory efficient for large datasets) */
  useStreaming?: boolean
  /**
   * Values to generate embeddings from (alternative to providing vector directly)
   * Requires an embedding generator to be configured
   */
  values?: any
}

export interface VectorSearchResult<T> {
  record: T
  score?: number
}

export interface GetFilteredRecordOptions {
  filter?: Filter
}

/**
 * Wrapper for search results that can be either an array or async generator
 */
export class KernelSearchResults<T> {
  constructor(
    public results: T[] | AsyncGenerator<T>,
    public totalCount?: number
  ) {}

  /**
   * Check if results are streaming (async generator)
   */
  isStreaming(): this is { results: AsyncGenerator<T> } {
    return typeof (this.results as any)[Symbol.asyncIterator] === 'function'
  }

  /**
   * Convert streaming results to array (consumes the generator)
   */
  async toArray(): Promise<T[]> {
    if (!this.isStreaming()) {
      return this.results as T[]
    }

    const array: T[] = []
    for await (const item of this.results as AsyncGenerator<T>) {
      array.push(item)
    }
    return array
  }

  /**
   * Get async iterator for results
   */
  async *[Symbol.asyncIterator](): AsyncGenerator<T> {
    if (this.isStreaming()) {
      yield* this.results as AsyncGenerator<T>
    } else {
      for (const item of this.results as T[]) {
        yield item
      }
    }
  }
}

// region: Settings

export class PostgresConfig {
  connectionString?: string
  host?: string
  port: number
  database?: string
  user?: string
  password?: string
  sslMode?: string
  minPool: number
  maxPool: number
  defaultDimensionality: number
  maxRowsPerTransaction: number

  constructor(settings?: PostgresSettings) {
    this.connectionString = settings?.connectionString || process.env.POSTGRES_CONNECTION_STRING
    this.host = settings?.host || process.env[PGHOST_ENV_VAR] || process.env.POSTGRES_HOST
    this.port = settings?.port || parseInt(process.env[PGPORT_ENV_VAR] || process.env.POSTGRES_PORT || '5432')
    this.database = settings?.database || process.env[PGDATABASE_ENV_VAR] || process.env.POSTGRES_DBNAME
    this.user = settings?.user || process.env[PGUSER_ENV_VAR] || process.env.POSTGRES_USER
    this.password = settings?.password || process.env[PGPASSWORD_ENV_VAR] || process.env.POSTGRES_PASSWORD
    this.sslMode = settings?.sslMode || process.env[PGSSLMODE_ENV_VAR] || process.env.POSTGRES_SSL_MODE
    this.minPool = settings?.minPool || parseInt(process.env.POSTGRES_MIN_POOL || '1')
    this.maxPool = settings?.maxPool || parseInt(process.env.POSTGRES_MAX_POOL || '5')
    this.defaultDimensionality =
      settings?.defaultDimensionality || parseInt(process.env.POSTGRES_DEFAULT_DIMENSIONALITY || '100')
    this.maxRowsPerTransaction =
      settings?.maxRowsPerTransaction || parseInt(process.env.POSTGRES_MAX_ROWS_PER_TRANSACTION || '1000')
  }

  getConnectionConfig(): PoolConfig {
    if (this.connectionString) {
      return {
        connectionString: this.connectionString,
        min: this.minPool,
        max: this.maxPool,
      }
    }

    return {
      host: this.host,
      port: this.port,
      database: this.database,
      user: this.user,
      password: this.password,
      ssl: this.sslMode === 'require' ? { rejectUnauthorized: false } : this.sslMode === 'disable' ? false : undefined,
      min: this.minPool,
      max: this.maxPool,
    }
  }

  async createConnectionPool(): Promise<Pool> {
    try {
      const pool = new Pool(this.getConnectionConfig())
      // Test connection
      const client = await pool.connect()
      client.release()
      return pool
    } catch (error) {
      throw new MemoryConnectorConnectionException(`Error creating connection pool: ${error}`, {
        cause: error as Error,
      })
    }
  }
}

// region: Collection

export class PostgresCollection<TKey extends string | number, TModel extends Record<string, any>> {
  static readonly SUPPORTED_KEY_TYPES = new Set(['string', 'number', 'int', 'str'])
  static readonly SUPPORTED_VECTOR_TYPES = new Set(['float', 'number'])
  static readonly SUPPORTED_DATA_TYPES = new Set([
    'string',
    'str',
    'TEXT',
    'number',
    'int',
    'float',
    'INTEGER',
    'DOUBLE PRECISION',
    'boolean',
    'bool',
    'BOOLEAN',
    'object',
    'dict',
    'JSONB',
    'Date',
    'datetime',
    'TIMESTAMP',
    'Buffer',
    'bytes',
    'BYTEA',
  ])

  connectionPool?: Pool
  dbSchema: string = DEFAULT_SCHEMA
  collectionName: string
  definition: VectorStoreCollectionDefinition
  recordType: new () => TModel
  managedClient: boolean
  embeddingGenerator?: EmbeddingGenerator<any>
  private settings: PostgresConfig
  private distanceColumnName: string = DISTANCE_COLUMN_NAME

  constructor(options: {
    recordType: new () => TModel
    definition?: VectorStoreCollectionDefinition
    collectionName?: string
    connectionPool?: Pool
    dbSchema?: string
    settings?: PostgresSettings
    embeddingGenerator?: EmbeddingGenerator<any>
  }) {
    this.recordType = options.recordType
    this.collectionName = options.collectionName || new options.recordType().constructor.name
    this.connectionPool = options.connectionPool
    this.dbSchema = options.dbSchema || DEFAULT_SCHEMA
    this.managedClient = !options.connectionPool
    this.settings = new PostgresConfig(options.settings)
    this.embeddingGenerator = options.embeddingGenerator

    // Initialize definition
    if (options.definition) {
      this.definition = options.definition
    } else {
      // Create basic definition from record type
      this.definition = new VectorStoreCollectionDefinition({
        fields: [],
        collectionName: this.collectionName,
      })
    }

    this.initializeDistanceColumnName()
    this.validateDataModel()
  }

  private initializeDistanceColumnName(): void {
    let distanceColumnName = DISTANCE_COLUMN_NAME
    const storageNames = this.definition.fields.map((f) => f.storageName || f.name)
    let tries = 0

    while (storageNames.includes(distanceColumnName)) {
      const suffix = Math.random().toString(36).substring(2, 10)
      distanceColumnName = `${DISTANCE_COLUMN_NAME}_${suffix}`
      tries++
      if (tries > 10) {
        throw new VectorStoreModelValidationError('Unable to generate a unique distance column name.')
      }
    }

    this.distanceColumnName = distanceColumnName
  }

  async connect(): Promise<PostgresCollection<TKey, TModel>> {
    if (!this.connectionPool) {
      this.connectionPool = await this.settings.createConnectionPool()
    }
    return this
  }

  async close(): Promise<void> {
    if (this.managedClient && this.connectionPool) {
      await this.connectionPool.end()
      if (this.managedClient) {
        this.connectionPool = undefined
      }
    }
  }

  private validateDataModel(): void {
    // Validate key field type
    const keyField = this.definition.fields.find((f) => f.fieldType === FieldTypes.KEY)
    if (keyField?.type_ && !PostgresCollection.SUPPORTED_KEY_TYPES.has(keyField.type_)) {
      throw new VectorStoreModelValidationError(
        `Key field must be one of ${Array.from(PostgresCollection.SUPPORTED_KEY_TYPES).join(', ')}, got ${keyField.type_}`
      )
    }

    // Validate vector fields
    for (const field of this.definition.fields) {
      if (field.fieldType === FieldTypes.VECTOR) {
        // Validate vector type
        if (field.type_ && !PostgresCollection.SUPPORTED_VECTOR_TYPES.has(field.type_)) {
          throw new VectorStoreModelValidationError(
            `Vector field ${field.name} must be one of ${Array.from(PostgresCollection.SUPPORTED_VECTOR_TYPES).join(', ')}, got ${field.type_}`
          )
        }

        // Validate dimensions
        if (field.dimensions && field.dimensions > MAX_DIMENSIONALITY) {
          throw new VectorStoreModelValidationError(
            `Dimensionality of ${field.dimensions} exceeds the maximum allowed value of ${MAX_DIMENSIONALITY}.`
          )
        }
      }

      // Validate data field types (if type is specified)
      if (field.fieldType === FieldTypes.DATA && field.type_) {
        // Extract base type if it's an array type
        const baseType = field.type_.replace(/\[\]$/, '').replace(/^Array<(.+)>$/, '$1')
        if (!PostgresCollection.SUPPORTED_DATA_TYPES.has(baseType) && !field.type_.includes('VECTOR')) {
          logger.warn(
            `Data field ${field.name} has type '${field.type_}' which may not be supported by PostgreSQL. ` +
              `Supported types: ${Array.from(PostgresCollection.SUPPORTED_DATA_TYPES).join(', ')}`
          )
        }
      }
    }
  }

  /**
   * Generate a vector embedding from values using the embedding generator
   * @param values The values to generate an embedding for
   * @param options Vector search options including vector property name
   * @returns The generated vector or null if no embedding generator is configured
   */
  private async generateVectorFromValues(values: any, options: VectorSearchOptions): Promise<number[] | null> {
    if (!values || !this.embeddingGenerator) {
      return null
    }

    // Verify the vector field exists
    const vectorField = this.definition.fields.find(
      (f) => f.fieldType === FieldTypes.VECTOR && (!options.vectorPropertyName || f.name === options.vectorPropertyName)
    )

    if (!vectorField) {
      throw new VectorStoreModelValidationError(
        `Vector field '${options.vectorPropertyName || 'default'}' not found in the data model.`
      )
    }

    // Generate embedding
    const embeddings = await this.embeddingGenerator.generateEmbeddings([values])
    return embeddings[0] || null
  }

  /**
   * Upsert records into the database using efficient batch inserts
   * Uses multi-row INSERT statements to minimize round trips to the database
   */
  async upsert(records: TModel[]): Promise<TKey[]> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const keys: TKey[] = []
    const client = await this.connectionPool.connect()

    try {
      await client.query('BEGIN')

      const fields = this.definition.fields
      const keyField = this.definition.fields.find((f) => f.fieldType === FieldTypes.KEY)
      const keyFieldName = keyField?.storageName || keyField?.name || 'id'
      const columnNames = fields.map((f) => f.storageName || f.name)
      const updateColumns = fields.filter((f) => f.name !== this.definition.keyName).map((f) => f.storageName || f.name)

      // Process records in batches
      const maxRows = this.settings.maxRowsPerTransaction
      for (let i = 0; i < records.length; i += maxRows) {
        const batch = records.slice(i, i + maxRows)

        // Convert all records to row values
        const allValues: any[] = []
        const valuePlaceholders: string[] = []

        batch.forEach((record, batchIndex) => {
          const values = convertDictToRow(record, fields)
          allValues.push(...values)

          // Create placeholder group for this record: ($1, $2, $3), ($4, $5, $6), etc.
          const offset = batchIndex * fields.length
          const recordPlaceholders = fields.map((_, idx) => `$${offset + idx + 1}`).join(', ')
          valuePlaceholders.push(`(${recordPlaceholders})`)
        })

        // Build multi-row INSERT statement using pg-format for safe identifier escaping
        const columnList = columnNames.map((col) => format('%I', col)).join(', ')
        const updateSet = updateColumns.map((col) => format('%I = EXCLUDED.%I', col, col)).join(', ')
        const tableName = format('%I.%I', this.dbSchema, this.collectionName)
        const query = `
          INSERT INTO ${tableName} (${columnList})
          VALUES ${valuePlaceholders.join(', ')}
          ON CONFLICT (${format('%I', keyFieldName)}) DO UPDATE SET ${updateSet}
          RETURNING ${format('%I', keyFieldName)}
        `

        const result = await client.query(query, allValues)

        // Extract keys from result
        for (const row of result.rows) {
          keys.push(row[keyFieldName] as TKey)
        }
      }

      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }

    return keys
  }

  /**
   * Get records by keys
   */
  async get(keys: TKey[], options?: GetFilteredRecordOptions): Promise<TModel[] | null> {
    if (!keys || keys.length === 0) {
      if (options?.filter) {
        // Support filtering without keys
        return this.getFiltered(options.filter)
      }
      return null
    }

    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const fields = this.definition.fields
    const selectList = fields.map((f) => format('%I', f.storageName || f.name)).join(', ')
    const keyField = fields.find((f) => f.fieldType === FieldTypes.KEY)
    const keyFieldName = keyField?.storageName || keyField?.name || 'id'

    const placeholders = keys.map((_, idx) => `$${idx + 1}`).join(', ')
    const tableName = format('%I.%I', this.dbSchema, this.collectionName)
    let query = `
      SELECT ${selectList}
      FROM ${tableName}
      WHERE ${format('%I', keyFieldName)} IN (${placeholders})
    `

    // Add additional filter if provided
    if (options?.filter) {
      const filterBuilder = new FilterBuilder(this.definition)
      const whereClause = filterBuilder.buildWhereClause(options.filter)
      query += ` AND ${whereClause}`
    }

    const result = await this.connectionPool.query(query, keys)

    if (!result.rows || result.rows.length === 0) {
      return null
    }

    const fieldTuples: Array<[string, VectorStoreField | null]> = fields.map((f) => [f.storageName || f.name, f])
    return result.rows.map((row) => convertRowToDict(row, fieldTuples) as TModel)
  }

  /**
   * Get records by filter without requiring keys
   */
  private async getFiltered(filter: Filter): Promise<TModel[]> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const fields = this.definition.fields
    const selectList = fields.map((f) => format('%I', f.storageName || f.name)).join(', ')
    const filterBuilder = new FilterBuilder(this.definition)
    const whereClause = filterBuilder.buildWhereClause(filter)

    const tableName = format('%I.%I', this.dbSchema, this.collectionName)
    const query = `
      SELECT ${selectList}
      FROM ${tableName}
      WHERE ${whereClause}
    `

    const result = await this.connectionPool.query(query)

    if (!result.rows || result.rows.length === 0) {
      return []
    }

    const fieldTuples: Array<[string, VectorStoreField | null]> = fields.map((f) => [f.storageName || f.name, f])
    return result.rows.map((row) => convertRowToDict(row, fieldTuples) as TModel)
  }

  /**
   * Get records by filter using async generator (streaming)
   */
  async *getFilteredStream(filter: Filter): AsyncGenerator<TModel> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const fields = this.definition.fields
    const selectList = fields.map((f) => format('%I', f.storageName || f.name)).join(', ')
    const filterBuilder = new FilterBuilder(this.definition)
    const whereClause = filterBuilder.buildWhereClause(filter)

    const tableName = format('%I.%I', this.dbSchema, this.collectionName)
    const query = `
      SELECT ${selectList}
      FROM ${tableName}
      WHERE ${whereClause}
    `

    const client = await this.connectionPool.connect()

    try {
      const cursorName = `filter_cursor_${Date.now()}_${Math.random().toString(36).substring(7)}`
      await client.query('BEGIN')
      await client.query(`DECLARE ${cursorName} CURSOR FOR ${query}`)

      const batchSize = 100
      let hasMore = true
      const fieldTuples: Array<[string, VectorStoreField | null]> = fields.map((f) => [f.storageName || f.name, f])

      while (hasMore) {
        const result = await client.query(`FETCH ${batchSize} FROM ${cursorName}`)

        if (result.rows.length === 0) {
          hasMore = false
        } else {
          for (const row of result.rows) {
            yield convertRowToDict(row, fieldTuples) as TModel
          }

          if (result.rows.length < batchSize) {
            hasMore = false
          }
        }
      }

      await client.query(`CLOSE ${cursorName}`)
      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  /**
   * Delete records by keys
   */
  async delete(keys: TKey[]): Promise<void> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const client = await this.connectionPool.connect()

    try {
      await client.query('BEGIN')

      const maxRows = this.settings.maxRowsPerTransaction
      const keyField = this.definition.fields.find((f) => f.fieldType === FieldTypes.KEY)
      const keyFieldName = keyField?.storageName || keyField?.name || 'id'

      for (let i = 0; i < keys.length; i += maxRows) {
        const batch = keys.slice(i, i + maxRows)
        const placeholders = batch.map((_, idx) => `$${idx + 1}`).join(', ')

        const tableName = format('%I.%I', this.dbSchema, this.collectionName)
        const query = `
          DELETE FROM ${tableName}
          WHERE ${format('%I', keyFieldName)} IN (${placeholders})
        `

        await client.query(query, batch)
      }

      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  /**
   * Ensure the collection (table) exists
   */
  async ensureCollectionExists(): Promise<void> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const columnDefinitions: string[] = []

    for (const field of this.definition.fields) {
      if (!field.type_) {
        throw new VectorStoreModelValidationError(`Property type is not defined for field '${field.name}'`)
      }

      const propertyType = pythonTypeToPostgres(field.type_) || field.type_.toUpperCase()
      const columnName = field.storageName || field.name

      if (field.fieldType === FieldTypes.VECTOR) {
        columnDefinitions.push(format('%I VECTOR(%s)', columnName, field.dimensions))
      } else if (field.fieldType === FieldTypes.KEY) {
        columnDefinitions.push(format('%I %s PRIMARY KEY', columnName, propertyType))
      } else {
        columnDefinitions.push(format('%I %s', columnName, propertyType))
      }
    }

    const columnsStr = columnDefinitions.join(', ')
    const tableName = format('%I.%I', this.dbSchema, this.collectionName)
    const createTableQuery = `
      CREATE TABLE ${tableName} (${columnsStr})
    `

    await this.connectionPool.query(createTableQuery)
    logger.info(`Postgres table '${this.collectionName}' created successfully.`)

    // Create indexes for vector fields
    for (const field of this.definition.fields) {
      if (field.fieldType === FieldTypes.VECTOR) {
        await this.createIndex(this.collectionName, field)
      }
    }
  }

  /**
   * Check if the collection exists
   */
  async collectionExists(): Promise<boolean> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const query = `
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = $1 AND table_name = $2
    `

    const result = await this.connectionPool.query(query, [this.dbSchema, this.collectionName])
    return result.rows.length > 0
  }

  /**
   * Delete the collection (drop table)
   */
  async ensureCollectionDeleted(): Promise<void> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const tableName = format('%I.%I', this.dbSchema, this.collectionName)
    const query = `DROP TABLE ${tableName} CASCADE`
    await this.connectionPool.query(query)
  }

  /**
   * Create an index on a vector column
   */
  private async createIndex(tableName: string, vectorField: VectorStoreField): Promise<void> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const distanceFunction = vectorField.distanceFunction || DistanceFunction.DEFAULT
    const indexKind = vectorField.indexKind || IndexKind.DEFAULT

    if (!(distanceFunction in DISTANCE_FUNCTION_MAP_STRING)) {
      throw new VectorStoreOperationException('Distance function must be set for HNSW indexes.')
    }

    if (!(indexKind in INDEX_KIND_MAP)) {
      throw new VectorStoreOperationException(`Index kind '${indexKind}' is not supported.`)
    }

    if (indexKind === IndexKind.IVFFlat && distanceFunction === DistanceFunction.ManhattanDistance) {
      throw new VectorStoreOperationException('IVF_FLAT index is not supported with MANHATTAN distance function.')
    }

    const columnName = vectorField.storageName || vectorField.name
    const indexName = `${tableName}_${columnName}_idx`
    const indexKindStr = INDEX_KIND_MAP[indexKind]
    const distanceOp = DISTANCE_FUNCTION_MAP_STRING[distanceFunction]

    const fullTableName = format('%I.%I', this.dbSchema, tableName)
    const query = format(
      'CREATE INDEX %I ON %s USING %s (%I %s)',
      indexName,
      fullTableName,
      indexKindStr,
      columnName,
      distanceOp
    )

    await this.connectionPool.query(query)
    logger.info(`Index '${indexName}' created successfully on column '${columnName}'.`)
  }

  /**
   * Vector similarity search
   *
   * @param vector - The query vector (or null if using options.values for embedding generation)
   * @param options - Search options including filter, top, skip, values for embedding generation, etc.
   * @returns Search results with optional total count
   */
  async search(
    vector: number[] | null,
    options: VectorSearchOptions = {}
  ): Promise<KernelSearchResults<VectorSearchResult<TModel>>> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    // Generate vector from values if provided
    let searchVector = vector
    if (!searchVector && options.values) {
      searchVector = await this.generateVectorFromValues(options.values, options)
      if (!searchVector) {
        throw new VectorStoreOperationException(
          'No embedding generator configured. Either provide a vector directly or configure an embedding generator.'
        )
      }
    }

    if (!searchVector) {
      throw new VectorStoreOperationException('Either vector or options.values must be provided for search.')
    }

    const { query, params, returnFields } = this.constructVectorQuery(searchVector, options)

    // If total count is needed, we must fetch all results
    if (options.includeTotalCount) {
      const result = await this.connectionPool.query(query, params)
      const rows = result.rows.map((row) => convertRowToDict(row, returnFields))
      const results = rows.map((row) => this.getVectorSearchResultFromRow(row))
      return new KernelSearchResults(results, results.length)
    }

    // Use streaming if requested or by default when total count not needed
    if (options.useStreaming !== false) {
      const resultsGenerator = this.searchStream(searchVector, options)
      return new KernelSearchResults(resultsGenerator)
    }

    // Fallback to fetching all results at once
    const result = await this.connectionPool.query(query, params)
    const rows = result.rows.map((row) => convertRowToDict(row, returnFields))
    const results = rows.map((row) => this.getVectorSearchResultFromRow(row))
    return new KernelSearchResults(results)
  }

  /**
   * Vector similarity search with streaming results (async generator)
   *
   * This method is memory-efficient for large result sets as it streams
   * results one at a time instead of loading everything into memory.
   *
   * @param vector - The query vector
   * @param options - Search options including filter, top, skip, etc.
   * @returns Async generator of search results
   *
   * @example
   * ```typescript
   * for await (const result of collection.searchStream(vector, { top: 1000 })) {
   *   console.log(result.record, result.score)
   * }
   * ```
   */
  async *searchStream(vector: number[], options: VectorSearchOptions = {}): AsyncGenerator<VectorSearchResult<TModel>> {
    if (!this.connectionPool) {
      throw new VectorStoreOperationException('Connection pool is not available, please call connect() first.')
    }

    const { query, params, returnFields } = this.constructVectorQuery(vector, options)
    const client = await this.connectionPool.connect()

    try {
      // Create a cursor for streaming
      const cursorName = `search_cursor_${Date.now()}_${Math.random().toString(36).substring(7)}`
      await client.query('BEGIN')
      await client.query(`DECLARE ${cursorName} CURSOR FOR ${query}`, params)

      // Fetch results in batches and yield one by one
      const batchSize = 100
      let hasMore = true

      while (hasMore) {
        const result = await client.query(`FETCH ${batchSize} FROM ${cursorName}`)

        if (result.rows.length === 0) {
          hasMore = false
        } else {
          for (const row of result.rows) {
            const dict = convertRowToDict(row, returnFields)
            yield this.getVectorSearchResultFromRow(dict)
          }

          if (result.rows.length < batchSize) {
            hasMore = false
          }
        }
      }

      await client.query(`CLOSE ${cursorName}`)
      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  private constructVectorQuery(
    vector: number[],
    options: VectorSearchOptions
  ): { query: string; params: any[]; returnFields: Array<[string, VectorStoreField | null]> } {
    // Find the vector field
    const vectorField = this.definition.fields.find(
      (f) => f.fieldType === FieldTypes.VECTOR && (!options.vectorPropertyName || f.name === options.vectorPropertyName)
    )

    if (!vectorField) {
      throw new VectorStoreModelValidationError(
        `Vector field '${options.vectorPropertyName}' not found in the data model.`
      )
    }

    const distanceFunction = vectorField.distanceFunction || DistanceFunction.DEFAULT
    if (!(distanceFunction in DISTANCE_FUNCTION_MAP_OPS)) {
      throw new VectorStoreOperationException(`Distance function '${distanceFunction}' is not supported.`)
    }

    // Build select list
    const selectFields = this.definition.fields.filter(
      (f) => options.includeVectors || f.fieldType !== FieldTypes.VECTOR
    )
    const selectList = selectFields.map((f) => format('%I', f.storageName || f.name)).join(', ')
    const vectorColumnName = vectorField.storageName || vectorField.name
    const distanceOp = DISTANCE_FUNCTION_MAP_OPS[distanceFunction]
    const tableName = format('%I.%I', this.dbSchema, this.collectionName)

    let query = `
      SELECT ${selectList}, ${format('%I', vectorColumnName)} ${distanceOp} $1 as ${format('%I', this.distanceColumnName)}
      FROM ${tableName}
    `

    // Add WHERE clause if filter exists
    if (options.filter) {
      const filterBuilder = new FilterBuilder(this.definition)
      const whereClause = filterBuilder.buildWhereClause(options.filter)
      query += ` WHERE ${whereClause}`
    }

    query += ` ORDER BY ${format('%I', this.distanceColumnName)} LIMIT ${options.top || 10}`

    if (options.skip) {
      query += ` OFFSET ${options.skip}`
    }

    // Handle cosine similarity transformation
    if (distanceFunction === DistanceFunction.CosineSimilarity) {
      query = `
        SELECT subquery.*, 1 - subquery.${format('%I', this.distanceColumnName)} AS ${format('%I', this.distanceColumnName)}
        FROM (${query}) AS subquery
      `
    }

    // Handle dot product transformation
    if (distanceFunction === DistanceFunction.DotProduct) {
      query = `
        SELECT subquery.*, -1 * subquery.${format('%I', this.distanceColumnName)} AS ${format('%I', this.distanceColumnName)}
        FROM (${query}) AS subquery
      `
    }

    const vectorStr = '[' + vector.map((v) => String(v)).join(',') + ']'
    const params = [vectorStr]

    const returnFields: Array<[string, VectorStoreField | null]> = [
      ...selectFields.map((f): [string, VectorStoreField | null] => [f.storageName || f.name, f]),
      [this.distanceColumnName, null],
    ]

    return { query, params, returnFields }
  }

  private getVectorSearchResultFromRow(row: Record<string, any>): VectorSearchResult<TModel> {
    const score = row[this.distanceColumnName]
    const record = { ...row }
    delete record[this.distanceColumnName]

    return {
      record: record as TModel,
      score,
    }
  }
}

// region: Store

export class PostgresStore {
  connectionPool: Pool
  dbSchema: string = DEFAULT_SCHEMA
  tables?: string[]

  constructor(connectionPool: Pool, dbSchema: string = DEFAULT_SCHEMA, tables?: string[]) {
    this.connectionPool = connectionPool
    this.dbSchema = dbSchema
    this.tables = tables
  }

  async listCollectionNames(): Promise<string[]> {
    let query = `
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = $1
    `
    const params: any[] = [this.dbSchema]

    if (this.tables && this.tables.length > 0) {
      const placeholders = this.tables.map((_, idx) => `$${idx + 2}`).join(', ')
      query += ` AND table_name IN (${placeholders})`
      params.push(...this.tables)
    }

    const result = await this.connectionPool.query(query, params)
    return result.rows.map((row) => row.table_name)
  }

  getCollection<TKey extends string | number, TModel extends Record<string, any>>(options: {
    recordType: new () => TModel
    definition?: VectorStoreCollectionDefinition
    collectionName?: string
  }): PostgresCollection<TKey, TModel> {
    return new PostgresCollection({
      ...options,
      connectionPool: this.connectionPool,
      dbSchema: this.dbSchema,
    })
  }
}
