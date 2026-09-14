# Contributing

Thanks for the interest — but this repository doesn't accept outside contributions.

Knak Labs repos are a **public showcase of Knak engineering**, published so people can read,
clone and learn from the code. They are maintained solely by Knak employees, and we don't accept
external pull requests.

You are welcome to:

- **Read and clone** the code — it's MIT licensed, so you can use it in your own work
- **Fork it** and take it in your own direction

If you've found a bug or have an idea, the most useful thing you can do is get in touch through
[knak.com](https://knak.com) rather than opening a pull request here, since we can't merge it.

## For Knak employees

Branch, commit, and open a pull request — direct pushes to `main` are blocked and a merge needs
one approving review from someone other than the author.

Every commit on every branch must satisfy the org rulesets:

- Author **and** committer email must end in `@knak.com`
- Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`, optional `(scope)`, optional
  `!`, then `: ` and a description

```
git config user.email "you@knak.com"
git switch -c docs/short-description
git commit -m "docs: short description"
git push -u origin docs/short-description
gh pr create
```

Squash and merge-commit are disabled, so every commit you push is replayed onto `main` as-is —
tidy up work-in-progress commits with `git rebase -i` before pushing. If a push is rejected on
the committer-email rule, check that **"Keep my email addresses private"** is unchecked in your
GitHub email settings; GitHub otherwise substitutes a `noreply` address.

See the Knak Labs page in the Engineering Wiki for the full policy.
