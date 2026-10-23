// Copyright (c) Microsoft. All rights reserved.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync, mkdtempSync, writeFileSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const workflow = readFileSync(
  path.join(__dirname, '../workflows/python-test-coverage-report.yml'),
  'utf8',
);
const selectionStep = workflow.split('      - name: Read and set PR number\n')[1].split('      - name:')[0];
const context = {
  repo: { owner: 'microsoft', repo: 'semantic-kernel' },
  payload: {
    repository: { id: 1 },
    workflow_run: {
      event: 'pull_request',
      head_sha: 'abc123',
      head_branch: 'topic',
      head_repository: { id: 2 },
      pull_requests: [{ number: 42 }],
    },
  },
};
const pullRequest = {
  number: 42,
  state: 'open',
  base: { repo: { id: 1 } },
  head: { sha: 'abc123', ref: 'topic', repo: { id: 2 } },
};

async function selectPullRequest({ eventContext = context, github = {}, artifactNumber = '99' } = {}) {
  const script = selectionStep.match(/          script: \|\n((?:            .*\n|\n)+)/);
  if (script) {
    const outputs = {};
    const warnings = [];
    const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
    await new AsyncFunction('context', 'github', 'core', script[1].replace(/^            /gm, ''))(
      eventContext,
      github,
      {
        setOutput: (name, value) => { outputs[name] = value; },
        warning: (message) => { warnings.push(message); },
        setFailed: (message) => { throw new Error(message); },
      },
    );
    return { number: outputs.pr_number, warnings };
  }

  const run = selectionStep.match(/        run: \|\n((?:          .*\n|\n)+)/);
  assert.ok(run, 'Expected an executable PR-selection step');
  const directory = mkdtempSync(path.join(tmpdir(), 'coverage-report-'));
  try {
    writeFileSync(path.join(directory, 'pr_number'), artifactNumber);
    const result = spawnSync(
      process.platform === 'win32' ? 'C:\\Program Files\\Git\\bin\\bash.exe' : 'bash',
      ['-e', '-c', run[1].replace(/^          /gm, '')],
      { cwd: directory, env: { ...process.env, GITHUB_ENV: 'github-env' }, encoding: 'utf8' },
    );
    assert.ifError(result.error);
    assert.equal(result.status, 0, result.stderr);
    const number = readFileSync(path.join(directory, 'github-env'), 'utf8').match(/^PR_NUMBER=(.+)$/m);
    return { number: number && Number(number[1]), warnings: [] };
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

function githubForPullRequest(pr = pullRequest) {
  return {
    rest: {
      pulls: {
        get: async (params) => {
          assert.deepEqual(params, { ...context.repo, pull_number: 42 });
          return { data: pr };
        },
      },
    },
  };
}

function contextWithRun(changes) {
  return {
    ...context,
    payload: {
      ...context.payload,
      workflow_run: { ...context.payload.workflow_run, ...changes },
    },
  };
}

function githubWithAssociatedPullRequests(prs) {
  const github = githubForPullRequest();
  github.rest.repos = { listPullRequestsAssociatedWithCommit: Symbol('associated pull requests') };
  github.paginate = async (method, params) => {
    assert.equal(method, github.rest.repos.listPullRequestsAssociatedWithCommit);
    assert.deepEqual(params, { ...context.repo, commit_sha: 'abc123', per_page: 100 });
    return prs;
  };
  return github;
}

describe('Coverage report PR selection', () => {
  it('selects the triggering run PR independently of the downloaded PR number', async () => {
    const result = await selectPullRequest({ github: githubForPullRequest() });
    assert.equal(result.number, 42);
  });

  it('finds the matching fork PR when the run has no PR association', async () => {
    const result = await selectPullRequest({
      eventContext: contextWithRun({ pull_requests: [] }),
      github: githubWithAssociatedPullRequests([
        { ...pullRequest, number: 43, head: { ...pullRequest.head, repo: { id: 3 } } },
        pullRequest,
      ]),
    });
    assert.equal(result.number, 42);
  });

  it('skips runs without a unique matching PR and explains why', async () => {
    for (const prs of [[], [pullRequest, { ...pullRequest, number: 43 }]]) {
      const result = await selectPullRequest({
        eventContext: contextWithRun({ pull_requests: [] }),
        github: githubWithAssociatedPullRequests(prs),
      });
      assert.equal(result.number, undefined);
      assert.match(result.warnings[0], /exactly one matching pull request/);
    }
    const result = await selectPullRequest({
      eventContext: contextWithRun({ pull_requests: [{ number: 42 }, { number: 43 }] }),
    });
    assert.equal(result.number, undefined);
    assert.match(result.warnings[0], /exactly one matching pull request/);
  });

  it('skips closed PRs and PRs whose commit, branch, or repository no longer matches', async () => {
    for (const pr of [
      { ...pullRequest, state: 'closed' },
      { ...pullRequest, base: { repo: { id: 3 } } },
      { ...pullRequest, head: { ...pullRequest.head, sha: 'def456' } },
      { ...pullRequest, head: { ...pullRequest.head, ref: 'other' } },
      { ...pullRequest, head: { ...pullRequest.head, repo: { id: 3 } } },
      { ...pullRequest, head: { ...pullRequest.head, repo: null } },
    ]) {
      const result = await selectPullRequest({ github: githubForPullRequest(pr) });
      assert.equal(result.number, undefined);
      assert.match(result.warnings[0], /no longer matches/);
    }
  });

  it('does not report on runs for other events', async () => {
    const result = await selectPullRequest({ eventContext: contextWithRun({ event: 'push' }) });
    assert.equal(result.number, undefined);
    assert.match(result.warnings[0], /pull request workflow run/);
  });

  it('skips runs whose source repository is no longer available', async () => {
    const result = await selectPullRequest({
      eventContext: contextWithRun({ head_repository: null }),
      github: githubForPullRequest({ ...pullRequest, head: { ...pullRequest.head, repo: null } }),
    });
    assert.equal(result.number, undefined);
    assert.match(result.warnings[0], /no longer matches/);
  });

  it('propagates API failures instead of selecting a different PR', async () => {
    const github = githubForPullRequest();
    github.rest.pulls.get = async () => { throw new Error('API unavailable'); };
    await assert.rejects(selectPullRequest({ github }), /API unavailable/);
  });

  it('uses the selected PR output for commenting and resolves it before downloading reports', () => {
    const commentStep = workflow.split('      - name: Pytest coverage comment\n')[1];
    const downloadStep = workflow.split('      - name: Download coverage report\n')[1].split('      - name:')[0];
    assert.match(commentStep, /issue-number: \$\{\{ steps\.pr\.outputs\.pr_number \}\}/);
    for (const step of [commentStep, downloadStep]) {
      assert.match(step, /if: steps\.pr\.outputs\.pr_number != ''/);
    }
    assert.ok(
      workflow.indexOf('      - name: Read and set PR number\n') <
      workflow.indexOf('      - name: Download coverage report\n'),
    );
  });
});
