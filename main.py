from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain.tools import tool
import os

# Load environment variables
load_dotenv()


# =========================================================
# TOOLS
# =========================================================

@tool
def shut():
    """Shuts down the Windows computer after 5 seconds."""

    os.system("shutdown -s -t 5")
    return "Computer will shut down in 5 seconds."


@tool
def cancel_shutdown():
    """Cancels any scheduled shutdown."""

    os.system("shutdown -a")
    return "Shutdown cancelled."


@tool
def restart():
    """Restarts the Windows computer after 5 seconds."""

    os.system("shutdown -r -t 5")
    return "Computer will restart in 5 seconds."


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():
    try:
        # Initialize Gemini model
        model = ChatGoogleGenerativeAI(
            model="models/gemini-3.1-flash-lite-preview",
            temperature=0
        )

        # Register tools
        tools = [shut, cancel_shutdown, restart]

        # Create agent
        agent_executor = create_react_agent(
            model=model,
            tools=tools
        )

        print("\n" + "-" * 60)
        print("Welcome! I'm your AI assistant.")
        print("Type 'quit' to exit.")
        print("-" * 60)

        while True:

            user_input = input("\nYou: ").strip()

            # Exit program
            if user_input.lower() == "quit":
                print("\nGoodbye!")
                break

            # Invoke agent
            response = agent_executor.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                }
            )

            # Get last assistant message
            last_message = response["messages"][-1]
            content = last_message.content

            print("\nAssistant:")

            # Clean output formatting
            if isinstance(content, list):

                text_found = False

                for item in content:

                    if (
                        isinstance(item, dict)
                        and item.get("type") == "text"
                    ):
                        print(item.get("text"))
                        text_found = True

                if not text_found:
                    print(content)

            else:
                print(content)

    except Exception as e:
        print(f"\nError occurred:\n{e}")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    main()