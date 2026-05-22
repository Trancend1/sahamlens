import type { EmotionLevel, RiskFlag } from "@/lib/journal-client";

const HIGH_EMOTION = new Set<EmotionLevel>(["fearful", "greedy", "excited"]);

interface CoolingOffBannerProps {
  emotion: EmotionLevel | null;
  riskFlag: RiskFlag | null;
}

export function CoolingOffBanner({ emotion, riskFlag }: CoolingOffBannerProps) {
  const emotionTriggered = emotion != null && HIGH_EMOTION.has(emotion);
  const riskTriggered = riskFlag === "red";

  if (!emotionTriggered && !riskTriggered) return null;

  const tags: string[] = [];
  if (emotionTriggered && emotion) tags.push(`Emosi: ${emotion}`);
  if (riskTriggered) tags.push("Risk flag: Red");

  return (
    <div
      role="alert"
      className="rounded-md border border-amber-500/40 bg-amber-500/[0.06] px-5 py-4"
    >
      <p className="text-sm font-semibold text-amber-300">⏸ Pertimbangkan cooling-off</p>
      <p className="mt-0.5 text-xs text-amber-200/70">{tags.join(" · ")}</p>
      <p className="mt-2 text-sm text-fg/80">
        Tunggu setidaknya 24 jam sebelum mengeksekusi rencana ini. AI explains, user decides.
      </p>
    </div>
  );
}
