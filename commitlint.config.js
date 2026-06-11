export default {
	extends: ['@commitlint/config-conventional'],
	rules: {
		// Permit longer subjects than the default 72 — Svelte component names eat chars fast.
		'subject-max-length': [2, 'always', 100],
		'body-max-line-length': [1, 'always', 120],
		'type-enum': [
			2,
			'always',
			['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert']
		]
	}
};
