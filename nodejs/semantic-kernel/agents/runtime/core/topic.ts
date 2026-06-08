import { experimental } from '../../../utils/feature-stage-decorator'

const TOPIC_TYPE_REGEX = /^[\w\-.:=]+$/

/**
 * Check if the given value is a valid topic type.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function isValidTopicType(value: string): boolean {
  return TOPIC_TYPE_REGEX.test(value)
}

/**
 * TopicId defines the scope of a broadcast message.
 *
 * In essence, agent runtime implements a publish-subscribe model through its broadcast API: when publishing a message,
 * the topic must be specified.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class TopicId {
  /**
   * Type of the event that this topic_id contains. Adheres to the cloud event spec.
   *
   * Must match the pattern: ^[\\w\\-\\.\\:\\=]+$
   *
   * Learn more here: https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md#type
   */
  readonly type: string

  /**
   * Identifies the context in which an event happened. Adheres to the cloud event spec.
   *
   * Learn more here: https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md#source-1
   */
  readonly source: string

  constructor(type: string, source: string) {
    if (!isValidTopicType(type)) {
      throw new Error(`Invalid topic type: ${type}. Must match the pattern: ^[\\w\\-\\.\\:\\=]+$`)
    }
    this.type = type
    this.source = source
  }

  /**
   * Convert a string of the format `type/source` into a TopicId.
   */
  static fromString(topicId: string): TopicId {
    const items = topicId.split('/', 2)
    if (items.length !== 2) {
      throw new Error(`Invalid topic id: ${topicId}`)
    }
    const [type, source] = items
    return new TopicId(type, source)
  }

  /**
   * Convert the TopicId to a string.
   */
  toString(): string {
    return `${this.type}/${this.source}`
  }
}
