// Copyright (c) Microsoft. All rights reserved.

import { ContentAdditionException } from '../exceptions/content-exceptions'

/**
 * Mixin class for all streaming kernel contents.
 */
export abstract class StreamingContentMixin {
  /**
   * The choice index of the streaming content.
   */
  public choiceIndex: number

  /**
   * Creates a new StreamingContentMixin instance.
   * @param choiceIndex - The choice index.
   */
  constructor(choiceIndex: number) {
    this.choiceIndex = choiceIndex
  }

  /**
   * Return the content of the response encoded as bytes.
   */
  public abstract toBytes(): Uint8Array

  /**
   * Combine two streaming contents together.
   * @param other - The other streaming content to add.
   * @returns A new instance with the combined content.
   */
  public abstract add(other: any): this

  /**
   * Create a new list with the items of the current instance and the given list.
   * @param otherItems - The list of items to merge.
   * @returns A new list with merged items.
   * @throws ContentAdditionException if the instance doesn't have an items property.
   */
  protected _mergeItemsLists(otherItems: any[]): any[] {
    if (!('items' in this)) {
      throw new ContentAdditionException(`Cannot merge items for this instance of type: ${this.constructor.name}`)
    }

    // Create a copy of the items list to avoid modifying the original instance.
    // Note that the items are not copied, only the list is.
    const items = (this as any).items as any[]
    const newItemsList = [...items]

    if (newItemsList.length > 0 || otherItems.length > 0) {
      for (const otherItem of otherItems) {
        let added = false
        for (let id = 0; id < newItemsList.length; id++) {
          const item = newItemsList[id]
          if (item.constructor === otherItem.constructor && typeof item.add === 'function') {
            try {
              const newItem = item.add(otherItem)
              newItemsList[id] = newItem
              added = true
              break
            } catch (ex) {
              if (ex instanceof ValueError || ex instanceof ContentAdditionException) {
                console.debug(`Could not add item ${otherItem} to ${item}.`, ex)
                continue
              }
              throw ex
            }
          }
        }
        if (!added) {
          console.debug(`Could not add item ${otherItem} to any item in the list. Adding it as a new item.`)
          newItemsList.push(otherItem)
        }
      }
    }

    return newItemsList
  }

  /**
   * Create a new list with the inner content of the current instance and the given one.
   * @param otherInnerContent - The inner content to merge (can be a single item or array).
   * @returns A new list with merged inner contents.
   * @throws ContentAdditionException if the instance doesn't have an innerContent property.
   */
  protected _mergeInnerContents(otherInnerContent: any | any[]): any[] {
    if (!('innerContent' in this)) {
      throw new ContentAdditionException(
        `Cannot merge inner content for this instance of type: ${this.constructor.name}`
      )
    }

    // Create a copy of the inner content list to avoid modifying the original instance.
    // Note that the inner content is not copied, only the list is.
    // If the inner content is not a list, it is converted to a list.
    const innerContent = (this as any).innerContent
    const newInnerContentsList = Array.isArray(innerContent) ? [...innerContent] : [innerContent]

    const otherInnerContentArray = Array.isArray(otherInnerContent)
      ? otherInnerContent
      : otherInnerContent
        ? [otherInnerContent]
        : []

    newInnerContentsList.push(...otherInnerContentArray)

    return newInnerContentsList
  }
}

/**
 * Custom ValueError for validation errors.
 */
class ValueError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValueError'
  }
}
