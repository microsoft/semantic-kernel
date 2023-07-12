type HttpAuthorizationType = 'bearer';
export function isHttpAuthorizationType(value: unknown): value is HttpAuthorizationType {
    return value === 'bearer';
}

type ManifestAuthType = 'none' | 'user_http';
export function isManifestAuthType(value: unknown): value is ManifestAuthType {
    return (value as ManifestAuthType) === 'none' || value === 'user_http';
}

interface BaseManifestAuth {
    type: ManifestAuthType;
    instructions?: string;
}

interface ManifestNoAuth extends BaseManifestAuth {
    type: 'none';
}

interface ManifestUserHttpAuth extends BaseManifestAuth {
    type: 'user_http';
    authorization_type: HttpAuthorizationType;
}

type ManifestAuth = ManifestNoAuth | ManifestUserHttpAuth;

interface ManifestApi {
    type: 'openapi';
    url: string;
}

// Define the class for the plugin manifest
export interface PluginManifest {
    schema_version: string;
    name_for_model: string;
    name_for_human: string;
    description_for_model: string;
    description_for_human: string;
    auth: ManifestAuth;
    api: ManifestApi;
    logo_url: string;
    contact_email: string;
    legal_info_url: string;
}

export const PluginManifestKeys = [
    'schema_version',
    'name_for_model',
    'name_for_human',
    'description_for_model',
    'description_for_human',
    'auth',
    'api',
    'logo_url',
    'contact_email',
    'legal_info_url',
];
