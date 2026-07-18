"""
NINDS audio pass: transcribe each exam (faster-whisper) and map the transcript onto the
NIHSS item windows already in the segmentation manifests. Adds a `transcript` field per item.

Usage: ./.venv/bin/python sample_data/ninds/ninds_audio.py
Requires the segmentation manifests (sample_data/ninds/segmented/) + the mp4s (scratchpad/ninds/).
"""
import json, os, glob, time
from faster_whisper import WhisperModel

VID_DIR = "/private/tmp/claude-501/-Users-brendanmurphy-Desktop-MedBridge-MedBridge/53edde2c-b8aa-4a38-94d1-17f6536bea6b/scratchpad/ninds"
SEG = "/Users/brendanmurphy/Desktop/MedBridge/MedBridge/sample_data/ninds/segmented"
MODEL = os.environ.get("MEDBRIDGE_WHISPER_MODEL", "base")

model = WhisperModel(MODEL, device="cpu", compute_type="int8")
mans = sorted(glob.glob(os.path.join(SEG, "*", "manifest.json")))
combined = {"dataset": "NINDS NIHSS (Internet Archive, CC0)", "audio_model": f"faster-whisper:{MODEL}",
            "videos": []}
t0 = time.time(); done = 0
for mp in mans:
    man = json.load(open(mp))
    ident = man["identifier"]
    vid = os.path.join(VID_DIR, f"{ident}.mp4")
    if not os.path.exists(vid):
        print(f"[skip] {ident}: mp4 not found"); combined["videos"].append(man); continue
    segments, info = model.transcribe(vid, language="en", vad_filter=True)
    segs = [(s.start, s.end, s.text.strip()) for s in segments]

    def txt_for(a, b):
        return " ".join(t for s, e, t in segs if e > a and s < b).strip()

    for it in man["items"]:
        it["transcript"] = txt_for(it["start_s"], it["end_s"])
    man["audio_model"] = f"faster-whisper:{MODEL}"
    man["n_transcript_segments"] = len(segs)
    json.dump(man, open(mp, "w"), indent=2)
    combined["videos"].append(man)
    done += 1
    print(f"[{ident}] {len(segs)} segs, {man['n_items']} items transcribed "
          f"({done}/{len(mans)}, {time.time()-t0:.0f}s elapsed)", flush=True)

combined["n_videos"] = len(combined["videos"])
json.dump(combined, open(os.path.join(SEG, "ALL_manifest.json"), "w"), indent=2)
print(f"\nAUDIO PASS COMPLETE: {done}/{len(mans)} videos in {time.time()-t0:.0f}s "
      f"-> transcripts added to manifests + ALL_manifest.json")
