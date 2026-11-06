import { experimental } from '../../../utils/feature-stage-decorator'

/**
 * A token used to cancel pending async calls.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class CancellationToken {
  private _cancelled: boolean = false
  private _callbacks: Array<() => void> = []

  /**
   * Cancel pending async calls linked to this cancellation token.
   */
  cancel(): void {
    if (!this._cancelled) {
      this._cancelled = true
      for (const callback of this._callbacks) {
        callback()
      }
    }
  }

  /**
   * Check if the CancellationToken has been used.
   */
  isCancelled(): boolean {
    return this._cancelled
  }

  /**
   * Attach a callback that will be called when cancel is invoked.
   */
  addCallback(callback: () => void): void {
    if (this._cancelled) {
      callback()
    } else {
      this._callbacks.push(callback)
    }
  }

  /**
   * Link a pending async call to a token to allow its cancellation.
   */
  linkPromise<T>(promise: Promise<T>): Promise<T> {
    if (this._cancelled) {
      return Promise.reject(new Error('Operation cancelled'))
    }

    return new Promise<T>((resolve, reject) => {
      this.addCallback(() => {
        reject(new Error('Operation cancelled'))
      })

      promise.then(resolve, reject)
    })
  }
}
