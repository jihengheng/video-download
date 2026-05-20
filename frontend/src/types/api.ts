export interface VideoFormatOption {
  format_id: string;
  ext: string;
  resolution: string;
  filesize_mb?: number | null;
  note?: string | null;
  has_video?: boolean;
  has_audio?: boolean;
}

export interface InspectResponse {
  title: string;
  thumbnail_url?: string | null;
  duration_seconds?: number | null;
  source_platform: string;
  supports_summary: boolean;
  estimated_processing_minutes: number;
  formats: VideoFormatOption[];
}

export interface TaskArtifact {
  artifact_type: string;
  storage_key: string;
  download_url?: string | null;
  mime_type: string;
  size_bytes?: number | null;
}

export interface TaskItem {
  id: number;
  source_url: string;
  source_platform: string;
  video_title: string;
  thumbnail_url?: string | null;
  duration_seconds?: number | null;
  selected_format_id?: string | null;
  public_token: string;
  need_summary: boolean;
  status: string;
  progress: number;
  retry_count: number;
  error_code?: string | null;
  error_message?: string | null;
  can_retry: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  artifacts: TaskArtifact[];
}

export interface TaskListResponse {
  items: TaskItem[];
  total: number;
}

export interface SummaryResult {
  task_id: number;
  summary: string;
  key_points: string[];
  timeline: Array<{ time: string; label: string; description: string }>;
  title_suggestion?: string | null;
  tags: string[];
  transcript: string;
  transcript_segments: Array<{ start: number; end: number; text: string }>;
  artifacts: TaskArtifact[];
}

export interface QuotaResponse {
  quota_date: string;
  limit_count: number;
  used_count: number;
  remaining_count: number;
}
