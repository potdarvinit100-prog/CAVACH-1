# Maharashtra Cyber video — product research analysis

Source file: `workspace/user/media_library/video/ad/ade5476c4ace1b802bee59dfdba6ed8bbecdb643cdcda194c755389be172cba9.mp4`
Verified: 100.3 seconds, 15.5 MB. Analysis below is from the visual frames / on-screen
text supplied with the upload. No audio transcript was supplied, so no dialogue is
quoted and no spoken demand is claimed. Where a frame is ambiguous, that is stated.

## 1. What the video actually shows (evidence only)

Opening cards (0–7s):
- "महाराष्ट्र शासन प्रस्तुत सायबर जनजागृती अभियान" — Maharashtra Government presents
  a Cyber Awareness Campaign.
- "सायबर फसवणूक झाल्यास त्वरित संपर्क साधा — 1930 | ऑनलाइन तक्रार www.cybercrime.gov.in
  | सतर्क राहा, सुरक्षित राहा." — If cyber fraud happens, contact immediately on 1930;
  online complaint at cybercrime.gov.in; stay alert, stay safe.
- Second card: "A Cyber Awareness Initiative by the Government of Maharashtra — DIAL 1930",
  with the Maharashtra government emblem, Maharashtra Police emblem and Maharashtra
  Cyber shield.

Intro text (7–13s, Marathi):
- "प्रिय नागरिकांनो, सायबर गुन्हे आणि ऑनलाइन फसवणुकीपासून नागरिकांचे संरक्षण
  करण्यासाठी महाराष्ट्र सायबर, महाराष्ट्र शासनामार्फत ही माहिती देण्यात येत आहे."
  — Dear citizens, this information is being given by Maharashtra Cyber, Government of
  Maharashtra, to protect citizens from cyber crime and online fraud.

Dramatised scene (13–71s):
- An older man at a home-office desk takes a video call on a phone propped on a stand.
- The call screen is labelled "Unknown" / "Connected". That label is the only
  caller-verification signal visible in the frames.
- The caller wears a police uniform, seated in front of a Maharashtra Police emblem
  backdrop. Visual authority cues are the whole costume: uniform + emblem + formal setting.
- The phone then displays a document headed "SUPREME COURT OF INDIA" in a green border.
  The body text of that document is not legible in the frames, so its exact claims are
  NOT asserted here.
- The man reacts with visible distress and gesturing during the call, and is calmer in
  the closing shots of the scene. The frames alone do not establish the exact plot
  resolution (whether he paid, refused, or hung up), so no outcome is claimed.

Closing message (71–96s):
- "सावध राहा, फसणार नाही! हम बेवकूफ नहीं बनेंगे" — Stay alert, will not be cheated!
  We will not be made fools.
- "डायल करा १९३०" — Dial 1930 (Marathi numerals).
- A closing address segment shows a speaker in front of a Maharashtra map graphic.
  Its exact wording is not reliably readable from the frames, so it is not quoted.

Persistent footer (throughout the scene):
- "कोणत्याही सायबर गुन्ह्याची तक्रार नोंदवण्यासाठी www.mhcyber.gov.in या संकेतस्थळाला
  भेट द्या किंवा हेल्पलाइन क्रमांक १९३० वर संपर्क साधा. अधिक माहितीसाठी आम्हाला फॉलो करा."
  — To register a complaint about any cyber crime, visit mhcyber.gov.in or contact
  helpline 1930. Follow for more information.
- Social handles shown: Facebook /MaharashtraCyber, Instagram /maharashtracyber,
  X /MahaCyber1, YouTube @maharashtracyber.

## 2. Scam technique this dramatises (inference, labelled as such)

The visual pattern — unknown video call + police uniform + police-emblem backdrop +
a court-headed document shown on screen — matches the well-documented
"digital arrest" / authority-impersonation pattern: a stranger borrows the visual
language of the state to create fear and compliance in real time. This is an
inference from the visuals, not a transcript of what the caller said, and it is
not evidence about any real incident.

Why it works, in product terms:
1. **Authority is visual, not verified.** Uniform + emblem + court letterhead can be
   staged. The victim has no independent check inside the call itself.
2. **Pressure is live.** A video call leaves no time to think, search, or ask someone.
   The decision window is seconds, while reporting (1930 / portal) is after the fact.
3. **"Unknown" is a weak signal.** It is easy to miss, and it does not explain itself
   ("unknown caller claiming state authority" is a very different warning).
4. **A document photo proves nothing.** A court-headed image sent over chat/video can
   be fabricated; legitimacy comes from the issuing channel, not the letterhead.

## 3. Problems the video reveals (the gap AI Cyber Guardian must close)

