// This file makes Jest globals available to all test files without explicit imports
import '@jest/globals'

declare global {
  // Re-export Jest globals to the global scope
  const describe: typeof import('@jest/globals').describe
  const test: typeof import('@jest/globals').test
  const it: typeof import('@jest/globals').it
  const expect: typeof import('@jest/globals').expect
  const beforeAll: typeof import('@jest/globals').beforeAll
  const afterAll: typeof import('@jest/globals').afterAll
  const beforeEach: typeof import('@jest/globals').beforeEach
  const afterEach: typeof import('@jest/globals').afterEach
  const jest: typeof import('@jest/globals').jest
}

export {}
