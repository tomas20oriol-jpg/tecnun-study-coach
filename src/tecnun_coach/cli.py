"""Terminal chat with the tecnun-study-coach agent."""

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError

from .agent import AGENT_NAME, PROJECT_ENDPOINT, StudyCoach

HELP = "Commands: /new (new conversation), /exit (quit)"


def main():
    print(f"Connecting to agent '{AGENT_NAME}' at {PROJECT_ENDPOINT} ...")
    try:
        coach = StudyCoach()
    except ClientAuthenticationError as e:
        raise SystemExit(f"Authentication failed. Run 'az login' first.\n{e.message}")
    print(f"Connected. {HELP}\n")

    try:
        while True:
            try:
                text = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                continue
            if text in ("/exit", "/quit"):
                break
            if text == "/new":
                coach.reset()
                print("New conversation started.\n")
                continue
            try:
                reply = coach.ask(text)
            except HttpResponseError as e:
                print(f"[error] {e.message}\n")
                continue
            except Exception as e:  # openai SDK errors
                print(f"[error] {e}\n")
                continue
            tools = f"  [tools: {', '.join(reply.tools)}]" if reply.tools else ""
            print(f"\nCoach >{tools}\n{reply.text}\n")
    finally:
        coach.close()
        print("Bye!")


if __name__ == "__main__":
    main()
