"""Authentication and connection to the tecnun-study-coach agent in Microsoft Foundry."""

import os
from dataclasses import dataclass, field

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://foundry-tecnun-resource.services.ai.azure.com/api/projects/foundry-tecnun-project",
)
AGENT_NAME = os.getenv("FOUNDRY_AGENT_NAME", "tecnun-study-coach")


def _tools_used(output) -> list[str]:
    """Tool calls in a response, e.g. 'code_interpreter' or 'mcp:github_issues' (MCP calls show their server)."""
    used = set()
    for item in output:
        if item.type == "mcp_call":
            used.add(f"mcp:{item.server_label}")
        elif item.type.endswith("_call"):
            used.add(item.type.removesuffix("_call"))
    return sorted(used)


@dataclass
class Reply:
    text: str
    tools: list[str] = field(default_factory=list)


class StudyCoach:
    """One conversation with the agent. Auth uses DefaultAzureCredential (az login, env vars or managed identity)."""

    def __init__(self):
        self._credential = DefaultAzureCredential()
        self._project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=self._credential)
        self._openai = self._project.get_openai_client()
        self.conversation_id = self._openai.conversations.create().id

    def ask(self, text: str) -> Reply:
        response = self._openai.responses.create(
            conversation=self.conversation_id,
            input=text,
            extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        )
        return Reply(text=response.output_text, tools=_tools_used(response.output))

    def _delete_conversation(self):
        """Delete the current conversation from Foundry so no chat history is kept."""
        if not self.conversation_id:
            return
        try:
            self._openai.conversations.delete(self.conversation_id)
        except Exception:
            pass  # already gone or network issue: nothing else to clean up
        self.conversation_id = None

    def reset(self):
        self._delete_conversation()
        self.conversation_id = self._openai.conversations.create().id

    def close(self):
        self._delete_conversation()
        self._project.close()
        self._credential.close()
