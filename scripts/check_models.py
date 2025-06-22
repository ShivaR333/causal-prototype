#!/usr/bin/env python3
"""
Check which OpenAI models are available with your API key.
"""

import os
from openai import OpenAI

def check_available_models():
    """Check which OpenAI models are available."""
    
    print("🔍 Checking Available OpenAI Models")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        print("Please set your API key first.")
        return
    
    print(f"✅ Using API key: {api_key[:10]}...")
    
    client = OpenAI(api_key=api_key)
    
    # List of models to test
    models_to_test = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125", 
        "gpt-4",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4-1106-preview"
    ]
    
    available_models = []
    
    print("\n🧪 Testing models...")
    
    for model in models_to_test:
        try:
            print(f"   Testing {model}...", end=" ")
            
            # Make a minimal test request
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            
            print("✅ Available")
            available_models.append(model)
            
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "model_not_found" in error_msg:
                print("❌ Not available")
            elif "insufficient_quota" in error_msg:
                print("⚠️  Available but quota exceeded")
                available_models.append(model)
            else:
                print(f"❌ Error: {error_msg}")
    
    print(f"\n📊 Summary:")
    print(f"Available models: {len(available_models)}")
    
    if available_models:
        print("\n✅ You can use these models:")
        for model in available_models:
            print(f"   - {model}")
        
        recommended = available_models[0]
        print(f"\n💡 Recommended model for the agent: {recommended}")
        
        # Show how to use specific model
        print(f"\n🔧 To use a specific model:")
        print(f"   agent = CausalAnalysisAgent(model='{recommended}')")
    else:
        print("\n❌ No models available. Please check:")
        print("   1. Your API key is correct")
        print("   2. Your OpenAI account has credits")
        print("   3. Your account has access to chat models")

if __name__ == "__main__":
    check_available_models()