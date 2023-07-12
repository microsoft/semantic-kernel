import {
    PluginManifest,
    PluginManifestKeys,
    isHttpAuthorizationType,
    isManifestAuthType,
} from '../models/PluginManifest';

export const isValidPluginManifest = (manifest: PluginManifest) => {
    const missingKeys: string[] = [];

    PluginManifestKeys.forEach((key) => {
        if (!(key in manifest)) {
            missingKeys.push(key);
        }
    });

    if (missingKeys.length > 0) {
        throw new Error(`Plugin manifest is missing the following keys: ${missingKeys.toLocaleString()}`);
    }

    // Check that the auth type is valid
    const authType = manifest.auth.type;
    if (!isManifestAuthType(manifest.auth.type)) {
        throw new Error(`Invalid auth type: ${authType}`);
    }

    // Check that the auth properties match the auth type
    if (authType === 'user_http') {
        if (!('authorization_type' in manifest.auth)) {
            throw new Error('Missing authorization_type for user_http auth');
        }
        const authHttpType = manifest.auth.authorization_type;
        if (!isHttpAuthorizationType(authHttpType)) {
            throw new Error(`Invalid authorization_type for user_http auth: ${authHttpType as string}`);
        }
    }

    // Check that the api type is valid
    const apiType = manifest.api.type;
    if ((apiType as unknown) !== 'openapi') {
        throw new Error(`Invalid api type: ${apiType as string}`);
    }

    // Check that the api url is valid
    const apiUrl = manifest.api.url;
    if (!apiUrl.startsWith('http')) {
        throw new Error(`Invalid api url: ${apiUrl}`);
    } else {
        try {
            new URL(apiUrl);
        } catch {
            throw new Error(`Invalid api url: ${apiUrl}`);
        }
    }

    // If no errors are thrown, the plugin manifest is valid
    return true;
};

export const isValidOpenAPISpec = (_specPath: string) => {
    // TODO: verify openAPI spec
    return true;
};
