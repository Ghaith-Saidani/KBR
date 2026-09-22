export interface AnalyticsQueryRequest {
  query: string;
}

export interface AnalyticsResult {
  type: "metric" | "trend" | "comparison";
  metric: string;
  value: number | null;
  label: string;
  source: string;

  start_date: string | null;
  end_date: string | null;

  months: [string, number][] | null;

  first_period_label: string | null;
  first_value: number | null;

  second_period_label: string | null;
  second_value: number | null;

  difference: number | null;
  percentage_change: number | null;
}

export interface AnalyticsQueryResponse {
  supported: boolean;
  result: AnalyticsResult | null;
}