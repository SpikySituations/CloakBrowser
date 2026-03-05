/**
 * Shared argument builder for Playwright and Puppeteer wrappers.
 */

import type { LaunchOptions } from "./types.js";
import { getDefaultStealthArgs } from "./config.js";

const DEBUG = /\bcloakbrowser\b/.test(process.env.DEBUG ?? "");

/**
 * Build deduplicated Chromium CLI args from stealth defaults + user overrides.
 *
 * Priority: stealth defaults < user args < dedicated params (timezone/locale).
 */
export function buildArgs(options: LaunchOptions): string[] {
  const seen = new Map<string, string>();

  if (options.stealthArgs !== false) {
    for (const arg of getDefaultStealthArgs()) {
      seen.set(arg.split("=")[0], arg);
    }
  }
  if (options.args) {
    for (const arg of options.args) {
      const key = arg.split("=")[0];
      if (seen.has(key)) {
        if (DEBUG) console.debug(`[cloakbrowser] Arg override: ${seen.get(key)} -> ${arg}`);
      }
      seen.set(key, arg);
    }
  }
  if (options.timezone) {
    const key = "--fingerprint-timezone";
    const flag = `${key}=${options.timezone}`;
    if (seen.has(key)) {
      if (DEBUG) console.debug(`[cloakbrowser] Arg override: ${seen.get(key)} -> ${flag}`);
    }
    seen.set(key, flag);
  }
  if (options.locale) {
    const key = "--lang";
    const flag = `${key}=${options.locale}`;
    if (seen.has(key)) {
      if (DEBUG) console.debug(`[cloakbrowser] Arg override: ${seen.get(key)} -> ${flag}`);
    }
    seen.set(key, flag);
  }
  return [...seen.values()];
}
