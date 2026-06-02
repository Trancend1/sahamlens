import { WeeklyReviewDashboard } from "@/components/WeeklyReviewDashboard";
import { fetchWeeklyReviews, type WeeklyReviewRun } from "@/lib/journalReview";

export const dynamic = "force-dynamic";

export default async function WeeklyReviewPage() {
  let reviews: WeeklyReviewRun[] = [];
  let error: string | null = null;

  try {
    reviews = await fetchWeeklyReviews({ limit: 5 });
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return <WeeklyReviewDashboard reviews={reviews} error={error} />;
}
