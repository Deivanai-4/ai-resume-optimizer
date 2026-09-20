"""
Qwen Connectivity Test
Run: python test_qwen.py
Expected output: QWEN_CONNECTION_SUCCESS
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HF_TOKEN")
provider = os.getenv("HF_PROVIDER", "hf-inference")
model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

if not token:
    print("[ERROR] HF_TOKEN is missing from .env")
    sys.exit(1)

print(f"[INFO] Testing model: {model}")
print(f"[INFO] Provider:      {provider}")
print(f"[INFO] Token starts:  {token[:8]}...")

try:
    from huggingface_hub import InferenceClient

    # Explicitly pass provider= to avoid auto-router (which requires HF token detection)
    client = InferenceClient(
        token=token,
        provider=provider,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Respond with exactly: QWEN_CONNECTION_SUCCESS",
            }
        ],
        max_tokens=30,
    )

    reply = response.choices[0].message.content.strip()
    print(f"\n[RESPONSE] {reply}\n")

    if "QWEN_CONNECTION_SUCCESS" in reply:
        print("[OK] Qwen connection test PASSED")
    else:
        print("[WARN] Qwen responded but not with expected string -- model is working")

except Exception as e:
    print(f"\n[FAIL] Connection failed: {e}")
    sys.exit(1)