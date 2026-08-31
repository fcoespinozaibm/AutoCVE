import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { getCurrentLanguage, setAppLanguage, type SupportedLanguage } from "@/shared/i18n";

const LANGUAGE_CYCLE: Record<SupportedLanguage, SupportedLanguage> = {
  zh: "en",
  en: "es",
  es: "zh",
};

const LANGUAGE_BADGES: Record<SupportedLanguage, string> = {
  zh: "中文",
  en: "EN",
  es: "ES",
};

interface LanguageSwitcherProps {
  collapsed?: boolean;
}

export default function LanguageSwitcher({ collapsed = false }: LanguageSwitcherProps) {
  const { t } = useTranslation();
  const currentLanguage = getCurrentLanguage();
  const nextLanguage = LANGUAGE_CYCLE[currentLanguage];

  async function handleToggleLanguage() {
    await setAppLanguage(nextLanguage);
  }

  return (
    <Button
      type="button"
      variant="ghost"
      aria-label={t("language.switchTo")}
      title={collapsed ? t("language.switchTo") : undefined}
      className={`w-full justify-start gap-3 rounded-[22px] border border-slate-200/80 bg-white/70 px-3 py-3 text-slate-600 transition hover:border-[hsl(var(--primary)/0.35)] hover:bg-white hover:text-slate-900 ${collapsed ? "h-11 justify-center px-0" : "h-auto"}`}
      onClick={handleToggleLanguage}
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-100/80 text-slate-500">
        <Languages className="h-4 w-4" />
      </span>
      {!collapsed && (
        <span className="flex min-w-0 flex-1 items-center justify-between gap-3">
          <span className="truncate text-sm font-semibold">{t("language.label")}</span>
          <span className="rounded-full border border-slate-200 bg-[#f8f9f8] px-2 py-0.5 text-xs font-semibold text-slate-500">
            {LANGUAGE_BADGES[currentLanguage]}
          </span>
        </span>
      )}
      {collapsed && (
        <span className="sr-only">{LANGUAGE_BADGES[nextLanguage]}</span>
      )}
    </Button>
  );
}
