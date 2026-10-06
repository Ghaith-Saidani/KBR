export type AnalyticsResultType =
  | "metric"
  | "trend"
  | "comparison"
  | "distribution"
  | "growth"
  | "ranking";

export interface AnalyticsQueryRequest {
  query: string;
}

export interface AnalyticsResult {
  type: AnalyticsResultType;

  metric: string;
  label: string;
  source: string;

  value: number | null;

  start_date: string | null;
  end_date: string | null;

  months: [string, number][] | null;

  first_period_label: string | null;
  first_value: number | null;

  second_period_label: string | null;
  second_value: number | null;

  difference: number | null;
  percentage_change: number | null;

  categories: [string, number][] | null;

  current_period_label: string | null;
  current_value: number | null;

  previous_period_label: string | null;
  previous_value: number | null;

  direction: string | null;

  period_label: string | null;
  rank: number | null;
}

export interface AnalyticsQueryResponse {
  supported: boolean;
  result: AnalyticsResult | null;
}