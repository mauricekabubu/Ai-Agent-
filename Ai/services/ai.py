import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition

from prompts.prompt import SYSTEM_PROMPT
from tools.tools import ALL_TOOLS

load_dotenv()


class AIService:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            api_key=os.getenv("GEMINI_API_KEY"),
        ).bind_tools(ALL_TOOLS)        
        self.tool_node = ToolNode(ALL_TOOLS)
        self.graph = self._build_graph()

    def _build_graph(self):
        def call_model(state: MessagesState):
            response = self.llm.invoke(state["messages"])
            return {"messages": [response]}

        builder = StateGraph(MessagesState)

        builder.add_node("call_model", call_model)
        builder.add_node("tools", self.tool_node)

        builder.add_edge(START, "call_model")

        builder.add_conditional_edges(
            "call_model",
            tools_condition,
        )

        builder.add_edge("tools", "call_model")

        return builder.compile()

    def chat(self, messages):
        # System prompt goes in as the first message in LangGraph's world
        lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for message in messages:
            if message["role"] == "system":
                continue
            elif message["role"] == "user":
                lc_messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                lc_messages.append(AIMessage(content=message["content"]))

        result = self.graph.invoke({"messages": lc_messages})

        last_message = result["messages"][-1]
        content = last_message.content

        # Gemini may return structured content blocks
        if isinstance(content, list):
            text = ""

            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")

            return text

        return str(content)
        