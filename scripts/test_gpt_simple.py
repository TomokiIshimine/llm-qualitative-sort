"""Simple test to verify OpenAI API connectivity."""

import asyncio
import os
import aiohttp


async def test_openai_connection():
    """Test basic connectivity to OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return

    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")

    # Get proxy from environment
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    print(f"Using proxy: {proxy[:50]}..." if proxy else "No proxy")

    # Test simple completion
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello in 3 words"}],
        "temperature": 0
    }

    print(f"\nTesting connection to: {url}")
    print("Payload:", data)

    try:
        # Try with proxy
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=data,
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                print(f"\nStatus: {response.status}")
                print(f"Response: {result}")

                if response.status == 200:
                    content = result["choices"][0]["message"]["content"]
                    print(f"\nSuccess! Model says: {content}")
                else:
                    print(f"\nError from API: {result}")
    except aiohttp.ClientError as e:
        print(f"\nConnection error: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_openai_connection())
