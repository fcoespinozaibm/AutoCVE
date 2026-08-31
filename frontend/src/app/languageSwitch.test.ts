import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const sourceRoot = resolve(import.meta.dirname, "..");

test("language switch runtime is enabled with zh/en/es support", () => {
  const mainSource = readFileSync(resolve(sourceRoot, "app/main.tsx"), "utf8");
  const appSource = readFileSync(resolve(sourceRoot, "app/App.tsx"), "utf8");
  const sidebarSource = readFileSync(resolve(sourceRoot, "components/layout/Sidebar.tsx"), "utf8");
  const loginSource = readFileSync(resolve(sourceRoot, "pages/Login.tsx"), "utf8");
  const registerSource = readFileSync(resolve(sourceRoot, "pages/Register.tsx"), "utf8");
  const i18nSource = readFileSync(resolve(sourceRoot, "shared/i18n/index.ts"), "utf8");
  const domSource = readFileSync(resolve(sourceRoot, "shared/i18n/useAutoTranslateDom.ts"), "utf8");

  assert.match(mainSource, /shared\/i18n/);
  assert.match(appSource, /useAutoTranslateDom/);
  assert.match(sidebarSource, /LanguageSwitcher/);
  assert.match(loginSource, /LanguageSwitcher/);
  assert.match(registerSource, /LanguageSwitcher/);
  assert.match(i18nSource, /"zh"\s*\|\s*"en"\s*\|\s*"es"/);
  assert.match(domSource, /startsWith\("en"\)/);
  assert.match(domSource, /startsWith\("es"\)/);
});

test("spanish catalog is registered with auto translations", () => {
  const resourcesSource = readFileSync(resolve(sourceRoot, "shared/i18n/resources.ts"), "utf8");

  assert.match(resourcesSource, /\bes:\s*\{\s*translation:\s*\{/);
  assert.match(resourcesSource, /const autoTextTranslations[\s\S]*?\{\s*en:\s*\{[\s\S]*?\bes:\s*\{/);
  assert.match(resourcesSource, /const autoAttributeTranslations[\s\S]*?\ben:\s*\{[\s\S]*?\bes:\s*\{/);
  assert.match(resourcesSource, /const autoTemplateTranslations[\s\S]*?\ben:\s*\[[\s\S]*?\bes:\s*\[/);
});
