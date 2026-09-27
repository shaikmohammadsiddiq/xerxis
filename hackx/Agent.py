from __future__ import annotations

import asyncio
import json
from typing import TypedDict, Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


# ============================================================
# CONFIGURATION
# ============================================================

MCP_SERVER = {
    "registrar": {
        "command": "python",
        "args": ["server.py"],
        "transport": "stdio",
    }
}


# ============================================================
# AGENT INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are an AI University Registrar Service Request Agent.

Your job is to process university service requests using
the available MCP tools.

Supported request categories:

1. Registration Hold
2. Transcript Request
3. Enrollment Verification
4. Grade Dispute
5. Tuition & Fee Billing


============================================================
CORE BEHAVIOR
============================================================

For every incoming request:

1. Understand the student's request.

2. Classify it into one of the supported categories.

3. Investigate relevant information using MCP tools
   when necessary.

4. Use previous request history to determine whether
   the current request may be related to an existing request.

5. For Tuition & Fee Billing requests, check the
   verified billing discrepancy before making a decision.

6. Reason over the information returned by the tools.

7. Take an appropriate action using the MCP action tools.

8. If information is insufficient, conflicting, or the
   request requires manual intervention, use
   flag_for_human_review.

9. Never invent student information, billing information,
   request history, or policy information.

10. Do not claim that an action succeeded unless the MCP
    tool returned a successful result.


============================================================
AVAILABLE INVESTIGATION TOOLS
============================================================

check_related_history
- Finds previous requests from the same student.
- Returns similarity scores and historical request details.

get_request_details
- Retrieves a historical request using request_id.

check_billing_discrepancy
- Checks verified billing discrepancy information.


============================================================
AVAILABLE ACTION TOOLS
============================================================

route_request
- Routes the request to a university department.

acknowledge_request
- Sends an acknowledgement for the request.

close_duplicate_request
- Closes a request when it is determined to be a duplicate.

flag_for_human_review
- Sends the request for human/manual review.

issue_courtesy_resolution
- Issues the automated courtesy resolution for an
  eligible billing case.


============================================================
HISTORY / DUPLICATE RULE
============================================================

Do not close a request as a duplicate merely because
a historical request exists.

Use the historical request content, status, and similarity
as evidence.

If the evidence is unclear, send the request for
human review instead of assuming it is a duplicate.


============================================================
BILLING RULE
============================================================

For Tuition & Fee Billing requests:

1. Check billing discrepancy information.

2. Examine the returned evidence.

3. If the evidence clearly supports an eligible
   courtesy resolution, use issue_courtesy_resolution.

4. If the evidence is missing, conflicting, or insufficient,
   use flag_for_human_review.

Do not invent eligibility criteria that are not provided.


============================================================
ACTION RULE
============================================================

Use investigation tools before action tools when evidence
is required.

Possible actions include:

- acknowledge
- route
- close as duplicate
- courtesy resolution
- human review

You may call multiple tools when necessary.


============================================================
FINAL RESPONSE
============================================================

After completing the workflow, provide a concise structured
result containing:

- request_id
- classification
- decision
- actions_taken
- reason

Do not expose internal chain-of-thought.
Provide only a concise explanation of the decision.
"""


# ============================================================
# MAIN AGENT
# ============================================================

async def create_registrar_agent():

    client = MultiServerMCPClient(MCP_SERVER)

    # Load tools exposed by the MCP server
    tools = await client.get_tools()

    print("\nLoaded MCP tools:")

    for tool in tools:
        print(f" - {tool.name}")

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    # --------------------------------------------------------
    # LangGraph ReAct Agent
    # --------------------------------------------------------

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )

    return agent


# ============================================================
# PROCESS REQUEST
# ============================================================

async def process_request(
    agent,
    request: dict[str, Any],
):
    """
    Send a new university service request to the agent.
    """

    request_text = f"""
Process the following university service request.

REQUEST:

{json.dumps(request, indent=2)}

Process the request using the available MCP tools.
Investigate the request when necessary and take the
appropriate action.
"""

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request_text,
                }
            ]
        }
    )

    return result


# ============================================================
# DISPLAY RESULT
# ============================================================

def print_result(result):

    print("\n")
    print("=" * 70)
    print("AGENT RESULT")
    print("=" * 70)

    messages = result.get(
        "messages",
        []
    )

    if not messages:
        print("No response returned.")
        return

    final_message = messages[-1]

    print(
        final_message.content
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

async def main():

    agent = await create_registrar_agent()

    # --------------------------------------------------------
    # TEST REQUEST
    # --------------------------------------------------------

    request = {
        "request_id": "REQ100",
        "student_name": "Norha Ashwood",
        "student_status": "Active",
        "body_text": (
            "I was charged an incorrect tuition amount "
            "and would like this issue resolved."
        ),
    }

    result = await process_request(
        agent,
        request,
    )

    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
