// Copyright (c) Microsoft. All rights reserved.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const checkTeamMembership = require('../scripts/check_team_membership.js');

const context = { repo: { owner: 'microsoft', repo: 'semantic-kernel' } };

function githubWithMembership(membership, username = 'contributor') {
  return {
    rest: {
      pulls: {
        get: async (params) => {
          assert.deepEqual(params, { ...context.repo, pull_number: 42 });
          return { data: { user: { login: 'contributor' } } };
        },
      },
      teams: {
        getByName: async (params) => {
          assert.deepEqual(params, { org: 'microsoft', team_slug: 'developers' });
        },
        getMembershipForUserInOrg: async (params) => {
          assert.deepEqual(params, {
            org: 'microsoft',
            team_slug: 'developers',
            username,
          });
          if (membership instanceof Error) throw membership;
          return { data: { state: membership } };
        },
      },
    },
  };
}

describe('Review requester team membership', () => {
  const options = { context, teamSlug: 'developers', prNumber: '42' };

  it('uses the PR author from the event on automatic runs', async () => {
    const github = githubWithMembership('active');
    github.rest.pulls.get = async () => {
      throw new Error('Should not look up the PR when the event includes its author');
    };
    assert.deepEqual(
      await checkTeamMembership({
        ...options,
        context: { ...context, payload: { pull_request: { user: { login: 'contributor' } } } },
        github,
      }),
      { author: 'contributor', isTeamMember: true },
    );
  });

  it('uses the initiator on manual runs, even if the PR author is external', async () => {
    const github = githubWithMembership('active', 'maintainer');
    github.rest.pulls.get = async () => {
      throw new Error('Should not look up the PR author on manual runs');
    };
    assert.deepEqual(
      await checkTeamMembership({ ...options, github, username: 'maintainer' }),
      { author: 'maintainer', isTeamMember: true },
    );
    assert.deepEqual(
      await checkTeamMembership({
        ...options,
        github: githubWithMembership(Object.assign(new Error('Not Found'), { status: 404 }), 'outsider'),
        username: 'outsider',
      }),
      { author: 'outsider', isTeamMember: false },
    );
  });

  it('accepts an active team member', async () => {
    assert.deepEqual(
      await checkTeamMembership({ ...options, github: githubWithMembership('active') }),
      { author: 'contributor', isTeamMember: true },
    );
  });

  it('rejects a pending team member and an outsider', async () => {
    for (const membership of ['pending', Object.assign(new Error('Not Found'), { status: 404 })]) {
      assert.deepEqual(
        await checkTeamMembership({ ...options, github: githubWithMembership(membership) }),
        { author: 'contributor', isTeamMember: false },
      );
    }
  });

  it('does not treat API errors or a missing team as nonmembership', async () => {
    await assert.rejects(
      checkTeamMembership({
        ...options,
        github: githubWithMembership(Object.assign(new Error('Forbidden'), { status: 403 })),
      }),
      /Forbidden/,
    );
    const github = githubWithMembership('active');
    github.rest.teams.getByName = async () => {
      throw Object.assign(new Error('Team not found'), { status: 404 });
    };
    await assert.rejects(checkTeamMembership({ ...options, github }), /Team not found/);
  });

  it('rejects missing configuration and invalid PR numbers', async () => {
    await assert.rejects(
      checkTeamMembership({ ...options, github: githubWithMembership('active'), teamSlug: '' }),
      /DEVELOPER_TEAM/,
    );
    for (const prNumber of ['0', '1e2', '9007199254740992']) {
      await assert.rejects(
        checkTeamMembership({ ...options, github: githubWithMembership('active'), prNumber }),
        /valid PR number/,
      );
    }
  });
});
