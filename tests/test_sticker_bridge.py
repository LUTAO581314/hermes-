from __future__ import annotations

import unittest

from hermes_runtime.sticker_bridge import (
    build_outbound_payload,
    list_intents,
    select_sticker,
)


class StickerBridgeTests(unittest.TestCase):
    def test_select_sticker_returns_metadata_only_default(self) -> None:
        candidate = select_sticker("happy_praise")

        self.assertEqual(candidate.intent, "happy_praise")
        self.assertEqual(candidate.provider, "metadata_only")
        self.assertEqual(candidate.style, "kawaii_anime")
        self.assertFalse(candidate.preview_url)
        self.assertFalse(candidate.provider_ref)
        self.assertIn("anime", candidate.query)

    def test_unknown_intent_falls_back_to_cute_greeting(self) -> None:
        candidate = select_sticker("not_real")

        self.assertEqual(candidate.intent, "cute_greeting")
        self.assertEqual(candidate.text_fallback, "嘿嘿，来啦～")

    def test_feishu_payload_requires_runtime_upload(self) -> None:
        candidate = select_sticker("soft_comfort", provider="stipop")
        payload = build_outbound_payload(candidate, "feishu").to_dict()

        self.assertEqual(payload["channel"], "feishu")
        self.assertEqual(payload["action"], "resolve_runtime_upload_send")
        self.assertEqual(payload["provider"], "stipop")
        self.assertIn("image_key", " ".join(payload["instructions"]))
        self.assertTrue(payload["metadata"]["runtime_upload_required"])
        self.assertNotIn("api_key", payload)

    def test_image_generation_payload_is_review_upload_send(self) -> None:
        candidate = select_sticker("shy_like", provider="image_generation")
        payload = build_outbound_payload(candidate, "wechat")

        self.assertEqual(payload.action, "generate_review_upload_send")
        self.assertIn("original kawaii anime", payload.metadata["query"])
        self.assertEqual(payload.text_fallback, "哼，才没有很想你呢。")

    def test_list_intents_is_owner_reviewable(self) -> None:
        intents = list_intents()

        self.assertGreaterEqual(len(intents), 7)
        self.assertTrue(all("intent" in item for item in intents))
        self.assertTrue(any(item["intent"] == "sleepy_goodnight" for item in intents))


if __name__ == "__main__":
    unittest.main()
