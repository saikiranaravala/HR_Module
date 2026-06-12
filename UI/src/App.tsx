import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { CommandPalette, Crumbs, GlobalHeader, NavBar, Toasts } from "./components";
import Home from "./pages/Home";
import Approvals from "./pages/Approvals";
import Team from "./pages/Team";
import Payslips from "./pages/Payslips";
import TimeAbsence from "./pages/TimeAbsence";
import Benefits from "./pages/Benefits";
import Profile from "./pages/Profile";
import Directory from "./pages/Directory";
import Performance from "./pages/Performance";
import Learning from "./pages/Learning";
import Help from "./pages/Help";
import CompCycle from "./pages/CompCycle";
import Recruiting from "./pages/Recruiting";
import PayrollHub from "./pages/PayrollHub";
import Succession from "./pages/Succession";
import Analytics from "./pages/Analytics";

export default function App() {
  const [navOpen, setNavOpen] = useState(true);
  const [palette, setPalette] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((v) => !v);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  return (
    <div className="shell">
      <a className="skipnav" href="#main">Skip to content</a>
      <GlobalHeader onToggleNav={() => setNavOpen((v) => !v)} onOpenPalette={() => setPalette(true)} />
      <Crumbs />
      <div className="shell-body">
        <NavBar open={navOpen} />
        <main className="main" id="main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/team" element={<Team />} />
            <Route path="/pay" element={<Payslips />} />
            <Route path="/time" element={<TimeAbsence />} />
            <Route path="/benefits" element={<Benefits />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/directory" element={<Directory />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/learning" element={<Learning />} />
            <Route path="/help" element={<Help />} />
            <Route path="/comp-cycle" element={<CompCycle />} />
            <Route path="/recruiting" element={<Recruiting />} />
            <Route path="/payroll-hub" element={<PayrollHub />} />
            <Route path="/succession" element={<Succession />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
      <CommandPalette open={palette} onClose={() => setPalette(false)} />
      <Toasts />
    </div>
  );
}
