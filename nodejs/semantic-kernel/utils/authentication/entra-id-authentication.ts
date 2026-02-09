import { AccessToken, TokenCredential } from '@azure/identity'

/**
 * Retrieve a Microsoft Entra Auth Token for a given token endpoint.
 *
 * The token endpoint may be specified as an environment variable, via the .env
 * file or as an argument. If the token endpoint is not provided, an error is thrown.
 *
 * @param credential - The credential to use to retrieve the authentication token
 * @param tokenEndpoint - The token endpoint to use to retrieve the authentication token
 * @returns The Azure token or null if the token could not be retrieved
 * @throws Error if token endpoint is not provided
 */
export async function getEntraAuthToken(credential: TokenCredential, tokenEndpoint: string): Promise<string | null> {
  if (!tokenEndpoint) {
    throw new Error(
      'A token endpoint must be provided either in settings, as an environment variable, or as an argument.'
    )
  }

  try {
    const authToken: AccessToken | null = await credential.getToken(tokenEndpoint)
    return authToken ? authToken.token : null
  } catch (error) {
    console.error(`Failed to retrieve Azure token for the specified endpoint: ${tokenEndpoint}.`, error)
    return null
  }
}
