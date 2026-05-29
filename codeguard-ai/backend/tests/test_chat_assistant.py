import unittest

from app.api.dependencies import get_current_user_optional
from app.api.endpoints.chat import _local_assistant_reply


class ChatAssistantTests(unittest.TestCase):
    def test_get_current_user_optional_returns_none_without_credentials(self):
        async def run_test():
            result = await get_current_user_optional(credentials=None, db=None)
            self.assertIsNone(result)

        import asyncio

        asyncio.run(run_test())

    def test_project_specific_reply_mentions_core_stack(self):
        reply = _local_assistant_reply(
            "What is this CodeGuard AI project and how does the chat assistant help?"
        )

        lowered = reply.lower()
        self.assertIn("codeguard ai", lowered)
        self.assertIn("fastapi", lowered)
        self.assertIn("next.js", lowered)
        self.assertIn("scan", lowered)


if __name__ == "__main__":
    unittest.main()
