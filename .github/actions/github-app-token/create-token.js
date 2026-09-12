// Copyright (c) Microsoft. All rights reserved.

const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');

const PERMISSION_PROFILES = Object.freeze({
  issues: Object.freeze({
    issues: 'write',
  }),
  'pull-requests': Object.freeze({
    contents: 'read',
    pull_requests: 'write',
  }),
  devflow: Object.freeze({
    contents: 'read',
    issues: 'write',
    pull_requests: 'write',
  }),
});

function base64Url(value) {
  return Buffer.from(value).toString('base64url');
}

function base64ToBase64Url(value) {
  return Buffer.from(value, 'base64').toString('base64url');
}

function createJwtSigningInput(clientId, nowSeconds) {
  const header = base64Url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const payload = base64Url(JSON.stringify({
    iat: nowSeconds - 60,
    exp: nowSeconds + 540,
    iss: clientId,
  }));
  return `${header}.${payload}`;
}

function signJwt(signingInput, config, execute = execFileSync) {
  const digest = crypto.createHash('sha256').update(signingInput).digest('base64');
  const signature = execute(
    'az',
    [
      'keyvault', 'key', 'sign',
      '--subscription', config.azureSubscriptionId,
      '--vault-name', config.keyVaultName,
      '--name', config.keyName,
      '--algorithm', 'RS256',
      '--digest', digest,
      '--query', 'signature',
      '--output', 'tsv',
      '--only-show-errors',
    ],
    { encoding: 'utf8' },
  ).trim();

  if (!signature) {
    throw new Error('Key Vault returned an empty signature.');
  }

  return `${signingInput}.${base64ToBase64Url(signature)}`;
}

async function createInstallationToken(config, dependencies = {}) {
  const execute = dependencies.execute ?? execFileSync;
  const request = dependencies.fetch ?? fetch;
  const nowSeconds = dependencies.nowSeconds ?? Math.floor(Date.now() / 1000);
  const repositoryParts = config.targetRepository.split('/');

  if (repositoryParts.length !== 2 || repositoryParts.some((part) => part.length === 0)) {
    throw new Error('TARGET_REPOSITORY must use the owner/repository format.');
  }
  if (!Object.hasOwn(PERMISSION_PROFILES, config.permissionProfile)) {
    throw new Error('PERMISSION_PROFILE must be issues, pull-requests, or devflow.');
  }
  const permissions = PERMISSION_PROFILES[config.permissionProfile];

  const [, repository] = repositoryParts;
  const signingInput = createJwtSigningInput(config.githubAppClientId, nowSeconds);
  const jwt = signJwt(signingInput, config, execute);

  const response = await request(
    `https://api.github.com/app/installations/${config.githubAppInstallationId}/access_tokens`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${jwt}`,
        'X-GitHub-Api-Version': '2022-11-28',
      },
      body: JSON.stringify({
        repositories: [repository],
        permissions,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(`GitHub installation token request failed with HTTP ${response.status}.`);
  }

  const result = await response.json();
  if (typeof result.token !== 'string' || result.token.length === 0) {
    throw new Error('GitHub returned an empty installation token.');
  }

  return result.token;
}

function readConfig(environment) {
  const config = {
    azureSubscriptionId: environment.AZURE_SUBSCRIPTION_ID,
    keyVaultName: environment.KEY_VAULT_NAME,
    keyName: environment.KEY_NAME,
    githubAppClientId: environment.GITHUB_APP_CLIENT_ID,
    githubAppInstallationId: environment.GITHUB_APP_INSTALLATION_ID,
    targetRepository: environment.TARGET_REPOSITORY,
    permissionProfile: environment.PERMISSION_PROFILE,
  };

  if (Object.values(config).some((value) => !value)) {
    throw new Error('Required GitHub App authentication configuration is missing.');
  }

  return config;
}

async function main() {
  try {
    const token = await createInstallationToken(readConfig(process.env));
    process.stdout.write(token);
  } catch {
    console.error('GitHub App token generation failed.');
    process.exitCode = 1;
  }
}

if (require.main === module) {
  void main();
}

module.exports = {
  base64ToBase64Url,
  createInstallationToken,
  createJwtSigningInput,
  readConfig,
  signJwt,
  PERMISSION_PROFILES,
};
