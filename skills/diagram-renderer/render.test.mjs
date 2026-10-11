import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';

const render = source => spawnSync(process.execPath, [fileURLToPath(new URL('./render.mjs', import.meta.url))], {
  input: source, encoding: 'utf8', timeout: 30_000,
});

test('sequence, state, and flow render labeled SVG without remote font imports', () => {
  for (const source of [
    'sequenceDiagram\n A->>B: Request\n B-->>A: Result',
    'stateDiagram-v2\n Waiting --> Streaming: Request\n Streaming --> Done: Result',
    'flowchart TB\n A[Request] --> B[Result]',
  ]) {
    const result = render(source);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /<svg\b/);
    assert.match(result.stdout, />Request</);
    assert.match(result.stdout, />Result</);
    assert.doesNotMatch(result.stdout, /@import/);
    assert.doesNotMatch(result.stdout, /^[ \t]+$/m);
  }
});

test('rejects termination arrows without rejecting ordinary label text', () => {
  for (const arrow of ['-x', '--x']) {
    const result = render(`sequenceDiagram\n A${arrow}B: Terminated`);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /Termination crosses are unsupported/);
    assert.equal(result.stdout, '');
  }
  assert.equal(render('sequenceDiagram\n A->>B: non-x label').status, 0);
});
