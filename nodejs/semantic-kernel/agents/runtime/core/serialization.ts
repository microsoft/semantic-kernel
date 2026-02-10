import { Message } from 'google-protobuf'
import { Any as AnyProto } from 'google-protobuf/google/protobuf/any_pb'

/**
 * Content type constants
 */
export const JSON_DATA_CONTENT_TYPE = 'application/json'
export const PROTOBUF_DATA_CONTENT_TYPE = 'application/x-protobuf'

/**
 * Serializer interface for messages.
 */
export interface MessageSerializer<T> {
  /**
   * Content type of the data being serialized.
   */
  readonly dataContentType: string

  /**
   * Type name of the message being serialized.
   */
  readonly typeName: string

  /**
   * Deserialize the payload into a message.
   */
  deserialize(payload: Uint8Array): T

  /**
   * Serialize the message into a payload.
   */
  serialize(message: T): Uint8Array
}

/**
 * Serializer for plain JavaScript objects/classes using JSON.
 */
export class JsonMessageSerializer<T extends Record<string, any>> implements MessageSerializer<T> {
  private readonly _cls: new (...args: any[]) => T
  private readonly _typeName: string

  /**
   * Initialize the serializer with a class type.
   * @param cls - The class constructor
   * @param typeName - Optional custom type name (defaults to class name)
   */
  constructor(cls: new (...args: any[]) => T, typeName?: string) {
    this._cls = cls
    this._typeName = typeName ?? getTypeName(cls)
  }

  get dataContentType(): string {
    return JSON_DATA_CONTENT_TYPE
  }

  get typeName(): string {
    return this._typeName
  }

  deserialize(payload: Uint8Array): T {
    const messageStr = new TextDecoder().decode(payload)
    const data = JSON.parse(messageStr)
    return new this._cls(data)
  }

  serialize(message: T): Uint8Array {
    const jsonStr = JSON.stringify(message)
    return new TextEncoder().encode(jsonStr)
  }
}

/**
 * Serializer for Protobuf messages.
 */
export class ProtobufMessageSerializer<T extends Message> implements MessageSerializer<T> {
  private readonly _cls: new () => T
  private readonly _typeName: string

  /**
   * Initialize the serializer with a Protobuf message type.
   * @param cls - The Protobuf message constructor
   */
  constructor(cls: new () => T) {
    this._cls = cls
    this._typeName = getTypeName(cls)
  }

  get dataContentType(): string {
    return PROTOBUF_DATA_CONTENT_TYPE
  }

  get typeName(): string {
    return this._typeName
  }

  deserialize(payload: Uint8Array): T {
    // Parse payload into a proto Any
    const anyProto = AnyProto.deserializeBinary(payload)

    // Create destination message
    const destinationMessage = new this._cls()

    // Unpack the Any message
    if (!anyProto.unpack((destinationMessage as any).deserializeBinary.bind(destinationMessage), this.typeName)) {
      throw new Error(`Failed to unpack payload into ${this.typeName}`)
    }

    return destinationMessage
  }

  serialize(message: T): Uint8Array {
    const anyProto = new AnyProto()
    anyProto.pack(message.serializeBinary(), this.typeName)
    return anyProto.serializeBinary()
  }
}

/**
 * Class to represent an unknown payload.
 */
export class UnknownPayload {
  constructor(
    public readonly typeName: string,
    public readonly dataContentType: string,
    public readonly payload: Uint8Array
  ) {}
}

/**
 * Get the type name of a class or message.
 */
function getTypeName(cls: any): string {
  // For Protobuf messages, try to get the descriptor full name
  if (cls.prototype instanceof Message) {
    // In google-protobuf for JavaScript, descriptors are accessed differently
    // Try to get the descriptor if available
    const descriptor = (cls as any).DESCRIPTOR
    if (descriptor && descriptor.full_name) {
      return descriptor.full_name
    }
    // Fallback to class name
    return cls.name
  }

  // For regular classes, use the constructor name
  if (typeof cls === 'function') {
    return cls.name
  }

  // For instances, check if it's a protobuf message instance
  if (cls instanceof Message) {
    const descriptor = (cls as any).DESCRIPTOR
    if (descriptor && descriptor.full_name) {
      return descriptor.full_name
    }
  }

  // Default to class name
  return cls.constructor.name
}

/**
 * Try to get known serializers for a type.
 */
export function tryGetKnownSerializersForType<T>(cls: new (...args: any[]) => T): MessageSerializer<any>[] {
  const serializers: MessageSerializer<any>[] = []

  // Check if it's a Protobuf message
  if (cls.prototype instanceof Message) {
    serializers.push(new ProtobufMessageSerializer(cls as any))
  } else {
    // Assume it's a plain object/class that can be JSON serialized
    serializers.push(new JsonMessageSerializer(cls as any))
  }

  return serializers
}

/**
 * Serialization registry for messages.
 */
export class SerializationRegistry {
  private readonly _serializers: Map<string, MessageSerializer<any>> = new Map()

  /**
   * Add a new serializer to the registry.
   */
  addSerializer(serializer: MessageSerializer<any> | MessageSerializer<any>[]): void {
    if (Array.isArray(serializer)) {
      for (const s of serializer) {
        this.addSerializer(s)
      }
      return
    }

    const key = this._makeKey(serializer.typeName, serializer.dataContentType)
    this._serializers.set(key, serializer)
  }

  /**
   * Deserialize a payload into a message.
   */
  deserialize(payload: Uint8Array, options: { typeName: string; dataContentType: string }): any {
    const key = this._makeKey(options.typeName, options.dataContentType)
    const serializer = this._serializers.get(key)

    if (!serializer) {
      return new UnknownPayload(options.typeName, options.dataContentType, payload)
    }

    return serializer.deserialize(payload)
  }

  /**
   * Serialize a message into a payload.
   */
  serialize(message: any, options: { typeName: string; dataContentType: string }): Uint8Array {
    const key = this._makeKey(options.typeName, options.dataContentType)
    const serializer = this._serializers.get(key)

    if (!serializer) {
      throw new Error(`Unknown type ${options.typeName} with content type ${options.dataContentType}`)
    }

    return serializer.serialize(message)
  }

  /**
   * Check if a type is registered in the registry.
   */
  isRegistered(typeName: string, dataContentType: string): boolean {
    const key = this._makeKey(typeName, dataContentType)
    return this._serializers.has(key)
  }

  /**
   * Get the type name of a message.
   */
  getTypeName(message: any): string {
    return getTypeName(message)
  }

  private _makeKey(typeName: string, dataContentType: string): string {
    return `${typeName}::${dataContentType}`
  }
}
