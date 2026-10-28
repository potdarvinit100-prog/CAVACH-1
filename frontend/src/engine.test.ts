// CAVACH frontend parity tests — same audit cases as backend/scenarios.json.
// Run: npm test (vitest). Python is the source of truth; a mismatch here
// must be fixed in this port, not hidden.
import { describe, it, expect } from "vitest";
import { fuse, redactForStorage } from "./engine";
const band = (text: string) => fuse([{ id: "a1", type: "message", text }]).band;
const signals = (text: string) => fuse([{ id: "a1", type: "message", text }]).unique_findings.map((f) => f.signal);
describe("audit cases (Python parity)", () => {
  it("Marathi relative-payment + lookalike HDFC link is High", () => {
    expect(band("आई, मी अडचणीत आहे, ५००० रुपये पाठव, कोणाला सांगू नकोस https://pay-hdfc-secure.xyz/pay")).toBe("High concern");
  });
  it("Hindi relative + new number is High", () => {
    expect(band("माँ, मेरा नया नंबर है, इसे सेव कर लो, 2000 रुपये भेजो urgently, किसी को मत बताना")).toBe("High concern");
  });
  it("Genuine OTP notice is Low, not Suspicious", () => {
    expect(band("Your OTP is 482913. Do not share it with anyone. -HDFC Bank")).toBe("Low concern");
    expect(signals("Your OTP is 482913. Do not share it with anyone. -HDFC Bank")).toContain("genuine_notice_protective");
  });
  it("Punycode PayPal lookalike is Suspicious", () => {
    expect(band("Verify here: https://xn--pypal-4ve.com/login")).toBe("Suspicious");
    expect(signals("Verify here: https://xn--pypal-4ve.com/login")).toContain("lookalike_domain");
  });
  it("Real PayPal is Low", () => {
    expect(band("Download from https://www.paypal.com/help when convenient.")).toBe("Low concern");
  });
  it("Benign family greeting does not flag relative impersonation", () => {
    expect(signals("आई, कशी आहेस? उद्या फोन कर.")).not.toContain("relative_impersonation");
  });
  it("Redaction removes OTP digits before storage", () => {
    const { redacted, wasRedacted } = redactForStorage("Your OTP is 482913. Do not share it.");
    expect(wasRedacted).toBe(true);
    expect(redacted).not.toContain("482913");
    expect(redacted).toContain("[REDACTED]");
  });
});
