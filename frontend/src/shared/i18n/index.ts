import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { resources } from "./resources";

export type SupportedLanguage = "zh" | "en" | "es";

export const LANGUAGE_STORAGE_KEY = "autocve.language";

function isSupportedLanguage(value: string | null): value is SupportedLanguage {
  return value === "zh" || value === "en" || value === "es";
}

function getInitialLanguage(): SupportedLanguage {
  if (typeof window === "undefined") {
    return "zh";
  }

  const storedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (isSupportedLanguage(storedLanguage)) {
    return storedLanguage;
  }

  const browserLanguage = window.navigator.language?.toLowerCase() ?? "";
  if (browserLanguage.startsWith("en")) {
    return "en";
  }
  if (browserLanguage.startsWith("es")) {
    return "es";
  }
  return "zh";
}

void i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  fallbackLng: "zh",
  supportedLngs: ["zh", "en", "es"],
  interpolation: {
    escapeValue: false,
  },
});

export function getCurrentLanguage(): SupportedLanguage {
  if (i18n.language === "en") {
    return "en";
  }
  if (i18n.language === "es") {
    return "es";
  }
  return "zh";
}

export async function setAppLanguage(language: SupportedLanguage) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }

  await i18n.changeLanguage(language);
}

export default i18n;
