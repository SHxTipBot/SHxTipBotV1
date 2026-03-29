import re

def parse_amount_sync(input_str: str) -> float | None:
    input_str = str(input_str).strip().lower()
    is_usd = input_str.startswith('$') or input_str.endswith('usd')
    clean_str = input_str.replace('$', '').replace('usd', '').replace(',', '').strip()
    try:
        val = float(clean_str)
        if val <= 0: return None
        # Mock USD price for test
        if is_usd: return val / 0.005 # Example price
        return val
    except ValueError:
        return None

def test_parse_multi_each(input_str):
    pattern = r'(<@!?\d+>)\s*[:=]?\s*([\$]?[\d,]+(?:\.\d+)?(?:usd)?)'
    matches = re.findall(pattern, input_str, re.IGNORECASE)
    results = []
    for mention, amt_str in matches:
        uid = int(re.search(r'\d+', mention).group())
        amt = parse_amount_sync(amt_str)
        results.append((uid, amt))
    return results

def test_parse_mentions(input_str):
    user_ids = set(re.findall(r'<@!?(\d+)>', input_str))
    role_ids = set(re.findall(r'<@&(\d+)>', input_str))
    return user_ids, role_ids

# Test Cases
print("--- Test Multi Each ---")
print(f"Input: '<@123> 100, <@456> $2.50'")
print(f"Output: {test_parse_multi_each('<@123> 100, <@456> $2.50')}")

print("\n--- Test Split Mentions ---")
print(f"Input: '<@123> <@!456> <@&789>'")
print(f"Output (Users, Roles): {test_parse_mentions('<@123> <@!456> <@&789>')}")
