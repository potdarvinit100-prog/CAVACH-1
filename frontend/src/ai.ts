// One free AI model, wired the honest way (fast slice).
//
// Model: Pollinations text endpoint — a keyless public endpoint serving
// open models. No API key exists anywhere in this file, so there is
// nothing to leak from the browser bundle. The trade-off is stated
// plainly: no SLA, and if the endpoint is unreachable (or blocks the
// browser), the caller falls back to the deterministic explanation.
//
// Privacy gate: this client sends ONLY redacted triage data — the band
// and the signal names with severity/confidence. It never sends the raw
// message, link, phone number, amount, or any credential. The UI keeps
// this behind an explicit opt-in checkbox (default off), so nothing
// leaves the device without the user's say-so.
//
// Authority: model output is display-only. It never changes the engine
// band, score, findings, or next step, and it is labelled as unverified
// model text wherever it appears.

export interface AiSignal {
  signal: string;
  severity: string;
  confidence: string;
}

export type AiResult =
  | { ok: true; text: string; model: string }
  | { ok: false; reason: string };

const ENDPOINT = "https://text.pollinations.ai/";
const MODEL_LABEL = "Pollinations (open model, keyless public endpoint)";

export async function explainWithFreeModel(input: {
  band: string;
  score: number;
  signals: AiSignal[];
  lang: string;
}): Promise<AiResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const langName = input.lang === "mr" ? "Marathi" : input.lang === "hi" ? "Hindi" : "English";
    const signalLines = input.signals
      .map((s) => `- ${s.signal} (severity: ${s.severity}, confidence: ${s.confidence})`)
      .join("\n");
    const userPrompt =
      `Explain this scam-risk triage result in plain, calm ${langName} that a non-technical person can understand, in under 120 words.\n` +
      `Band: ${input.band}. Internal ranking score: ${input.score} (this is NOT a probability).\n` +
      `Signals observed:\n${signalLines}\n` +
      `Rules: do not name any person as a criminal. Do not say the message is safe. Do not promise that money can be recovered. Do not invent facts beyond the signals above. End with one safe next step: verify the sender through an official channel you already trust.`;
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "openai",
        temperature: 0.2,
        messages: [
          {
            role: "system",
            content:
              "You explain scam-risk triage results only from the signals given. You never add facts, never judge a person, never promise recovery, and never call anything safe.",
          },
          { role: "user", content: userPrompt },
        ],
      }),
      signal: controller.signal,
    });
    if (!res.ok) return { ok: false, reason: `Model service returned HTTP ${res.status}` };
    const text = (await res.text()).trim().slice(0, 1500);
    if (!text) return { ok: false, reason: "Model returned an empty answer" };
    return { ok: true, text, model: MODEL_LABEL };
  } catch (e) {
    return {
      ok: false,
      reason: controller.signal.aborted
        ? "Model request timed out (20s)"
        : "Model unreachable — check your connection",
    };
  } finally {
    clearTimeout(timer);
  }
}
