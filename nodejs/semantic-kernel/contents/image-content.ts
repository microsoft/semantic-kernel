import { readFileSync } from 'fs'
import { lookup } from 'mime-types'
import { BinaryContent } from './binary-content'
import { IMAGE_CONTENT_TAG } from './const'

/**
 * Image Content class.
 *
 * This can be created either with bytes data or a data URI, additionally it can have a URI.
 * The URI is a reference to the source, and might or might not point to the same thing as the data.
 *
 * Use the .fromImageFile method to create an instance from an image file.
 * This reads the file and guesses the MIME type.
 *
 * If both dataUri and data is provided, data will be used.
 */
export class ImageContent extends BinaryContent {
  readonly contentType: string = IMAGE_CONTENT_TAG
  readonly tag: string = IMAGE_CONTENT_TAG

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
    super(options)
  }

  /**
   * Create an instance from an image file path.
   * @deprecated Use fromImageFile instead.
   */
  static fromImagePath(path: string): ImageContent {
    return this.fromImageFile(path)
  }

  /**
   * Create an instance from an image file.
   *
   * @param path - Path to the image file
   * @returns ImageContent instance with the file data
   */
  static fromImageFile(path: string): ImageContent {
    const mimeType = lookup(path) || undefined
    const data = readFileSync(path)

    return new ImageContent({
      data,
      dataFormat: 'base64',
      mimeType,
      uri: path,
    })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    return {
      type: 'image_url',
      image_url: { url: this.toString() },
    }
  }
}
