import {
  Dumbbell,
  LucideIcon,
  Table2,
  Trophy,
  Waves,
  Zap,
} from "lucide-react";
import {
  CircleDot,
  Circle,
  Volleyball as VolleyballIcon,
} from "lucide-react";

export interface SportTheme {
  icon: LucideIcon;
  gradient: string;
  solid: string;
  light: string;
}

const DEFAULT_THEME: SportTheme = {
  icon: Trophy,
  gradient: "from-brand-from to-brand-to",
  solid: "bg-brand-from",
  light: "bg-indigo-50 text-indigo-700",
};

const SPORT_THEMES: Record<string, SportTheme> = {
  badminton: {
    icon: CircleDot,
    gradient: "from-teal-600 to-cyan-500",
    solid: "bg-teal-600",
    light: "bg-teal-50 text-teal-700",
  },
  cricket: {
    icon: Circle,
    gradient: "from-orange-600 to-red-500",
    solid: "bg-orange-600",
    light: "bg-orange-50 text-orange-700",
  },
  football: {
    icon: Circle,
    gradient: "from-green-600 to-lime-500",
    solid: "bg-green-600",
    light: "bg-green-50 text-green-700",
  },
  tennis: {
    icon: CircleDot,
    gradient: "from-yellow-500 to-lime-400",
    solid: "bg-yellow-500",
    light: "bg-yellow-50 text-yellow-700",
  },
  table_tennis: {
    icon: Table2,
    gradient: "from-pink-600 to-rose-500",
    solid: "bg-pink-600",
    light: "bg-pink-50 text-pink-700",
  },
  volleyball: {
    icon: VolleyballIcon,
    gradient: "from-blue-600 to-indigo-500",
    solid: "bg-blue-600",
    light: "bg-blue-50 text-blue-700",
  },
  basketball: {
    icon: Circle,
    gradient: "from-amber-600 to-orange-500",
    solid: "bg-amber-600",
    light: "bg-amber-50 text-amber-700",
  },
  pickleball: {
    icon: CircleDot,
    gradient: "from-purple-600 to-fuchsia-500",
    solid: "bg-purple-600",
    light: "bg-purple-50 text-purple-700",
  },
  swimming: {
    icon: Waves,
    gradient: "from-cyan-600 to-blue-500",
    solid: "bg-cyan-600",
    light: "bg-cyan-50 text-cyan-700",
  },
  gym: {
    icon: Dumbbell,
    gradient: "from-slate-600 to-zinc-500",
    solid: "bg-slate-600",
    light: "bg-slate-100 text-slate-700",
  },
  snooker: {
    icon: Zap,
    gradient: "from-emerald-600 to-green-500",
    solid: "bg-emerald-600",
    light: "bg-emerald-50 text-emerald-700",
  },
};

export function getSportTheme(sport: string | null | undefined): SportTheme {
  if (!sport) return DEFAULT_THEME;
  return SPORT_THEMES[sport.toLowerCase()] ?? DEFAULT_THEME;
}

export function sportLabel(sport: string): string {
  return sport.replace(/_/g, " ");
}
