"""Print the agent's current definition (model, tools and instructions) from the Foundry project."""

import textwrap

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from .agent import AGENT_NAME, PROJECT_ENDPOINT


def main():
    with AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential()) as project:
        agent = project.agents.get(agent_name=AGENT_NAME)
    latest = agent["versions"]["latest"]
    definition = latest["definition"]
    print(f"Agente : {agent['name']} | versión: {latest['version']} | estado: {agent.get('state', 'enabled')}")
    print(f"Modelo : {definition['model']}")
    print("Herramientas:")
    for tool in definition["tools"]:
        print(f"  - {tool['type']:<17} {tool.get('server_label') or '':<15} {tool.get('server_url') or ''}")
    print("\nInstrucciones (system message):")
    for line in definition["instructions"].split("\n"):
        print(textwrap.fill(line, 110, subsequent_indent="   ") if line else "")


if __name__ == "__main__":
    main()
