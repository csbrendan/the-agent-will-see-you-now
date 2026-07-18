"""
Cut per-NIHSS-item media from the full NINDS exams using the segmentation manifests:
  - every item  -> <id>/<item>.mp4   (video clip, for eval + demo)
  - speech items -> <id>/<item>.wav  (16kHz mono audio, for audio-only tests)
Adds clip_path / audio_path to each item in the manifests.

Usage: ./.venv/bin/python sample_data/ninds/ninds_clips.py
"""
import json, os, glob, subprocess, time

ROOT = "/Users/brendanmurphy/Desktop/MedBridge/MedBridge"
SEG = os.path.join(ROOT, "sample_data/ninds/segmented")
VIDEOS = os.path.join(ROOT, "sample_data/ninds/videos")
SPEECH_ITEMS = {"1a", "1b", "1c", "9", "10"}   # audio-only / verbal tests

FF = "ffmpeg"
if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()


def cut_video(src, a, b, dst):
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b),
                    "-i", src, "-c:v", "libx264", "-c:a", "aac", dst], check=True)


def cut_audio(src, a, b, dst):
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b),
                    "-i", src, "-vn", "-ac", "1", "-ar", "16000", dst], check=True)


mans = sorted(glob.glob(os.path.join(SEG, "*", "manifest.json")))
t0 = time.time(); nv = na = 0
for mp in mans:
    man = json.load(open(mp)); ident = man["identifier"]
    src = os.path.join(VIDEOS, f"{ident}.mp4")
    outdir = os.path.dirname(mp)
    if not os.path.exists(src):
        print(f"[skip] {ident}: full mp4 missing"); continue
    for it in man["items"]:
        iid = it["item_id"]; a, b = it["start_s"], it["end_s"]
        vclip = os.path.join(outdir, f"{iid}.mp4")
        cut_video(src, a, b, vclip); it["clip_path"] = os.path.relpath(vclip, SEG); nv += 1
        if iid in SPEECH_ITEMS:
            wav = os.path.join(outdir, f"{iid}.wav")
            cut_audio(src, a, b, wav); it["audio_path"] = os.path.relpath(wav, SEG); na += 1
    json.dump(man, open(mp, "w"), indent=2)
    print(f"[{ident}] {len(man['items'])} clips (+{sum(1 for it in man['items'] if it['item_id'] in SPEECH_ITEMS)} audio) "
          f"| {nv} vid / {na} aud total, {time.time()-t0:.0f}s", flush=True)

# rebuild combined index
combined = {"dataset": "NINDS NIHSS (Internet Archive, CC0)",
            "videos": [json.load(open(m)) for m in mans]}
combined["n_videos"] = len(mans)
json.dump(combined, open(os.path.join(SEG, "ALL_manifest.json"), "w"), indent=2)
print(f"\nCLIPS COMPLETE: {nv} video clips + {na} audio clips in {time.time()-t0:.0f}s")
