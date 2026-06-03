import { WeeklyReviewDashboard } from "@/components/WeeklyReviewDashboard";
import { fetchWeeklyReviews, type WeeklyReviewRun } from "@/lib/journalReview";
import { normalizeRuntimeError, type RuntimeErrorInfo } from "@/lib/pythonRunner";

export const dynamic = "force-dynamic";

export default async function WeeklyReviewPage() {
  let reviews: WeeklyReviewRun[] = [];
  let error: RuntimeErrorInfo | null = null;

  try {
    reviews = await fetchWeeklyReviews({ limit: 5 });
  } catch (err) {
    error = normalizeRuntimeError(err);
  }

  return <WeeklyReviewDashboard reviews={reviews} error={error} />;
}
