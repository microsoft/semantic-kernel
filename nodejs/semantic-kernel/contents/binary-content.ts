import { existsSync, readFileSync, statSync, writeFileSync } from 'fs'
import { BINARY_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * Data URI utility class for handling data URIs.
 */
class DataUri {
  dataBytes?: Buffer
  dataString?: string
  dataFormat?: string
  mimeType: string
  parameters: Record<string, string>

  constructor(options: {
    dataBytes?: Buffer
    dataString?: string
    dataFormat?: string
    mimeType?: string
    parameters?: Record<string, string>
  }) {
    this.dataBytes = options.dataBytes
    this.dataString = options.dataString
    this.dataFormat = options.dataFormat || 'base64'
    this.mimeType = options.mimeType || 'text/plain'
    this.parameters = options.parameters || {}
  }

  static fromDataUri(dataUri: string, defaultMimeType: string = 'text/plain'): DataUri {
    // Parse data URI: data:[<mediatype>][;base64],<data>
    const match = dataUri.match(/^data:([^;,]+)?(;base64)?,(.*)$/)
    if (!match) {
      throw new Error('Invalid data URI format')
    }

    const [, mimeType = defaultMimeType, encoding, data] = match
    const dataFormat = encoding ? 'base64' : undefined
    const dataBytes = encoding ? Buffer.from(data, 'base64') : Buffer.from(data)

    return new DataUri({
      dataBytes,
      dataFormat,
      mimeType,
    })
  }

  toString(_metadata?: Record<string, any>): string {
    if (!this.dataBytes && !this.dataString) {
      return ''
    }

    const data = this.dataBytes
      ? this.dataBytes.toString((this.dataFormat as BufferEncoding) || 'base64')
      : this.dataString || ''

    const encoding = this.dataFormat === 'base64' ? ';base64' : ''
    return `data:${this.mimeType}${encoding},${data}`
  }

  getDataString(): string {
    if (this.dataString) {
      return this.dataString
    }
    if (this.dataBytes) {
      return this.dataBytes.toString((this.dataFormat as BufferEncoding) || 'base64')
    }
    return ''
  }

  updateData(value: string | Buffer): void {
    if (typeof value === 'string') {
      this.dataString = value
      this.dataBytes = undefined
    } else {
      this.dataBytes = value
      this.dataString = undefined
    }
  }
}

/**
 * Base class for different types of binary content.
 *
 * This can be created either with bytes data or a data URI, and can optionally have a reference URI.
 * The uri is a reference to the source and might or might not point to the same thing as the data.
 *
 * Ideally only subclasses of this class are used, like AudioContent or ImageContent.
 */
export abstract class BinaryContent extends KernelContent {
  readonly contentType: string = BINARY_CONTENT_TAG
  readonly tag: string = BINARY_CONTENT_TAG
  uri?: string
  private _dataUri?: DataUri
  protected defaultMimeType: string = 'text/plain'

  constructor(
    options: {
      uri?: string
      dataUri?: string
      data?: string | Buffer
      dataFormat?: string
      mimeType?: string
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { uri, dataUri, data, dataFormat, mimeType, innerContent, aiModelId, metadata = {} } = options

    // Call super first before accessing 'this'
    super({ innerContent, aiModelId, metadata })

    let tempDataUri: DataUri | undefined

    if (dataUri) {
      tempDataUri = DataUri.fromDataUri(dataUri, this.defaultMimeType)
      Object.assign(metadata, tempDataUri.parameters)
    } else if (data !== undefined) {
      if (Buffer.isBuffer(data)) {
        tempDataUri = new DataUri({
          dataBytes: data,
          dataFormat,
          mimeType: mimeType || this.defaultMimeType,
        })
      } else if (typeof data === 'string') {
        tempDataUri = new DataUri({
          dataString: data,
          dataFormat,
          mimeType: mimeType || this.defaultMimeType,
        })
      }
    }

    // Validate URI if provided
    const validatedUri = uri
    if (uri && existsSync(uri)) {
      const stats = statSync(uri)
      if (!stats.isFile()) {
        throw new Error('URI must be a file path, not a directory.')
      }
    }

    this.uri = validatedUri
    this._dataUri = tempDataUri
  }

  /**
   * Get the data URI.
   */
  get dataUri(): string {
    if (this._dataUri) {
      return this._dataUri.toString(this.metadata)
    }
    return ''
  }

  /**
   * Set the data URI.
   */
  set dataUri(value: string) {
    if (!this._dataUri) {
      this._dataUri = DataUri.fromDataUri(value, this.defaultMimeType)
    } else {
      this._dataUri.updateData(value)
    }
    if (this._dataUri.parameters) {
      Object.assign(this.metadata, this._dataUri.parameters)
    }
  }

  /**
   * Returns the data as a string, using the data format.
   */
  get dataString(): string {
    if (this._dataUri) {
      return this._dataUri.getDataString()
    }
    return ''
  }

  /**
   * Get the data as bytes.
   */
  get data(): Buffer {
    if (this._dataUri && this._dataUri.dataBytes) {
      return this._dataUri.dataBytes
    }
    return Buffer.alloc(0)
  }

  /**
   * Set the data.
   */
  set data(value: string | Buffer) {
    if (this._dataUri) {
      this._dataUri.updateData(value)
      return
    }

    if (Buffer.isBuffer(value)) {
      this._dataUri = new DataUri({
        dataBytes: value,
        mimeType: this.mimeType,
      })
    } else if (typeof value === 'string') {
      this._dataUri = new DataUri({
        dataString: value,
        mimeType: this.mimeType,
      })
    } else {
      throw new Error('Data must be a string or Buffer.')
    }
  }

  /**
   * Get the MIME type.
   */
  get mimeType(): string {
    if (this._dataUri && this._dataUri.mimeType) {
      return this._dataUri.mimeType
    }
    return this.defaultMimeType
  }

  /**
   * Set the MIME type.
   */
  set mimeType(value: string) {
    if (this._dataUri) {
      this._dataUri.mimeType = value
    }
  }

  /**
   * Get whether the content can be read.
   * Returns true if the content has data available for reading.
   */
  get canRead(): boolean {
    return this._dataUri !== undefined
  }

  /**
   * Create BinaryContent from a file.
   */
  static fromFile<T extends BinaryContent>(this: new (options: any) => T, filePath: string, mimeType?: string): T {
    if (!existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`)
    }

    const stats = statSync(filePath)
    if (!stats.isFile()) {
      throw new Error(`Path is not a file: ${filePath}`)
    }

    const data = readFileSync(filePath)

    return new this({
      data,
      mimeType,
      uri: filePath,
      dataFormat: 'base64',
    })
  }

  /**
   * Return the string representation of the content.
   */
  toString(): string {
    return this._dataUri ? this.dataUri : this.uri || ''
  }

  /**
   * Convert the instance to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; text?: string } {
    const element: { tag: string; attributes: Record<string, string>; text?: string } = {
      tag: this.tag,
      attributes: {},
    }

    if (this._dataUri) {
      element.text = this.dataUri
    }
    if (this.uri) {
      element.attributes.uri = this.uri
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement<T extends BinaryContent>(
    this: new (options: any) => T,
    element: { tag: string; attributes: Record<string, string>; text?: string }
  ): T {
    if (element.tag !== BINARY_CONTENT_TAG) {
      throw new Error(`Element tag is not ${BINARY_CONTENT_TAG}`)
    }

    if (element.text) {
      return new this({
        dataUri: element.text,
        uri: element.attributes.uri,
      })
    }

    return new this({
      uri: element.attributes.uri,
    })
  }

  /**
   * Write the data to a file.
   */
  writeToFile(path: string): void {
    writeFileSync(path, this.data)
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    return {
      type: 'binary',
      binary: { uri: this.toString() },
    }
  }
}
