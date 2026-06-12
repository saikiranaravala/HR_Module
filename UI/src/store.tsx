/* App store: persona, interactive state (approvals, PTO, worksheet, pipeline),
   and toasts. Reducer-shaped so swapping in the REST client later is a
   dispatch-for-fetch substitution, not a rewrite. */
import { createContext, useContext, useMemo, useReducer, type ReactNode } from "react";
import {
  APPROVALS, CANDIDATES, WORKSHEET,
  type Approval, type Candidate, type Persona, type WorksheetLine,
} from "./data";

interface Toast { id: number; text: string; warn?: boolean }
interface State {
  persona: Persona;
  approvals: Approval[];
  ptoRequested: { start: string; end: string; days: number } | null;
  worksheet: WorksheetLine[];
  candidates: Candidate[];
  toasts: Toast[];
}

type Action =
  | { type: "persona"; persona: Persona }
  | { type: "approve"; id: string; approve: boolean }
  | { type: "bulk-approve"; ids: string[] }
  | { type: "request-pto"; start: string; end: string; days: number }
  | { type: "merit"; id: string; pct: number; justification?: string }
  | { type: "advance-candidate"; id: string; stage: string }
  | { type: "toast"; text: string; warn?: boolean }
  | { type: "dismiss-toast"; id: number };

let toastSeq = 1;
const toast = (s: State, text: string, warn = false): State => ({
  ...s, toasts: [...s.toasts.slice(-3), { id: toastSeq++, text, warn }],
});

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "persona":
      return { ...state, persona: action.persona };
    case "approve": {
      const item = state.approvals.find((a) => a.id === action.id);
      const next = {
        ...state,
        approvals: state.approvals.map((a) =>
          a.id === action.id ? { ...a, status: action.approve ? "approved" as const : "rejected" as const } : a),
      };
      return toast(next, `${action.approve ? "Approved" : "Rejected"}: ${item?.subject} — ${item?.type}`);
    }
    case "bulk-approve": {
      const barred = state.approvals.filter((a) => action.ids.includes(a.id) && a.bulkBarred);
      if (barred.length)
        return toast(state, "Compensation approvals require individual review — bulk action refused.", true);
      const next = {
        ...state,
        approvals: state.approvals.map((a) =>
          action.ids.includes(a.id) ? { ...a, status: "approved" as const } : a),
      };
      return toast(next, `Approved ${action.ids.length} items`);
    }
    case "request-pto":
      return toast(
        { ...state, ptoRequested: { start: action.start, end: action.end, days: action.days } },
        `PTO request submitted (${action.days}d) — routed to Morgan Lee`);
    case "merit": {
      const line = state.worksheet.find((l) => l.id === action.id)!;
      const [lo, hi] = line.guideline;
      const out = action.pct < lo || action.pct > hi;
      if (out && !action.justification)
        return toast(state, `${action.pct}% is outside guideline ${lo}–${hi}% — justification required.`, true);
      const next = {
        ...state,
        worksheet: state.worksheet.map((l) =>
          l.id === action.id ? { ...l, merit: action.pct, justification: action.justification } : l),
      };
      return toast(next, `Recommendation saved: ${line.name} +${action.pct}%${out ? " (out of guideline, flagged)" : ""}`);
    }
    case "advance-candidate":
      return {
        ...state,
        candidates: state.candidates.map((c) =>
          c.id === action.id ? { ...c, stage: action.stage } : c),
      };
    case "toast":
      return toast(state, action.text, action.warn);
    case "dismiss-toast":
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.id) };
    default:
      return state;
  }
}

const initial: State = {
  persona: "employee",
  approvals: APPROVALS,
  ptoRequested: null,
  worksheet: WORKSHEET,
  candidates: CANDIDATES,
  toasts: [],
};

const StoreCtx = createContext<{ state: State; dispatch: React.Dispatch<Action> } | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initial);
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return <StoreCtx.Provider value={value}>{children}</StoreCtx.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreCtx);
  if (!ctx) throw new Error("useStore outside StoreProvider");
  return ctx;
}
