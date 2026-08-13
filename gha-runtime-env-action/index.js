const fs = require('fs');

const names = [
  'ACTIONS_RUNTIME_TOKEN',
  'ACTIONS_CACHE_URL',
  'ACTIONS_RESULTS_URL',
  'ACTIONS_CACHE_SERVICE_V2',
];

for (const name of names) {
  const value = process.env[name] || '';
  if (!value) continue;
  if (name.endsWith('_TOKEN')) process.stdout.write(`::add-mask::${value}\n`);
  fs.appendFileSync(process.env.GITHUB_ENV, `${name}<<__RUNTIME_${name}__\n${value}\n__RUNTIME_${name}__\n`);
}
