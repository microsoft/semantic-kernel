// Copyright (c) Microsoft. All rights reserved.

async function checkTeamMembership({ github, context, teamSlug, prNumber, username = '' }) {
  if (!teamSlug) {
    throw new Error('DEVELOPER_TEAM must be configured with the developer team slug.');
  }

  const number = Number(prNumber);
  if (!/^[1-9][0-9]*$/.test(prNumber) || !Number.isSafeInteger(number)) {
    throw new Error('A valid PR number is required to check team membership.');
  }

  let author = username.trim() || context.payload?.pull_request?.user?.login;
  if (!author) {
    const { data: pr } = await github.rest.pulls.get({
      ...context.repo,
      pull_number: number,
    });
    author = pr.user?.login;
  }
  if (!author) {
    throw new Error('Could not determine PR author (user may be deleted).');
  }

  // Verify the team exists so a missing or inaccessible team is not mistaken for a nonmember.
  await github.rest.teams.getByName({
    org: context.repo.owner,
    team_slug: teamSlug,
  });

  try {
    const { data: membership } = await github.rest.teams.getMembershipForUserInOrg({
      org: context.repo.owner,
      team_slug: teamSlug,
      username: author,
    });
    return { author, isTeamMember: membership.state === 'active' };
  } catch (error) {
    if (error.status === 404) {
      return { author, isTeamMember: false };
    }
    throw error;
  }
}

module.exports = checkTeamMembership;
