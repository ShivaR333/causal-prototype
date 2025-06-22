#!/usr/bin/env python3
"""
Example usage of the Causal Analysis Agent

This script demonstrates how to use the agent programmatically instead of the interactive mode.
"""

import os
from causal_agent import CausalAnalysisAgent

def main():
    """Example usage of the causal analysis agent."""
    
    # Set up OpenAI API key (you need to set this environment variable)
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set the OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize the agent
    print("🤖 Initializing Causal Analysis Agent...")
    agent = CausalAnalysisAgent()
    
    # Example workflow
    print("\n" + "="*60)
    print("EXAMPLE WORKFLOW")
    print("="*60)
    
    # Step 1: Initial question
    print("\n1️⃣ User Question:")
    question = "I want to analyze the effect of treatment on patient outcomes in a healthcare setting"
    print(f"   '{question}'")
    
    print("\n🤖 Agent Response:")
    response1 = agent.process_user_question(question)
    print(response1)
    
    # Step 2: Confirm the proposal
    print("\n2️⃣ User Confirmation:")
    confirmation = "yes, proceed with this setup"
    print(f"   '{confirmation}'")
    
    print("\n🤖 Agent Response:")
    response2 = agent.process_user_question(confirmation)
    print(response2)
    
    # Step 3: Confirm analysis plan
    print("\n3️⃣ User Approval:")
    approval = "proceed with the causal analysis"
    print(f"   '{approval}'")
    
    print("\n🤖 Agent Response:")
    response3 = agent.process_user_question(approval)
    print(response3)
    
    # Step 4: Follow-up question
    print("\n4️⃣ Follow-up Question:")
    followup = "What are the key assumptions of this analysis?"
    print(f"   '{followup}'")
    
    print("\n🤖 Agent Response:")
    response4 = agent.process_user_question(followup)
    print(response4)
    
    # Show final state
    print("\n" + "="*60)
    print("FINAL STATE")
    print("="*60)
    state_info = agent.get_state_info()
    for key, value in state_info.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()