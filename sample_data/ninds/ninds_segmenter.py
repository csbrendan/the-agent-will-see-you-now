"""
NINDS NIHSS auto-segmenter.
Video -> OCR title cards -> segment into NIHSS items -> sample exam frames -> gold manifest.

Usage: python ninds_segmenter.py <identifier> [<identifier> ...]
Downloads (if needed), segments, writes frames + manifest under OUT/<identifier>/.
"""
import os, sys, re, json, time, tempfile, urllib.request
import cv2
from ocrmac import ocrmac

BASE = "/private/tmp/claude-501/-Users-brendanmurphy-Desktop-MedBridge-MedBridge/53edde2c-b8aa-4a38-94d1-17f6536bea6b/scratchpad"
VID_DIR = os.path.join(BASE, "ninds")
OUT = os.path.join(BASE, "ninds_segmented")
os.makedirs(VID_DIR, exist_ok=True); os.makedirs(OUT, exist_ok=True)

OCR_INTERVAL_S = 1.2      # OCR one frame every N seconds
FRAMES_PER_ITEM = 3       # exam frames sampled per NIHSS item segment

# Canonical NIHSS items. Match on distinctive keywords (order matters: check
# QUESTIONS/COMMANDS before bare LOC; MOTOR ARM/LEG before generic).
NIHSS = [
    ("1b", "LOC Questions",      lambda t: "CONSCIOUSNESS" in t and "QUESTION" in t),
    ("1c", "LOC Commands",       lambda t: "CONSCIOUSNESS" in t and "COMMAND" in t),
    ("1a", "Level of Consciousness", lambda t: "CONSCIOUSNESS" in t),
    ("2",  "Best Gaze",          lambda t: "GAZE" in t),
    ("3",  "Visual Fields",      lambda t: "VISUAL" in t),
    ("4",  "Facial Palsy",       lambda t: "FACIAL" in t),
    ("5",  "Motor Arm",          lambda t: "MOTOR" in t and "ARM" in t),
    ("6",  "Motor Leg",          lambda t: "MOTOR" in t and "LEG" in t),
    ("7",  "Limb Ataxia",        lambda t: "ATAXIA" in t),
    ("8",  "Sensory",            lambda t: "SENSORY" in t),
    ("9",  "Best Language",      lambda t: "LANGUAGE" in t),
    ("10", "Dysarthria",         lambda t: "DYSARTHRIA" in t),
    ("11", "Extinction/Inattention", lambda t: "EXTINCTION" in t or "INATTENTION" in t or "NEGLECT" in t),
]
CARD_MARKERS = ("CERTIFICATION", "DEMONSTRATION")


def match_item(text):
    for iid, name, pred in NIHSS:
        if pred(text):
            return iid, name
    return None


def ocr_text(frame):
    tmp = os.path.join(tempfile.gettempdir(), "ocr_tmp.jpg")
    cv2.imwrite(tmp, frame)
    res = ocrmac.OCR(tmp).recognize()
    return " ".join(r[0] for r in res).upper().strip()


def segment(ident):
    path = os.path.join(VID_DIR, f"{ident}.mp4")
    if not os.path.exists(path):
        url = f"https://archive.org/download/{ident}/{ident}_512kb.mp4"
        urllib.request.urlretrieve(url, path)
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(round(fps * OCR_INTERVAL_S)))

    # 1) OCR timeline: at each sampled ts, what NIHSS item card (if any) is shown + patient header
    timeline = []   # (ts, item_id_or_None)
    patient_header = None
    t0 = time.time(); idx = 0; n_ocr = 0
    while idx < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok: break
        txt = ocr_text(fr); n_ocr += 1
        ts = idx / fps
        if patient_header is None and "PATIENT" in txt and ("EXAMINED" in txt or "GROUP" in txt or "DEMONSTRATION" in txt):
            patient_header = txt[:120]
        is_card = any(m in txt for m in CARD_MARKERS)
        m = match_item(txt) if is_card else None
        timeline.append((ts, m[0] if m else None, m[1] if m else None))
        idx += step
    ocr_secs = time.time() - t0

    # 2) Collapse to item segments: an item is "active" from its first card ts until the next item's card
    boundaries = []   # (item_id, item_name, start_ts)
    last_item = None
    for ts, iid, iname in timeline:
        if iid and iid != last_item:
            boundaries.append([iid, iname, ts, None])
            if boundaries and len(boundaries) > 1:
                boundaries[-2][3] = ts     # previous segment ends here
            last_item = iid
    if boundaries:
        boundaries[-1][3] = total / fps

    # 3) sample exam frames from each segment (skip ~2s of title card at the start)
    seg_out = os.path.join(OUT, ident); os.makedirs(seg_out, exist_ok=True)
    items = []
    for iid, iname, start, end in boundaries:
        exam_start = min(start + 2.0, end)      # skip the card
        span = max(0.1, end - exam_start)
        ts_list = [exam_start + span * (k + 1) / (FRAMES_PER_ITEM + 1) for k in range(FRAMES_PER_ITEM)]
        fpaths = []
        for k, ts in enumerate(ts_list):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * fps))
            ok, fr = cap.read()
            if not ok: continue
            fp = os.path.join(seg_out, f"{iid}_{k}.jpg")
            cv2.imwrite(fp, fr); fpaths.append(os.path.relpath(fp, OUT))
        items.append({"item_id": iid, "item_name": iname,
                      "start_s": round(start, 1), "end_s": round(end, 1),
                      "frame_paths": fpaths})
    cap.release()

    manifest = {"identifier": ident, "patient_header": patient_header,
                "duration_s": round(total / fps, 1), "n_items": len(items),
                "ocr_frames": n_ocr, "ocr_secs": round(ocr_secs, 1), "items": items}
    with open(os.path.join(seg_out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["ALL"]:
        idents = ["gov.hhs.ninds.stroke.1.3", "gov.hhs.ninds.stroke.1.4"] + \
                 [f"gov.hhs.ninds.stroke.2.{n}" for n in range(1, 18)]
    else:
        idents = args
    all_items = 0; t0 = time.time()
    for ident in idents:
        m = segment(ident)
        all_items += m["n_items"]
        print(f"[{ident}] {m['n_items']} items | ocr {m['ocr_frames']}f/{m['ocr_secs']}s | "
              f"hdr={ (m['patient_header'] or '')[:55] }")
        print("   items:", ", ".join(f"{it['item_id']}:{it['item_name']}({it['start_s']}-{it['end_s']}s,{len(it['frame_paths'])}f)"
                                     for it in m["items"]))
    print(f"\nTOTAL {len(idents)} videos, {all_items} item-segments in {time.time()-t0:.0f}s -> {OUT}")
