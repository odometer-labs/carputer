export type LogSeverity = "error" | "warning" | "message";

export type LogEntry = {
  id: string;
  raw: string;
  timestamp: string;
  source: string;
  level: string;
  message: string;
  severity: LogSeverity;
};

export type ParsedSystemLog = {
  errors: LogEntry[];
  warnings: LogEntry[];
  messages: LogEntry[];
  total: number;
};

const EMPTY_FIELD = "Unknown";
const PYTHON_LOG_PATTERN =
  /^(?<timestamp>.+?) - (?<source>.+?) - (?<level>[A-Z]+): (?<message>.*)$/;

function classifySeverity(level: string, rawLine: string): LogSeverity {
  const normalizedLevel = level.toUpperCase();
  const normalizedLine = rawLine.toUpperCase();

  if (
    normalizedLevel.includes("ERROR") ||
    normalizedLevel.includes("CRITICAL")
  ) {
    return "error";
  }

  if (normalizedLevel.includes("WARN") || normalizedLine.includes("WARNING")) {
    return "warning";
  }

  return "message";
}

export function parseLogLine(rawLine: string, index: number): LogEntry {
  const trimmedLine = rawLine.trim();
  const match = trimmedLine.match(PYTHON_LOG_PATTERN);
  const timestamp = match?.groups?.timestamp?.trim() ?? EMPTY_FIELD;
  const source = match?.groups?.source?.trim() ?? EMPTY_FIELD;
  const level = match?.groups?.level?.trim() ?? "INFO";
  const message = match?.groups?.message?.trim() ?? trimmedLine;

  return {
    id: `${index}-${timestamp}-${source}`,
    raw: trimmedLine,
    timestamp,
    source,
    level,
    message,
    severity: classifySeverity(level, trimmedLine),
  };
}

export function parseSystemLog(rawLogFile: string): ParsedSystemLog {
  const entries = rawLogFile
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line, index) => parseLogLine(line, index))
    .reverse();

  return {
    errors: entries.filter((entry) => entry.severity === "error"),
    warnings: entries.filter((entry) => entry.severity === "warning"),
    messages: entries.filter((entry) => entry.severity === "message"),
    total: entries.length,
  };
}

export const EMPTY_PARSED_SYSTEM_LOG: ParsedSystemLog = {
  errors: [],
  warnings: [],
  messages: [],
  total: 0,
};
