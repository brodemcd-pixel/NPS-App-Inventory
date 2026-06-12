"use client";

import type { MetaFilters } from "@/lib/api";

export interface TableFilters {
  q: string;
  draft_class: number[];
  round: number[];
  position_group: string[];
  position: string[];
  team: string;
  college: string;
  conference: string;
  height_min: string;
  height_max: string;
  weight_min: string;
  weight_max: string;
  forty_max: string;
  arm_min: string;
  hand_min: string;
  wingspan_min: string;
  scheme: string;
  coaching_tree: string;
  role: string;
  red_flag: boolean;
  green_flag: boolean;
  trait: string;
  trait_min: number;
}

export const EMPTY_FILTERS: TableFilters = {
  q: "",
  draft_class: [],
  round: [],
  position_group: [],
  position: [],
  team: "",
  college: "",
  conference: "",
  height_min: "",
  height_max: "",
  weight_min: "",
  weight_max: "",
  forty_max: "",
  arm_min: "",
  hand_min: "",
  wingspan_min: "",
  scheme: "",
  coaching_tree: "",
  role: "",
  red_flag: false,
  green_flag: false,
  trait: "",
  trait_min: 0.6,
};

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-1 mt-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
      {children}
    </div>
  );
}

const inputCls =
  "w-full rounded border border-ink-600 bg-ink-850 px-2 py-1 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-sky-700";
const selectCls = inputCls;

function ToggleChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded border px-2 py-0.5 text-[11px] transition-colors ${
        active
          ? "border-sky-600 bg-sky-900/60 text-sky-200"
          : "border-ink-600 bg-ink-850 text-slate-400 hover:border-ink-700 hover:text-slate-200"
      }`}
    >
      {children}
    </button>
  );
}

export default function FilterSidebar({
  meta,
  filters,
  onChange,
}: {
  meta: MetaFilters | null;
  filters: TableFilters;
  onChange: (f: TableFilters) => void;
}) {
  const set = <K extends keyof TableFilters>(key: K, value: TableFilters[K]) =>
    onChange({ ...filters, [key]: value });

  const toggleIn = <T,>(list: T[], v: T): T[] =>
    list.includes(v) ? list.filter((x) => x !== v) : [...list, v];

  const showArm = filters.position_group.includes("OL");
  const showHand = filters.position_group.includes("QB");
  const showWingspan = filters.position_group.includes("DB");

  const schemes = meta
    ? [...meta.offense_schemes, ...meta.defense_schemes]
    : [];

  return (
    <div className="text-xs">
      <div className="flex items-center justify-between">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
          Filters
        </h2>
        <button
          type="button"
          onClick={() => onChange(EMPTY_FILTERS)}
          className="text-[11px] text-slate-500 hover:text-sky-300"
        >
          Clear all
        </button>
      </div>

      <Label>Search</Label>
      <input
        value={filters.q}
        onChange={(e) => set("q", e.target.value)}
        placeholder="Player name…"
        className={inputCls}
      />

      <Label>Draft class</Label>
      <div className="flex flex-wrap gap-1">
        {(meta?.classes || []).map((c) => (
          <ToggleChip
            key={c}
            active={filters.draft_class.includes(c)}
            onClick={() => set("draft_class", toggleIn(filters.draft_class, c))}
          >
            {c}
          </ToggleChip>
        ))}
      </div>

      <Label>Draft round</Label>
      <div className="flex flex-wrap gap-1">
        {[1, 2, 3, 4, 5, 6, 7].map((r) => (
          <ToggleChip
            key={r}
            active={filters.round.includes(r)}
            onClick={() => set("round", toggleIn(filters.round, r))}
          >
            R{r}
          </ToggleChip>
        ))}
      </div>

      <Label>Position group</Label>
      <div className="flex flex-wrap gap-1">
        {(meta?.position_groups || []).map((g) => (
          <ToggleChip
            key={g}
            active={filters.position_group.includes(g)}
            onClick={() =>
              set("position_group", toggleIn(filters.position_group, g))
            }
          >
            {g}
          </ToggleChip>
        ))}
      </div>

      <Label>Position</Label>
      <div className="flex flex-wrap gap-1">
        {(meta?.positions || []).map((p) => (
          <ToggleChip
            key={p}
            active={filters.position.includes(p)}
            onClick={() => set("position", toggleIn(filters.position, p))}
          >
            {p}
          </ToggleChip>
        ))}
      </div>

      <Label>NFL team</Label>
      <select
        value={filters.team}
        onChange={(e) => set("team", e.target.value)}
        className={selectCls}
      >
        <option value="">Any team</option>
        {(meta?.teams || []).map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <Label>College</Label>
      <select
        value={filters.college}
        onChange={(e) => set("college", e.target.value)}
        className={selectCls}
      >
        <option value="">Any college</option>
        {(meta?.colleges || []).map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <Label>Conference</Label>
      <select
        value={filters.conference}
        onChange={(e) => set("conference", e.target.value)}
        className={selectCls}
      >
        <option value="">Any conference</option>
        {(meta?.conferences || []).map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <Label>Height (in)</Label>
      <div className="flex gap-1">
        <input
          value={filters.height_min}
          onChange={(e) => set("height_min", e.target.value)}
          placeholder="Min"
          inputMode="decimal"
          className={inputCls}
        />
        <input
          value={filters.height_max}
          onChange={(e) => set("height_max", e.target.value)}
          placeholder="Max"
          inputMode="decimal"
          className={inputCls}
        />
      </div>

      <Label>Weight (lb)</Label>
      <div className="flex gap-1">
        <input
          value={filters.weight_min}
          onChange={(e) => set("weight_min", e.target.value)}
          placeholder="Min"
          inputMode="numeric"
          className={inputCls}
        />
        <input
          value={filters.weight_max}
          onChange={(e) => set("weight_max", e.target.value)}
          placeholder="Max"
          inputMode="numeric"
          className={inputCls}
        />
      </div>

      <Label>40-yard max (s)</Label>
      <input
        value={filters.forty_max}
        onChange={(e) => set("forty_max", e.target.value)}
        placeholder="e.g. 4.55"
        inputMode="decimal"
        className={inputCls}
      />

      {showArm && (
        <>
          <Label>Arm length min (in) · OL</Label>
          <input
            value={filters.arm_min}
            onChange={(e) => set("arm_min", e.target.value)}
            placeholder="e.g. 33"
            inputMode="decimal"
            className={inputCls}
          />
        </>
      )}
      {showHand && (
        <>
          <Label>Hand size min (in) · QB</Label>
          <input
            value={filters.hand_min}
            onChange={(e) => set("hand_min", e.target.value)}
            placeholder="e.g. 9.25"
            inputMode="decimal"
            className={inputCls}
          />
        </>
      )}
      {showWingspan && (
        <>
          <Label>Wingspan min (in) · DB</Label>
          <input
            value={filters.wingspan_min}
            onChange={(e) => set("wingspan_min", e.target.value)}
            placeholder="e.g. 76"
            inputMode="decimal"
            className={inputCls}
          />
        </>
      )}

      <Label>Scheme archetype</Label>
      <select
        value={filters.scheme}
        onChange={(e) => set("scheme", e.target.value)}
        className={selectCls}
      >
        <option value="">Any scheme</option>
        {schemes.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      <Label>Coaching tree</Label>
      <select
        value={filters.coaching_tree}
        onChange={(e) => set("coaching_tree", e.target.value)}
        className={selectCls}
      >
        <option value="">Any tree</option>
        {(meta?.coaching_trees || []).map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <Label>Functional role</Label>
      <select
        value={filters.role}
        onChange={(e) => set("role", e.target.value)}
        className={selectCls}
      >
        <option value="">Any role</option>
        {(meta?.roles || []).map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>

      <Label>Flags</Label>
      <div className="flex gap-1">
        <ToggleChip
          active={filters.red_flag}
          onClick={() => set("red_flag", !filters.red_flag)}
        >
          ● Red flag
        </ToggleChip>
        <ToggleChip
          active={filters.green_flag}
          onClick={() => set("green_flag", !filters.green_flag)}
        >
          ● Green flag
        </ToggleChip>
      </div>

      <Label>Mental trait</Label>
      <select
        value={filters.trait}
        onChange={(e) => set("trait", e.target.value)}
        className={selectCls}
      >
        <option value="">Any trait</option>
        {(meta?.traits || []).map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
      {filters.trait && (
        <div className="mt-2">
          <div className="mb-1 flex justify-between text-[11px] text-slate-500">
            <span>Min score</span>
            <span className="num text-sky-300">
              {filters.trait_min.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filters.trait_min}
            onChange={(e) => set("trait_min", Number(e.target.value))}
          />
        </div>
      )}
    </div>
  );
}
