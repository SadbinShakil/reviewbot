import anthropic, asyncio
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../.env")
key = os.getenv("ANTHROPIC_API_KEY", "")
print(f"Key starts with: {key[:20]}... length={len(key)}")

async def test():
    client = anthropic.AsyncAnthropic(api_key=key)
    r = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=30,
        messages=[{"role": "user", "content": "Say OK"}]
    )
    print("SUCCESS:", r.content[0].text)

asyncio.run(test())
