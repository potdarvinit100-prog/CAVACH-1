// CAVACH app shell — routing only. Screens live in pages.tsx, shared UI
// in components.tsx, the engine in engine.ts, persistence in store.ts.
import { useEffect, useState } from "react";
import { Routes, Route, Link, NavLink } from "react-router-dom";
import { Logo } from "./components";
import { loadInvestigations, type SavedInvestigation } from "./store";
import { Landing, Dashboard, Investigate, Detail, RagPage, IncidentPage, SettingsPage, EvaluationPage, PrePayPage, PrivacyPage } from "./pages";
import type { Lang } from "./i18n";
import { t } from "./i18n";

export default function App() {
  const [lang, setLang] = useState<Lang>(() => (localStorage.getItem("cavach.lang") as Lang) || "en");
  const [large, setLarge] = useState(() => localStorage.getItem("cavach.large") === "1");
  const [list, setList] = useState<SavedInvestigation[]>([]);
  const refresh = () => loadInvestigations().then(setList);
  useEffect(() => { refresh(); }, []);
  useEffect(() => { localStorage.setItem("cavach.lang", lang); }, [lang]);
  useEffect(() => { localStorage.setItem("cavach.large", large ? "1" : "0"); }, [large]);
  return (
    <div className="app-shell" style={{ fontSize: large ? 19 : 16 }}>
      <header className="topbar">
        <Link to="/" style={{ textDecoration: "none" }}><Logo /></Link>
        <nav className="main-nav">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "dashboard")}</NavLink>
          <NavLink to="/investigate" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "investigate")}</NavLink>
          <NavLink to="/rag" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "rag")}</NavLink>
          <NavLink to="/incident" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "incident")}</NavLink>
          <NavLink to="/prepay" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "prepay")}</NavLink>
          <NavLink to="/evaluation" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "evaluation")}</NavLink>
          <NavLink to="/settings" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "settings")}</NavLink>
          <NavLink to="/privacy" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>{t(lang, "privacy")}</NavLink>
        </nav>
        <span className="mode-pill">Device only · No sign-in</span>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<Landing lang={lang} />} />
          <Route path="/dashboard" element={<Dashboard list={list} lang={lang} />} />
          <Route path="/investigate" element={<Investigate lang={lang} onSaved={refresh} />} />
          <Route path="/investigate/:id" element={<Detail lang={lang} />} />
          <Route path="/rag" element={<RagPage lang={lang} />} />
          <Route path="/incident" element={<IncidentPage lang={lang} />} />
          <Route path="/prepay" element={<PrePayPage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
          <Route path="/settings" element={<SettingsPage lang={lang} setLang={setLang} large={large} setLarge={setLarge} />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="*" element={<Landing lang={lang} />} />
        </Routes>
        <footer className="site-footer">
          CAVACH — One Shield. Every Threat. · A clean result never means safe. A flag never means a person is a criminal. · For financial fraud: call 1930, report at cybercrime.gov.in. · Not endorsed by Maharashtra Cyber or Maharashtra Police.
        </footer>
      </main>
    </div>
  );
}
