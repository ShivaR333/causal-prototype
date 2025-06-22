#!/usr/bin/env python3
"""
Test script to verify the agent setup is working correctly.
"""

import os
from causal_agent import CausalAnalysisAgent

def test_setup():
    """Test if the agent can be initialized properly."""
    
    print("🔧 Testing Causal Analysis Agent Setup")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        print("\nPlease set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("   OPENAI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    # Try to initialize the agent
    try:
        print("\n🤖 Initializing agent...")
        agent = CausalAnalysisAgent()
        print(f"✅ Agent initialized successfully!")
        print(f"🔧 Using OpenAI model: {agent.model}")
        
        # Check available resources
        print(f"\n📁 Available DAGs: {len(agent.dag_library)}")
        for path, desc in list(agent.dag_library.items())[:3]:
            print(f"   - {path}: {desc}")
        
        print(f"\n📊 Available Datasets: {len(agent.data_library)}")
        for path, desc in list(agent.data_library.items())[:3]:
            print(f"   - {path}: {desc}")
        
        # Test basic functionality
        print(f"\n🔄 Current state: {agent.get_state_info()}")
        
        print("\n✅ Setup test completed successfully!")
        print("\nYou can now run:")
        print("   python causal_agent.py")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False

if __name__ == "__main__":
    test_setup()