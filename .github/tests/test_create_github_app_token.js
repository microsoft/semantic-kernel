// Copyright (c) Microsoft. All rights reserved.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const {
  base64ToBase64Url,
  createInstallationToken,
  createJwtSigningInput,
  readConfig,
} = require('../actions/github-app-token/create-token.js');

const CONFIG = {
  azureSubscriptionId: 'subscription-id',
  keyVaultName: 'vault-name',
  keyName: 'key-name',
  githubAppClientId: 'client-id',
  githubAppInstallationId: '12345',
  targetRepository: 'microsoft/semantic-kernel',
  permissionProfile: 'devflow',
};

describe('GitHub App token creation', () => {
  it('creates a short-lived GitHub App JWT', () => {
    const signingInput = createJwtSigningInput('client-id', 1_000);
    const [encodedHeader, encodedPayload] = signingInput.split('.');
    const header = JSON.parse(Buffer.from(encodedHeader, 'base64url').toString());
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString());

    assert.deepEqual(header, { alg: 'RS256', typ: 'JWT' });
    assert.deepEqual(payload, { iat: 940, exp: 1_540, iss: 'client-id' });
  });

  it('converts Key Vault signatures to unpadded base64url', () => {
    assert.equal(base64ToBase64Url('+/8='), '-_8');
  });

  it('requests a repository-scoped installation token', async () => {
    let request;
    const token = await createInstallationToken(CONFIG, {
      nowSeconds: 1_000,
      execute: (command, args) => {
        assert.equal(command, 'az');
        assert.ok(args.includes('RS256'));
        return '+/8=\n';
      },
      fetch: async (url, options) => {
        request = { url, options };
        return {
          ok: true,
          json: async () => ({ token: 'installation-token' }),
        };
      },
    });

    assert.equal(token, 'installation-token');
    assert.equal(request.url, 'https://api.github.com/app/installations/12345/access_tokens');
    assert.match(request.options.headers.Authorization, /^Bearer [^.]+\.[^.]+\.-_8$/);
    assert.deepEqual(JSON.parse(request.options.body), {
      repositories: ['semantic-kernel'],
      permissions: {
        contents: 'read',
        issues: 'write',
        pull_requests: 'write',
      },
    });
  });

  it('limits issue-label tokens to issue writes', async () => {
    let request;
    await createInstallationToken(
      { ...CONFIG, permissionProfile: 'issues' },
      {
        execute: () => '+/8=\n',
        fetch: async (_url, options) => {
          request = options;
          return {
            ok: true,
            json: async () => ({ token: 'installation-token' }),
          };
        },
      },
    );

    assert.deepEqual(JSON.parse(request.body).permissions, {
      issues: 'write',
    });
  });

  it('limits pull-request label tokens to contents and pull requests', async () => {
    let request;
    await createInstallationToken(
      { ...CONFIG, permissionProfile: 'pull-requests' },
      {
        execute: () => '+/8=\n',
        fetch: async (_url, options) => {
          request = options;
          return {
            ok: true,
            json: async () => ({ token: 'installation-token' }),
          };
        },
      },
    );

    assert.deepEqual(JSON.parse(request.body).permissions, {
      contents: 'read',
      pull_requests: 'write',
    });
  });

  it('rejects unknown permission profiles before signing', async () => {
    let signed = false;

    await assert.rejects(
      createInstallationToken(
        { ...CONFIG, permissionProfile: 'everything' },
        {
          execute: () => {
            signed = true;
            return '+/8=\n';
          },
        },
      ),
      /PERMISSION_PROFILE must be issues, pull-requests, or devflow/,
    );
    assert.equal(signed, false);
  });

  it('rejects inherited object properties as permission profiles before signing', async () => {
    let signed = false;

    await assert.rejects(
      createInstallationToken(
        { ...CONFIG, permissionProfile: 'toString' },
        {
          execute: () => {
            signed = true;
            return '+/8=\n';
          },
        },
      ),
      /PERMISSION_PROFILE must be issues, pull-requests, or devflow/,
    );
    assert.equal(signed, false);
  });

  it('rejects incomplete configuration', () => {
    assert.throws(
      () => readConfig({}),
      /Required GitHub App authentication configuration is missing/,
    );
  });

  it('rejects repository values with extra path segments before signing', async () => {
    let signed = false;

    await assert.rejects(
      createInstallationToken(
        { ...CONFIG, targetRepository: 'microsoft/semantic-kernel/extra' },
        {
          execute: () => {
            signed = true;
            return '+/8=\n';
          },
        },
      ),
      /TARGET_REPOSITORY must use the owner\/repository format/,
    );
    assert.equal(signed, false);
  });

  it('rejects an empty Key Vault signature', async () => {
    await assert.rejects(
      createInstallationToken(CONFIG, {
        execute: () => '\n',
      }),
      /Key Vault returned an empty signature/,
    );
  });

  it('rejects a failed GitHub token request', async () => {
    await assert.rejects(
      createInstallationToken(CONFIG, {
        execute: () => '+/8=\n',
        fetch: async () => ({ ok: false, status: 403 }),
      }),
      /GitHub installation token request failed with HTTP 403/,
    );
  });

  it('rejects an empty GitHub installation token', async () => {
    await assert.rejects(
      createInstallationToken(CONFIG, {
        execute: () => '+/8=\n',
        fetch: async () => ({
          ok: true,
          json: async () => ({ token: '' }),
        }),
      }),
      /GitHub returned an empty installation token/,
    );
  });
});
