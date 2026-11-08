#!/usr/bin/env node
/**
 * Install rea-toolkit skills/profiles into a Comate workspace.
 *
 * 用法：
 *   npx . install --project /path/to/project       # 项目级，默认 copy
 *   npx . install --global                         # 全局（~/.comate）
 *   npx . install --project . --link               # 开发时用软链
 *   npx . doctor --project /path/to/project
 *
 * 说明：
 *   - npx 本身只负责下载/执行包，不会自动把 skill 注册到全局。
 *     “全局”是本脚本的 --global 决定的：复制到 ~/.comate/skills/。
 *   - 默认 copy，避免 npx 缓存目录被清理后留下坏软链。
 *   - 已存在的目标默认跳过；--force 覆盖。
 */

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const SKILLS = [
  'reconstruction-bootstrap',
  'reconstruction-core',
  'reconstruction-scaffold',
];
const PROFILES = path.join('skills', 'reconstruction-bootstrap', 'profiles');

function usage() {
  console.log(`rea-toolkit

用法：
  rea-toolkit install [--project <dir>] [--global] [--link] [--force]
  rea-toolkit doctor  [--project <dir>] [--global]
  rea-toolkit list

选项：
  --project <dir>  安装到 <dir>/.comate（默认当前目录）
  --global         安装到 ~/.comate
  --link           用软链代替复制（开发时用；npx 缓存场景不建议）
  --force          覆盖已存在的 skill/profile
  --help           显示帮助

示例：
  npx . install --project ~/my-project
  npx . install --global
  npx /path/to/rea-toolkit install --project ~/my-project
`);
}

function parseArgs(argv) {
  const args = { command: argv[0] || '--help', project: process.cwd(), global: false, link: false, force: false };
  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') args.command = '--help';
    else if (arg === '--global') args.global = true;
    else if (arg === '--project') { args.project = path.resolve(argv[++i]); args.global = false; }
    else if (arg === '--link') args.link = true;
    else if (arg === '--force') args.force = true;
    else if (arg.startsWith('--project=')) { args.project = path.resolve(arg.slice(10)); args.global = false; }
    else throw new Error(`未知参数: ${arg}`);
  }
  return args;
}

function comateDir(args) {
  return args.global ? path.join(os.homedir(), '.comate') : path.join(args.project, '.comate');
}

function exists(pathname) {
  try { return fs.lstatSync(pathname); } catch { return null; }
}

function copyDir(src, dest) {
  fs.cpSync(src, dest, { recursive: true, force: true, dereference: true });
}

function installEntry(src, dest, { link, force }) {
  if (!exists(src)) throw new Error(`源不存在: ${src}`);
  const current = exists(dest);
  if (current) {
    if (!force) {
      console.log(`SKIP   ${dest} (已存在，--force 覆盖)`);
      return false;
    }
    fs.rmSync(dest, { recursive: true, force: true });
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  if (link) {
    fs.symlinkSync(src, dest, 'dir');
    console.log(`LINK   ${dest} -> ${src}`);
  } else {
    copyDir(src, dest);
    console.log(`COPY   ${dest}`);
  }
  return true;
}

function install(args) {
  const base = comateDir(args);
  console.log(`ROOT   ${ROOT}`);
  console.log(`TARGET ${base}`);
  const results = [];
  for (const skill of SKILLS) {
    results.push(installEntry(path.join(ROOT, 'skills', skill), path.join(base, 'skills', skill), args));
  }
  results.push(installEntry(path.join(ROOT, PROFILES), path.join(base, 'profiles'), args));
  results.push(installEntry(path.join(ROOT, 'toolkits'), path.join(base, 'toolkits'), args));
  const changed = results.filter(Boolean).length;
  console.log(`\n完成：${changed} 项写入，${results.length - changed} 项跳过`);
  console.log('如果 Comate 当前会话没有立即看到新 skill，重载/重开会话即可。');
  return 0;
}

function doctor(args) {
  const base = comateDir(args);
  console.log(`TARGET ${base}`);
  let failed = 0;
  for (const skill of SKILLS) {
    const skillMd = path.join(base, 'skills', skill, 'SKILL.md');
    if (exists(skillMd)) console.log(`OK     ${skillMd}`);
    else { console.log(`MISS   ${skillMd}`); failed += 1; }
  }
  const profile = path.join(base, 'profiles', 'wps-chart.json');
  if (exists(profile)) console.log(`OK     ${profile}`);
  else { console.log(`MISS   ${profile}`); failed += 1; }
  const focus = path.join(base, 'toolkits', 'metrics', 'focus.py');
  if (exists(focus)) console.log(`OK     ${focus}`);
  else { console.log(`MISS   ${focus}`); failed += 1; }
  console.log(failed ? `\n${failed} 项缺失` : '\n全部就绪');
  return failed ? 1 : 0;
}

function list() {
  console.log(`ROOT ${ROOT}`);
  for (const skill of SKILLS) console.log(`SKILL ${path.join('skills', skill)}`);
  console.log(`PROFILES ${PROFILES}`);
  console.log('TOOLKITS toolkits');
  return 0;
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(String(error.message || error));
    usage();
    return 2;
  }
  if (args.command === '--help' || args.command === 'help') { usage(); return 0; }
  if (args.command === 'install') return install(args);
  if (args.command === 'doctor') return doctor(args);
  if (args.command === 'list') return list();
  console.error(`未知命令: ${args.command}`);
  usage();
  return 2;
}

process.exitCode = main();
