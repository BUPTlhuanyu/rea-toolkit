#!/usr/bin/env node
/**
 * Batch-call rea MCP tools against one binary.
 *
 * 用法：
 *   node rea_batch.mjs --target /path/to/binary --out out.jsonl \
 *     --procedures 0x1000,0x2000,procedure_callers@0x3000
 *
 * 可选：
 *   --rea rea                 rea 命令（默认 env REA_BIN 或 "rea"）
 *   --provider ghidra         open_binary provider
 *   --ghidra /path/to/ghidra  env GHIDRA_INSTALL_DIR
 *   --java-home /path/to/jdk  env JAVA_HOME
 *   --timeout 3600000         单次 MCP 调用超时（毫秒）
 *   --procedures-file file    每行一个 procedure（与 --procedures 二选一）
 *
 * 输出：每行一个 JSON，包含 step/procedure/tool/result 或 error。
 */

import { spawn } from 'node:child_process';
import { appendFileSync, readFileSync } from 'node:fs';

function parseArgs(argv) {
  const out = { provider: 'ghidra', timeout: 3600000 };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) continue;
    const key = arg.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const value = argv[i + 1];
    if (value === undefined || value.startsWith('--')) {
      out[key] = true;
    } else {
      out[key] = value;
      i += 1;
    }
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const target = args.target || process.env.REA_TARGET;
const output = args.out;
let procedures = [];
if (args.procedures) {
  procedures = String(args.procedures).split(',').map((item) => item.trim()).filter(Boolean);
} else if (args.proceduresFile) {
  procedures = readFileSync(args.proceduresFile, 'utf8')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}

if (!target || !output || procedures.length === 0) {
  console.error(
    'usage: node rea_batch.mjs --target <binary> --out <jsonl> ' +
      '--procedures <a,b,...> | --procedures-file <file>',
  );
  process.exit(2);
}

const rea = args.rea || process.env.REA_BIN || 'rea';
const ghidra = args.ghidra || process.env.GHIDRA_INSTALL_DIR;
const javaHome = args.javaHome || process.env.JAVA_HOME;
const timeout = Number(args.timeout || 3600000);

const env = { ...process.env };
if (ghidra) env.GHIDRA_INSTALL_DIR = ghidra;
if (javaHome) {
  env.JAVA_HOME = javaHome;
  env.PATH = `${javaHome}/bin:${process.env.PATH ?? ''}`;
}
env.REA_GHIDRA_STARTUP_TIMEOUT_MS = String(timeout);

const server = spawn(rea, ['--mcp'], {
  stdio: ['pipe', 'pipe', 'inherit'],
  env,
});

const pending = new Map();
let buffer = '';
let nextId = 0;

server.stdout.on('data', (chunk) => {
  buffer += chunk;
  let newline;
  while ((newline = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, newline);
    buffer = buffer.slice(newline + 1);
    if (!line.trim()) continue;
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      continue;
    }
    if (message.id != null && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  }
});

function call(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`Timed out: ${method}`));
    }, timeout);
    pending.set(id, (message) => {
      clearTimeout(timer);
      resolve(message);
    });
    server.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`);
  });
}

function text(message) {
  return (
    message?.result?.content?.map((part) => part.text || '').join('\n') ??
    JSON.stringify(message)
  );
}

try {
  await call('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'rea-batch', version: '1' },
  });
  server.stdin.write(
    `${JSON.stringify({
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    })}\n`,
  );

  const opened = await call('tools/call', {
    name: 'open_binary',
    arguments: { path: target, provider_id: args.provider },
  });
  appendFileSync(output, `${JSON.stringify({ step: 'open_binary', result: text(opened) })}\n`);

  for (const item of procedures) {
    const [tool, procedure] = item.includes('@')
      ? item.split('@')
      : ['procedure_pseudo_code', item];
    const result = await call('tools/call', {
      name: tool,
      arguments: { procedure },
    });
    appendFileSync(output, `${JSON.stringify({ procedure, tool, result: text(result) })}\n`);
    console.log(`done ${item}`);
  }

  const closed = await call('tools/call', { name: 'close_binary', arguments: {} });
  appendFileSync(output, `${JSON.stringify({ step: 'close_binary', result: text(closed) })}\n`);
} catch (error) {
  appendFileSync(output, `${JSON.stringify({ step: 'driver_error', error: String(error) })}\n`);
  process.exitCode = 1;
} finally {
  server.kill('SIGTERM');
}
