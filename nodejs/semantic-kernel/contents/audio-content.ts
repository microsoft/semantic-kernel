import { readFileSync } from 'fs'
import { lookup } from 'mime-types'
import { BinaryContent } from './binary-content'
import { AUDIO_CONTENT_TAG } from './const'

/**
 * Audio Content class.
 *
 * This can be created either with bytes data or a data URI, additionally it can have a URI.
 * The URI is a reference to the source, and might or might not point to the same thing as the data.
 *
 * Use the .fromAudioFile method to create an instance from an audio file.
 * This reads the file and guesses the MIME type.
 *
 * If both dataUri and data is provided, data will be used.
 */
export class AudioContent extends BinaryContent {
  readonly contentType: string = AUDIO_CONTENT_TAG
  readonly tag: string = AUDIO_CONTENT_TAG

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
   * Create an instance from an audio file.
   *
   * @param path - Path to the audio file
   * @returns AudioContent instance with the file data
   */
  static fromAudioFile(path: string): AudioContent {
    const mimeType = lookup(path) || undefined
    const data = readFileSync(path)

    return new AudioContent({
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
      type: 'audio_url',
      audio_url: { url: this.toString() },
    }
  }
}
