import { z } from "zod";

export const TelemetryBatchSchema = z.object({
  batch_id: z.string().uuid(),
  sequence_number: z.number().int().nonnegative(),
  schema_version: z.string(),
  trace_id: z.string().uuid(),
  session_id: z.string().uuid(),
  timestamp_start: z.number().int().positive(),
  timestamp_end: z.number().int().positive(),
  keyboard: z.object({
    keystrokes: z.number().int().nonnegative(),
    backspaces: z.number().int().nonnegative(),
    longest_pause_ms: z.number().int().nonnegative(),
  }),
  mouse: z.object({
    distance_px: z.number().nonnegative(),
    clicks: z.number().int().nonnegative(),
    variance_x: z.number().nonnegative(),
    variance_y: z.number().nonnegative(),
  }),
  session: z.object({
    idle_time_ms: z.number().int().nonnegative(),
    tab_hidden: z.boolean(),
  }),
});

export type ValidatedTelemetryBatch = z.infer<typeof TelemetryBatchSchema>;
