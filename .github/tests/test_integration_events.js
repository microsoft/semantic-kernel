// Copyright (c) Microsoft. All rights reserved.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const YAML = require('yaml');

const workflows = [
  'python-integration-tests.yml',
  'dotnet-build-and-test.yml',
  'dotnet-integration-tests.yml',
].map((name) => ({
  name,
  workflow: YAML.parse(readFileSync(path.join(__dirname, '..', 'workflows', name), 'utf8')),
}));

async function evaluate(condition, context) {
  if (condition === undefined) return true;
  if (typeof condition === 'boolean') return condition;
  const { Lexer, Parser, Evaluator, data } = await import('@actions/expressions');
  const { truthy } = await import('@actions/expressions/result');
  const always = { name: 'always', minArgs: 0, maxArgs: 0, call: () => new data.BooleanData(true) };
  const convert = (value) => {
    if (typeof value === 'boolean') return new data.BooleanData(value);
    if (typeof value === 'string') return new data.StringData(value);
    return new data.Dictionary(
      ...Object.entries(value).map(([key, entry]) => ({ key, value: convert(entry) })),
    );
  };
  const expression = String(condition).replace(/^\s*\$\{\{|\}\}\s*$/g, '').trim();
  const tokens = new Lexer(expression).lex().tokens;
  const parsed = new Parser(tokens, Object.keys(context), [always]).parse();
  return truthy(new Evaluator(parsed, convert(context), new Map([['always', always]])).evaluate());
}

function contextFor(event, ref) {
  return {
    github: { event_name: event, ref },
    matrix: { 'integration-tests': true, os: 'ubuntu-latest' },
    steps: { filter: { outputs: { python: 'true', dotnet: 'true' } } },
    needs: {
      'paths-filter': { outputs: { pythonChanges: 'true', dotnetChanges: 'true' } },
    },
  };
}

function containsSecrets(value) {
  return JSON.stringify(value ?? {}).includes('secrets.');
}

describe('Integration workflow event selection', () => {
  for (const { name, workflow } of workflows) {
    for (const [event, ref] of [
      ['pull_request', 'refs/pull/42/merge'],
      ['merge_group', 'refs/heads/gh-readonly-queue/main/pr-42'],
      ['merge_group', 'refs/heads/main'],
      ['workflow_dispatch', 'refs/heads/topic'],
      ['repository_dispatch', 'refs/heads/main'],
    ]) {
      it(`${name} does not run integration setup or tests for ${event} on ${ref}`, async () => {
        const context = contextFor(event, ref);
        for (const [jobId, job] of Object.entries(workflow.jobs)) {
          if (!await evaluate(job.if, context)) continue;
          const prefix = `${name}: ${jobId}`;
          assert.equal(containsSecrets(workflow.env), false, `${prefix} inherits integration settings`);
          assert.notEqual(
            job.permissions?.['id-token'] ?? workflow.permissions?.['id-token'],
            'write',
            `${prefix} requests integration setup permissions`,
          );
          assert.equal(containsSecrets(job.env), false, `${prefix} has integration settings`);
          assert.notEqual(job.environment, 'integration', `${prefix} selects the integration environment`);
          for (const step of job.steps ?? []) {
            if (!await evaluate(step.if, context)) continue;
            assert.equal(containsSecrets(step), false, `${prefix}: ${step.name ?? step.uses}`);
            assert.doesNotMatch(
              step.uses ?? '',
              /^(azure\/login|google-github-actions\/auth|aws-actions\/configure-aws-credentials)@/,
              `${prefix}: ${step.name}`,
            );
          }
        }
      });
    }
  }

  it('keeps main-branch manual integration tests enabled', async () => {
    for (const { name, workflow } of workflows) {
      const context = contextFor('workflow_dispatch', 'refs/heads/main');
      let found = false;
      for (const [jobId, job] of Object.entries(workflow.jobs)) {
        if (jobId === 'python-merge-gate-ollama') continue;
        const tests = (job.steps ?? []).filter((step) => /Integration Tests/.test(step.name ?? ''));
        if (tests.length === 0) continue;
        assert.equal(await evaluate(job.if, context), true, `${name}: ${jobId} is disabled`);
        for (const step of tests) {
          assert.equal(await evaluate(step.if, context), true, `${name}: ${jobId}: ${step.name}`);
          assert.equal(containsSecrets(step.env), true, `${name}: ${jobId} has no integration settings`);
          found = true;
        }
      }
      assert.equal(found, true, `${name} has no manual integration tests`);
    }
  });

  it('keeps scheduled Python integration tests enabled on main', async () => {
    const { workflow } = workflows.find(({ name }) => name === 'python-integration-tests.yml');
    assert.equal(
      await evaluate(workflow.jobs['python-integration-tests'].if, contextFor('schedule', 'refs/heads/main')),
      true,
    );
  });

  it('keeps .NET build and unit tests enabled for pull requests and the merge queue', async () => {
    const { workflow } = workflows.find(({ name }) => name === 'dotnet-build-and-test.yml');
    const job = workflow.jobs['dotnet-build-and-test'];
    for (const event of ['pull_request', 'merge_group']) {
      const context = contextFor(event, 'refs/heads/gh-readonly-queue/main/pr-42');
      assert.equal(await evaluate(job.if, context), true);
      assert.equal(
        await evaluate(job.steps.find((step) => step.name === 'Run Unit Tests').if, context),
        true,
      );
    }
  });
});