| # | Problem visible in the video | What exists today | Gap |
|---|------------------------------|-------------------|-----|
| 1 | No in-the-moment verification step | 1930 + cybercrime.gov.in + mhcyber.gov.in exist for reporting | All three are post-incident. Nothing helps the user *during* the call. |
| 2 | Reporting channels are fragmented | 1930 (phone), cybercrime.gov.in (national portal), mhcyber.gov.in (state) | A panicked user must remember which channel does what. |
| 3 | Awareness is Marathi-first, tools are English-first | The video itself is Marathi-first | Most URL/message checkers, and their explanations, are English-only. |
| 4 | The likely victim is older / less digital-literate | General awareness ads | No low-friction tool: paste the message, get a Marathi explanation + one next step. |
| 5 | Evidence disappears | Victims may delete the call/chat/document in panic or shame | No "preserve this evidence pack" step before reporting. |
| 6 | One victim = one isolated incident | Individual complaints | No way for a user to see that the same persona/document pattern hit others (privacy-preserving correlation only). |
| 7 | Authority claims are never checked against an independent source | Caller ID / Truecaller-style labels | No "call back on the number you already trust, never the number on screen" workflow built into the moment. |

## 4. What already addresses part of this (do not rebuild, integrate or link to)

- 1930 national helpline and cybercrime.gov.in for financial-fraud reporting and
  attempted fund-freeze coordination. Recovery is never guaranteed; the product must
  never promise reversal.
- Google Safe Browsing (baseline URL reputation, conservative — misses many fresh
  phishing sites) and VirusTotal (multi-engine lookup; a clean result does not mean
  safe, especially for domains under 24–72 hours old, and uploads are not private).
- Spam/scam call labelling on phones. Useful, but a label is not an explanation and
  does not cover a video call with a staged backdrop.
- Bank fraud lines and Sanchar Saathi / Chakshu for reporting fraud calls and SMS.
- CERT-In / MeitY guidance on voice-cloning and deepfake calls: verify by callback,
  use a family safe word, never share OTP on a call, never transfer under pressure,
  preserve evidence, report fast on 1930.

## 5. Features this video justifies (in priority order)

1. **Pause-Verify-Preserve card (Marathi-first).** One screen, three actions, no jargon:
   hang up / do not pay, call back on a number you already trust (not the on-screen
   number), save the evidence. This is the video's lesson turned into a tool.
2. **Authority-claim checker.** Paste a message/transcript or describe the call:
   flags police/court/bank + threat + secrecy + payment/document-pressure combinations,
   and explains *why* each flag matters, in Marathi and English.
3. **Document-scepticism check.** A court/bank/government document received over
   WhatsApp or shown on a video call is treated as unverified by default; the product
   lists what a real notice would arrive through, and what to verify independently.
   It never authenticates a document image as genuine.
4. **Evidence pack for 1930 / cybercrime.gov.in.** The user assembles, in order:
   caller label/screenshot (user-supplied), message text, URL, time, what was asked for,
   what was / was not paid. Export as a checklist + summary they can read to the
   helpline. No OTP, PIN, password or bank credential is ever collected.
5. **Cross-channel correlation (ThreatFusion).** Same impersonation narrative +
   same/similar domain + same payment pattern across submitted artifacts = a linked
   investigation with a stated confidence (confirmed / possible / unknown), never an
   accusation against a named person.
6. **CyberWatch, honestly scoped.** Opt-in, user-submitted events only
   in the prototype. No secret call recording, no private-conversation inspection,
   no bypassing OS restrictions. Every alert shows what was monitored and why.

## 6. What this video does NOT prove (guardrails for the pitch)

- It does not prove how common digital-arrest scams are, what victims lose, or what
  any specific caller said. Do not quote statistics from this video.
- It is an awareness film, not an endorsement of AI Cyber Guardian. Never imply
  Maharashtra Cyber / Maharashtra Police back the product.
- The Developers Arena notice dated 27 October 2026 was mentioned by Vinit but no
  document for it was supplied in this turn. No attack method, attacker, or impact is
  claimed for it anywhere in this project. If a notice is supplied later, it goes in
  as a separate, sourced note with the same discipline.
- Voice-cloning detection is NOT claimed from this video. The video shows a live
  person on video, not a synthetic voice. VoiceShield therefore stays as specified:
  suspicious *context* detection + verification guidance, with synthetic-audio
  claims explicitly disclaimed.

## 7. Presentation story the video hands us (live input)

"An older citizen gets an Unknown video call. The caller wears a uniform, sits in
front of a police emblem, and shows a Supreme Court-headed document. A judge types
that same kind of message and link into AI Cyber Guardian themselves. In one
screen: authority + threat + secrecy + payment-link flags, the lookalike-domain
check, the fused assessment — High concern, do not pay, verify by callback — and a
Marathi evidence pack ready for 1930. The same tool that the awareness film asks
people to remember after the fact, available during the incident."
