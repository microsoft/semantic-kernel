// Copyright (c) Microsoft. All rights reserved.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const workflowPath = join(__dirname, '..', 'workflows', 'label-pr.yml');
const workflow = readFileSync(workflowPath, 'utf8');

describe('Label pull request workflow', () => {
  it('uses the pull request token without the protected GitHub App environment', () => {
    assert.match(workflow, /^on: \[pull_request_target\]$/m);
    assert.doesNotMatch(workflow, /^\s+environment: github-app-auth$/m);
    assert.match(workflow, /^\s+pull-requests: write$/m);
    assert.doesNotMatch(workflow, /github-app-token/);
    assert.doesNotMatch(workflow, /\$\{\{\s*(?:vars|secrets)\./);
    assert.doesNotMatch(workflow, /GH_APP_|GH_ACTIONS_PR_WRITE/);
    assert.match(workflow, /repo-token: \$\{\{ github\.token \}\}/);
  });
});
