"""CAVACH labelled evaluation set (template-generated, synthetic).

Structure (honesty rules):
- BASE templates (42): rules were tuned against these during development.
  Variants of base templates (amount/domain swaps) measure robustness to
  surface changes, NOT unseen-template generalisation.
- HELDOUT templates (20): written AFTER the rules above were frozen for
  this run and NOT used for tuning. Their score is the honest
  unseen-phrasing check. If a held-out case fails, it is reported, not
  silently tuned away in this run.
All figures are test-set results, never real-world accuracy.
Total = base 42 + base variants 126 + held-out 20 = 188 cases.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import fuse

# Import base templates by re-using the lists from the previous version:
# they are reproduced here so this file is self-contained.
MALICIOUS = [
 ("en", "URGENT: Your account will be blocked today. Share your OTP now to keep it active: https://secure-bank-verify.xyz/login"),
 ("en", "This is police. You are under digital arrest. Pay 50000 immediately or face jail. Do not tell anyone."),
 ("en", "Mum, my phone broke, this is my new number. Please send 2000 urgently, don't tell anyone."),
 ("en", "Congratulations! You won Rs 25000. Pay a small processing fee to claim: https://prize-claim-now.top"),
 ("en", "Your KYC is expired. Update now or your account closes: https://kyc-update-bank.xyz"),
 ("en", "Parcel delivery failed. Pay Rs 50 to reschedule: https://parcel-delivery-pay.xyz"),
 ("en", "Your electricity bill is unpaid. Pay now or power will be cut tonight: https://bill-pay-electric.xyz"),
 ("en", "Install this app to receive your refund: https://refund-app-download.xyz/app.apk"),
 ("en", "Send Rs 1 to receive Rs 10000 cashback. UPI collect request sent, approve now."),
 ("en", "Investment opportunity: double your money in 7 days. Send money to this UPI id now, limited seats."),
 ("mr", "पोलिस बोलत आहे. तुम्ही डिजिटल अरेस्टमध्ये आहात. लगेच 50000 रुपये पाठवा, कोणाला सांगू नकोस."),
 ("mr", "आई, माझा नवीन नंबर आहे, ५००० रुपये पाठव, कोणाला सांगू नकोस https://pay-hdfc-secure.xyz/pay"),
 ("mr", "तुमचे KYC संपले आहे. खाते बंद होण्यापूर्वी अपडेट करा: https://kyc-update-bank.xyz"),
 ("mr", "अभिनंदन! तुम्ही 25000 रुपये जिंकले. दावा करण्यासाठी फी भरा: https://prize-claim-now.top"),
 ("hi", "पुलिस बोल रही है। आप डिजिटल अरेस्ट में हैं। तुरंत 50000 रुपये भेजो, किसी को मत बताना।"),
 ("hi", "माँ, मेरा नया नंबर है, इसे सेव कर लो, 2000 रुपये भेजो urgently, किसी को मत बताना"),
 ("hi", "आपका KYC समाप्त हो गया है। खाता बंद होने से पहले अपडेट करें: https://kyc-update-bank.xyz"),
 ("hi", "बधाई हो! आपने 25000 रुपये जीते हैं। दावा करने के लिए फीस भेजो: https://prize-claim-now.top"),
 ("hinglish", "Bhai urgent hai, police case ho gaya, 10000 bhej de abhi, kisi ko mat batana"),
 ("hinglish", "Mum new number hai mera, 2000 bhejo urgently, kisi ko mat batana"),
 ("roman-marathi", "Aai, majha navin number aahe, 5000 pathav, konala sangu nakos https://pay-hdfc-secure.xyz"),
 ("roman-marathi", "Police bolat aahe, tumhi digital arrest madhe aahat, lagach paise pathav"),
]
BENIGN = [
 ("en", "Hi, how are you? Let's catch up this weekend for coffee."),
 ("en", "Your order has been shipped and will arrive tomorrow. Track it in the app."),
 ("en", "Your bank statement for October is ready in the app. Your balance is Rs 45210."),
 ("en", "Your OTP is 482913. Do not share it with anyone. -HDFC Bank"),
 ("en", "Your parcel is out for delivery today between 2 and 5 pm."),
 ("en", "Meeting moved to 4 pm tomorrow. Please bring the report."),
 ("mr", "आई, कशी आहेस? उद्या घरी येतो, काही आणायचे आहे का?"),
 ("mr", "तुमची ऑर्डर पाठवली आहे, उद्या पोहोचेल."),
 ("mr", "तुमचे ऑक्टोबरचे बँक स्टेटमेंट अॅपमध्ये तयार आहे."),
 ("hi", "माँ, कैसे हो? कल घर आ रहा हूँ।"),
 ("hi", "आपका ऑर्डर भेज दिया गया है, कल पहुँच जाएगा।"),
 ("hi", "आपका OTP 482913 है। इसे किसी के साथ साझा न करें। -HDFC Bank"),
 ("hinglish", "Bhai kal milte hain, chai peete hain"),
 ("roman-marathi", "Aai, kashi aahes? Udya ghari yeto"),
]
TRICKY = [
 ("en", "Your OTP is 482913. Do not share it with anyone. Never share your OTP with callers."),
 ("en", "Your delivery from Amazon is arriving today. Track: https://www.amazon.in/order"),
 ("en", "Your electricity bill for October is Rs 1240, due on 15 November. Pay via the official app."),
 ("en", "Your parcel PIN code is 411001. Delivery agent will call from the official number."),
 ("mr", "तुमचा पिन कोड 411001 आहे. पार्सल आज पोहोचेल."),
 ("hi", "आपका पिन कोड 411001 है। पार्सल आज पहुँचेगा।"),
]

MALICIOUS += [
 ("en", "Your SIM card will be blocked in 2 hours. Verify now: https://sim-verify-now.xyz"),
 ("en", "Bank alert: suspicious login detected. Share your OTP to secure your account: https://bank-secure-login.xyz"),
 ("en", "You are selected for a work-from-home job. Pay Rs 999 for training material: https://wfh-job-offer.top"),
 ("en", "Your Aadhaar card is suspended. Update details immediately or face legal action: https://aadhaar-update-now.xyz"),
 ("en", "Electricity department: your bill payment failed. Pay Rs 10 to avoid disconnection: https://electric-bill-pay.xyz"),
 ("en", "Courier company: customs fee of Rs 850 is pending. Pay now: https://courier-customs-fee.xyz"),
 ("en", "Dear customer, your credit card points worth Rs 5000 are expiring. Redeem now: https://card-points-redeem.top"),
 ("en", "Police verification: your number is linked to illegal activity. Pay a fine to avoid arrest: https://police-verify-case.xyz"),
 ("en", "Congratulations, you are the lucky winner of a car. Pay registration tax of Rs 4999: https://lucky-winner-car.top"),
 ("en", "Your Netflix subscription expired. Update payment here: https://netflix-renew-pay.xyz"),
 ("mr", "तुमचे सिम कार्ड 2 तासांत बंद होईल. आत्ताच व्हेरिफाय करा: https://sim-verify-now.xyz"),
 ("mr", "बँक अलर्ट: संशयास्पद लॉगिन आढळले. OTP शेअर करा: https://bank-secure-login.xyz"),
 ("mr", "घरबसल्या नोकरीसाठी निवड झाली आहे. 999 रुपये भरा: https://wfh-job-offer.top"),
 ("mr", "तुमचे आधार कार्ड निलंबित झाले आहे. लगेच अपडेट करा नाहीतर कायदेशीर कारवाई होईल: https://aadhaar-update-now.xyz"),
 ("mr", "वीज विभाग: तुमचे बिल भरणे अयशस्वी झाले. खंडित होऊ नये म्हणून 10 रुपये भरा: https://electric-bill-pay.xyz"),
 ("hi", "आपका सिम कार्ड 2 घंटे में बंद हो जाएगा। अभी वेरिफाई करें: https://sim-verify-now.xyz"),
 ("hi", "बैंक अलर्ट: संदिग्ध लॉगिन मिला है। अपना OTP शेयर करें: https://bank-secure-login.xyz"),
 ("hi", "घर से काम की नौकरी के लिए आपका चयन हुआ है। 999 रुपये भेजो: https://wfh-job-offer.top"),
 ("hi", "आपका आधार कार्ड निलंबित हो गया है। तुरंत अपडेट करें नहीं तो कानूनी कार्रवाई होगी: https://aadhaar-update-now.xyz"),
 ("hi", "बिजली विभाग: आपका बिल भुगतान विफल हुआ। कटने से बचने के लिए 10 रुपये भेजो: https://electric-bill-pay.xyz"),
 ("hinglish", "Sir aapka account block ho jayega, OTP bhejo jaldi se: https://bank-secure-login.xyz"),
 ("hinglish", "Job offer hai, 999 registration fee bhejo: https://wfh-job-offer.top"),
 ("roman-marathi", "Tumcha sim card 2 tasat band hoil, aatach verify kara: https://sim-verify-now.xyz"),
 ("roman-marathi", "Bank alert aahe, OTP share kara: https://bank-secure-login.xyz"),
]
BENIGN += [
 ("en", "Your appointment with Dr. Sharma is tomorrow at 11 am. Please arrive 15 minutes early."),
 ("en", "School notice: tomorrow is a holiday for all classes."),
 ("en", "Your train ticket PNR 8123456789 is confirmed. Coach B2, seat 45."),
 ("en", "Reminder: your car insurance renewal is due next month."),
 ("en", "Your electricity bill for September was Rs 980, paid successfully."),
 ("en", "Team lunch on Friday at 1 pm. Please confirm your attendance."),
 ("mr", "शाळेची सूचना: उद्या सर्व वर्गांना सुट्टी आहे."),
 ("mr", "तुमची ट्रेन तिकीट कन्फर्म झाली आहे. कोच B2, सीट 45."),
 ("mr", "तुमचे सप्टेंबरचे वीज बिल 980 रुपये यशस्वीरित्या भरले आहे."),
 ("hi", "स्कूल सूचना: कल सभी कक्षाओं की छुट्टी है।"),
 ("hi", "आपकी ट्रेन टिकट कन्फर्म हो गई है। कोच B2, सीट 45।"),
 ("hi", "आपका सितंबर का बिजली बिल 980 रुपये सफलतापूर्वक भुगतान किया गया।"),
 ("hinglish", "Kal office me meeting hai 11 baje, please time par aana"),
 ("roman-marathi", "Udya shalet sutti aahe, saglyanna kalva"),
]

HELDOUT = [
 ("malicious", "en", "Your loan is approved. Pay Rs 1500 processing charge to release it: https://loan-release-fast.xyz"),
 ("malicious", "en", "Dear customer, your SIM will be deactivated today. Recharge via this link to continue: https://sim-reactivate.xyz"),
 ("malicious", "en", "Work from home job: earn Rs 5000 daily. Join by paying Rs 499 registration: https://job-earn-daily.top"),
 ("malicious", "en", "Your Aadhaar is linked to a fraud case. Verify immediately or face arrest: https://aadhaar-verify-case.xyz"),
 ("malicious", "hinglish", "Mummy, phone tut gaya, naya number hai, 3000 bhej do jaldi, kisi ko mat batana"),
 ("malicious", "mr", "आई, माझा मोबाईल हरवला, नवीन नंबरवरून बोलतोय, 3000 रुपये पाठव"),
 ("malicious", "mr", "बँक खाते बंद होणार आहे, आजच KYC अपडेट करा"),
 ("malicious", "en", "Congratulations! Your mobile number won a lucky draw. Claim Rs 10000 by paying tax: https://lucky-draw-claim.top"),
 ("malicious", "en", "Courier: your package is held at customs. Pay Rs 999 clearance fee: https://customs-clearance-pay.xyz"),
 ("malicious", "en", "Electricity: last warning, your connection will be cut in 2 hours unless you pay: https://power-bill-pay.xyz"),
 ("benign", "en", "Your flight is delayed by 30 minutes. New departure 6:45 pm."),
 ("benign", "en", "Reminder: parent-teacher meeting tomorrow at 10 am in school hall."),
 ("benign", "en", "Your UPI transaction of Rs 500 to Ramesh was successful. Ref: 123456."),
 ("benign", "mr", "माझी तब्येत ठीक आहे, काळजी करू नकोस."),
 ("benign", "hi", "कल सुबह 9 बजे दूधवाला आएगा।"),
 ("benign", "en", "Happy birthday! Hope you have a great day."),
 ("benign", "en", "Your library book is due on Friday. Please return it."),
 ("benign", "roman-marathi", "Aai, jevan jhale ka? Udya yeto."),
 ("benign", "en", "Your salary has been credited to your account."),
 ("benign", "en", "Weather alert: heavy rain expected tomorrow in Pune. Stay safe."),
]

def variants(text):
    out = []
    for old, new in [("2000", "3000"), ("5000", "7500"), ("25000", "50000"),
                     ("50000", "75000"), (".xyz", ".top"), (".top", ".xyz")]:
        if old in text:
            out.append(text.replace(old, new, 1))
    return out[:3]

def build():
    cases = []
    base = ([(l, t, "malicious") for l, t in MALICIOUS]
            + [(l, t, "benign") for l, t in BENIGN]
            + [(l, t, "benign") for l, t in TRICKY])
    for i, (lang, text, label) in enumerate(base):
        cases.append({"id": f"eval-base-{i:03d}", "label": label, "language": lang,
                      "split": "base", "text": text})
        for j, v in enumerate(variants(text)):
            cases.append({"id": f"eval-base-{i:03d}-v{j}", "label": label, "language": lang,
                          "split": "base-variant", "text": v})
    for i, (label, lang, text) in enumerate(HELDOUT):
        cases.append({"id": f"eval-held-{i:03d}", "label": label, "language": lang,
                      "split": "heldout", "text": text})
    return cases

def metrics(rs):
    tp = sum(1 for x in rs if x["label"] == "malicious" and x["predicted"] == "malicious")
    fp = sum(1 for x in rs if x["label"] == "benign" and x["predicted"] == "malicious")
    fn = sum(1 for x in rs if x["label"] == "malicious" and x["predicted"] == "benign")
    tn = sum(1 for x in rs if x["label"] == "benign" and x["predicted"] == "benign")
    return {"n": len(rs), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(tp / (tp + fp), 3) if tp + fp else 0,
            "recall": round(tp / (tp + fn), 3) if tp + fn else 0,
            "accuracy": round((tp + tn) / len(rs), 3) if rs else 0}

def run():
    rows = []
    for c in build():
        r = fuse([{"id": "a1", "type": "message", "text": c["text"]}])
        pred = "malicious" if r["band"] in ("High concern", "Suspicious") else "benign"
        rows.append({**c, "predicted": pred, "band": r["band"], "score": r["score"],
                     "correct": pred == c["label"]})
    report = {"generated_from": "template-generated labelled cases (synthetic, not real victim messages)",
              "n": len(rows), "overall": metrics(rows),
              "base": metrics([x for x in rows if x["split"] in ("base", "base-variant")]),
              "heldout": metrics([x for x in rows if x["split"] == "heldout"]),
              "per_language": {lang: metrics([x for x in rows if x["language"] == lang])
                               for lang in sorted({x["language"] for x in rows})},
              "errors": [{"id": x["id"], "split": x["split"], "language": x["language"],
                          "label": x["label"], "band": x["band"]} for x in rows if not x["correct"]],
              "note": "Test-set result, not real-world accuracy."}
    out = Path(__file__).resolve().parent / "evaluation_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({k: report[k] for k in ("n", "overall", "base", "heldout")}, indent=2))
    print("per_language:", json.dumps(report["per_language"], indent=2))
    print("errors:", json.dumps(report["errors"], ensure_ascii=False))
    print(f"Wrote {out}")
    return report

if __name__ == "__main__":
    run()
