#!/usr/bin/env python3
"""
Python script to test streaming responses from Travel Assistant API
"""

import requests
import json
import time

API_URL = "http://localhost:8000"


def test_health():
    """Test server health endpoint."""
    print("🏥 Testing server health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy!")
            print(f"   Model: {data.get('model')}")
            print(f"   Tools: {', '.join(data.get('tools', []))}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_non_streaming(query):
    """Test non-streaming response."""
    print("\n" + "=" * 60)
    print("📝 Testing NON-STREAMING request")
    print("=" * 60)
    print(f"Query: {query}\n")

    start_time = time.time()

    try:
        response = requests.post(
            f"{API_URL}/travel-assistant",
            json={"query": query, "stream": False},
            headers={"Content-Type": "application/json"},
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print("-" * 60)
            print(data.get("response", "No response"))
            print("-" * 60)
            print(f"\n⏱️  Duration: {duration:.2f}s")
            print(f"📊 Characters: {len(data.get('response', ''))}")
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_streaming(query):
    """Test streaming response."""
    print("\n" + "=" * 60)
    print("🌊 Testing STREAMING request")
    print("=" * 60)
    print(f"Query: {query}\n")
    print("Response (streaming):")
    print("-" * 60)

    start_time = time.time()
    char_count = 0
    chunk_count = 0

    try:
        response = requests.post(
            f"{API_URL}/travel-assistant",
            json={"query": query, "stream": True},
            headers={"Content-Type": "application/json"},
            stream=True,  # Important: enable streaming
        )

        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            return False

        # Process streaming response
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")

                # SSE format: "data: {json}"
                if decoded.startswith("data: "):
                    data_str = decoded[6:]  # Remove 'data: ' prefix

                    if data_str == "[DONE]":
                        print("\n" + "-" * 60)
                        print("✅ Stream complete!")
                        break

                    try:
                        data = json.loads(data_str)

                        if "content" in data:
                            content = data["content"]
                            print(content, end="", flush=True)
                            char_count += len(content)
                            chunk_count += 1

                        if "error" in data:
                            print(f"\n❌ Error: {data['error']}")
                            return False

                    except json.JSONDecodeError:
                        # Some chunks might not be valid JSON
                        pass

        duration = time.time() - start_time

        print("\n" + "-" * 60)
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Characters: {char_count}")
        print(f"📦 Chunks: {chunk_count}")

        if chunk_count > 0:
            print(f"⚡ Avg chunk size: {char_count // chunk_count} chars")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def compare_streaming_vs_non_streaming(query):
    """Compare streaming vs non-streaming performance."""
    print("\n" + "=" * 60)
    print("⚖️  COMPARING STREAMING vs NON-STREAMING")
    print("=" * 60)

    # Non-streaming
    print("\n1️⃣  Non-Streaming Test:")
    ns_start = time.time()
    try:
        response = requests.post(
            f"{API_URL}/travel-assistant", json={"query": query, "stream": False}
        )
        ns_duration = time.time() - ns_start
        ns_chars = len(response.json().get("response", ""))
        print(f"   ⏱️  Time: {ns_duration:.2f}s")
        print(f"   📊 Chars: {ns_chars}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        ns_duration = 0

    # Streaming
    print("\n2️⃣  Streaming Test:")
    s_start = time.time()
    s_chars = 0
    s_chunks = 0

    try:
        response = requests.post(
            f"{API_URL}/travel-assistant",
            json={"query": query, "stream": True},
            stream=True,
        )

        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            s_chars += len(data["content"])
                            s_chunks += 1
                    except Exception:
                        pass

        s_duration = time.time() - s_start
        print(f"   ⏱️  Time: {s_duration:.2f}s")
        print(f"   📊 Chars: {s_chars}")
        print(f"   📦 Chunks: {s_chunks}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        s_duration = 0

    # Comparison
    if ns_duration > 0 and s_duration > 0:
        print("\n📊 Results:")
        print(f"   Time difference: {abs(ns_duration - s_duration):.2f}s")
        if s_chunks > 0:
            print(
                f"   Streaming benefit: Content delivered in {s_chunks} incremental chunks"
            )
            print(
                f"   User sees first content after: ~{s_duration / s_chunks:.2f}s (estimated)"
            )


def main():
    """Main test runner."""
    print("=" * 60)
    print("🧪 Travel Assistant API - Streaming Test Suite")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        print("\n⚠️  Server is not running. Start it with:")
        print("   python3 server.py")
        return

    # Test queries
    test_queries = [
        "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
        "I want to visit Paris. Can you search for flights from New York and check the weather?",
    ]

    # Test 2: Non-streaming
    test_non_streaming(test_queries[0])

    # Wait a bit
    time.sleep(2)

    # Test 3: Streaming
    test_streaming(test_queries[0])

    # Wait a bit
    time.sleep(2)

    # Test 4: Comparison
    compare_streaming_vs_non_streaming(test_queries[1])

    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)

    print("\n💡 Tips:")
    print("   • Streaming shows content incrementally (better UX)")
    print("   • Non-streaming waits for complete response")
    print("   • Both produce the same final output")
    print("   • Open streaming_test.html in browser for interactive UI")
    print("\n🌐 URLs:")
    print(f"   • API Docs: {API_URL}/docs")
    print(f"   • Health: {API_URL}/health")
    print("   • Test UI: file://./streaming_test.html")


if __name__ == "__main__":
    main()
