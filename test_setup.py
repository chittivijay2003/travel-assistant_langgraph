#!/usr/bin/env python3
"""Simple test script for Travel Assistant"""

import sys

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    print("\n1. Testing imports...")
    from langchain.tools import tool

    print("   ✅ langchain.tools")

    from langchain_google_genai import ChatGoogleGenerativeAI

    print("   ✅ langchain_google_genai")

    from langgraph.graph import StateGraph, END

    print("   ✅ langgraph.graph")

    from dotenv import load_dotenv

    print("   ✅ dotenv")

    import os

    load_dotenv()

    print("\n2. Checking API key...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"   ✅ API Key found: {api_key[:20]}...")
    else:
        print("   ❌ API Key not found!")
        sys.exit(1)

    print("\n3. Initializing LLM...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", temperature=0.7, google_api_key=api_key
    )
    print("   ✅ LLM initialized")

    print("\n4. Testing simple query...")
    from langchain_core.messages import HumanMessage

    response = llm.invoke([HumanMessage(content="Say hello in one sentence")])
    print(f"   ✅ Response: {response.content}")

    print("\n✅ All tests passed! The application is ready to run.")
    print("\nTo run the full application:")
    print("   python3 main.py")
    print("\nTo start the API server:")
    print("   uvicorn main:api_app --reload --port 8000")

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nPlease install dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
