import os
import unittest

from models.media import Modality, Observability
from sample_data.ninds.manifest import get_clip_path, get_transcript, load_manifest
from video.processor import (
    FRAME_BUDGET,
    ITEM_PROFILES,
    SamplingProfile,
    extract_for_item,
    profile_for,
    to_anthropic_content,
)

_MANIFEST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_data", "ninds", "segmented", "gov.hhs.ninds.stroke.1.3", "manifest.json",
)


class TestItemProfiles(unittest.TestCase):
    def test_speech_items_use_none_sampling_profile(self):
        for item_id in ("1b", "9", "10"):
            self.assertEqual(ITEM_PROFILES[item_id].sampling, SamplingProfile.NONE)
            self.assertEqual(ITEM_PROFILES[item_id].modality, Modality.AUDIO)

    def test_sensory_item_is_not_assessable(self):
        self.assertEqual(ITEM_PROFILES["8"].observability, Observability.NOT_ASSESSABLE)
        self.assertEqual(ITEM_PROFILES["8"].modality, Modality.CONTACT)

    def test_motor_items_recommend_pose(self):
        self.assertTrue(ITEM_PROFILES["5"].pose_recommended)
        self.assertTrue(ITEM_PROFILES["6"].pose_recommended)

    def test_profile_for_resolves_per_limb_suffix(self):
        self.assertEqual(profile_for("5a").item_id, "5")
        self.assertEqual(profile_for("6b").item_id, "6")

    def test_profile_for_unknown_item_raises(self):
        with self.assertRaises(KeyError):
            profile_for("not_a_real_item")

    def test_frame_budget_covers_every_sampling_profile(self):
        for profile in SamplingProfile:
            self.assertIn(profile, FRAME_BUDGET)

    def test_none_profile_yields_zero_frames(self):
        self.assertEqual(FRAME_BUDGET[SamplingProfile.NONE].n_for(30.0), 0)

    def test_temporal_profile_is_rate_based_not_flat(self):
        spec = FRAME_BUDGET[SamplingProfile.TEMPORAL]
        # A longer window should yield more frames than a shorter one (rate-based),
        # unlike a flat per-item count.
        self.assertGreater(spec.n_for(20.0), spec.n_for(5.0))


@unittest.skipUnless(os.path.exists(_MANIFEST_PATH), "real NINDS manifest not present — run sample_data/ninds/*.py")
class TestExtractForItemRealData(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest(_MANIFEST_PATH)

    def test_temporal_item_samples_frames_from_real_clip(self):
        clip_path = get_clip_path(self.manifest, "5")
        self.assertIsNotNone(clip_path)
        bundle = extract_for_item(clip_path, item_id="5", item_name="Motor Arm")
        self.assertGreater(len(bundle.frames), 0)
        self.assertTrue(bundle.assessable_from_video)
        self.assertTrue(bundle.pose_recommended)
        # Frames must carry an explicit temporal order/timestamp (fact #2 from the
        # module docstring) so the model can infer the trajectory.
        timestamps = [f.timestamp_s for f in bundle.frames]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_sensory_item_is_marked_not_assessable_even_with_frames(self):
        clip_path = get_clip_path(self.manifest, "5")  # any real clip; policy applies regardless
        bundle = extract_for_item(clip_path, item_id="8")
        self.assertFalse(bundle.assessable_from_video)
        self.assertTrue(any("not establishable from ordinary" in lim for lim in bundle.limitations))

    def test_speech_item_has_transcript_but_no_frames(self):
        clip_path = get_clip_path(self.manifest, "10")
        bundle = extract_for_item(clip_path, item_id="10")
        self.assertEqual(bundle.frames, [])
        transcript = get_transcript(self.manifest, "10")
        self.assertTrue(len(transcript) > 0)

    def test_unknown_item_id_raises(self):
        clip_path = get_clip_path(self.manifest, "5")
        with self.assertRaises(KeyError):
            extract_for_item(clip_path, item_id="not_a_real_item")

    def test_missing_video_path_raises(self):
        with self.assertRaises(FileNotFoundError):
            extract_for_item("/no/such/file.mp4", item_id="5")

    def test_to_anthropic_content_interleaves_timeline_before_images(self):
        clip_path = get_clip_path(self.manifest, "4")
        bundle = extract_for_item(clip_path, item_id="4", max_frames=3)
        content = to_anthropic_content(bundle)
        # header text block, then (label, image) pairs
        self.assertEqual(content[0]["type"], "text")
        self.assertEqual(content[1]["type"], "text")
        self.assertEqual(content[2]["type"], "image")

    def test_to_anthropic_content_flags_not_assessable_items_in_header(self):
        clip_path = get_clip_path(self.manifest, "5")
        bundle = extract_for_item(clip_path, item_id="8")
        content = to_anthropic_content(bundle)
        self.assertIn("CANNOT be graded from video", content[0]["text"])


if __name__ == "__main__":
    unittest.main()
