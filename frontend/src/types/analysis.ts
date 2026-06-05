export type Severity = "high" | "medium" | "low";
export type ServiceName = "ec2" | "rds" | "s3" | "elb" | "ebs";

export const ALL_SERVICES: ServiceName[] = ["ec2", "rds", "s3", "elb", "ebs"];

export interface AnalyzeRequest {
  regions?: string[] | null;
  services: ServiceName[];
  tags: Record<string, string>;
}

export interface Finding {
  finding_id: string;
  severity: Severity;
  category: string;
  title: string;
  description: string;
  resource_id: string;
  resource_type: string;
  region: string;
  evidence: Record<string, unknown>;
  recommendation_hint?: string | null;
}

export interface EnrichedFinding {
  finding_id: string;
  ai_explanation?: string | null;
  fix_command?: string | null;
}

export interface AIEnrichment {
  summary: string;
  estimated_savings: string;
  enriched_findings: EnrichedFinding[];
  skipped: boolean;
  skip_reason?: string | null;
}

export interface AnalyzeResponse {
  cloud_provider: string;
  analysis_id?: string | null;
  account_id?: string | null;
  regions_scanned: string[];
  services_scanned: string[];
  tags_filter: Record<string, string>;
  resource_count: number;
  findings: Finding[];
  findings_summary: Record<string, number>;
  ai_enrichment?: AIEnrichment | null;
}

export interface RegionsResponse {
  cloud_provider: string;
  regions: string[];
  count: number;
}

export interface HistoryDetailResponse {
  cloud_provider: string;
  analysis: AnalysisHistoryItem & {
    analysis_result?: AnalyzeResponse | null;
  };
}

export interface AnalysisHistoryItem {
  id: string;
  user_id?: string | null;
  scan_scope?: Record<string, unknown>;
  regions_scanned: string[];
  services_scanned: string[];
  resources_scanned: number;
  issues_found: number;
  estimated_savings?: string | null;
  status: string;
  created_at?: string | null;
  workload_label?: string;
}

export interface HistoryListResponse {
  cloud_provider: string;
  count: number;
  analyses: AnalysisHistoryItem[];
}
