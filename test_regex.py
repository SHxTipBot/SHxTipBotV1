import re

def test_regex():
    pattern = r'(<@!?\d+>)\s*[:=]?\s*([\$]?(?:[\d,]*\.)?[\d,]+(?:usd)?)'
    
    test_cases = [
        ("<@123> 100", [('<@123>', '100')]),
        ("<@!456> $0.15", [('<@!456>', '$0.15')]),
        ("<@789> $.15", [('<@789>', '$.15')]),
        ("<@101> .50usd", [('<@101>', '.50usd')]),
        ("<@202> 1,000.50", [('<@202>', '1,000.50')]),
        ("<@303> $10,000", [('<@303>', '$10,000')]),
        ("<@404> .1", [('<@404>', '.1')]),
        ("<@505> 0.15", [('<@505>', '0.15')]),
        ("<@606> 10.", [('<@606>', '10')]), # Matches the 10, ignores the trailing dot
    ]
    
    for input_str, expected in test_cases:
        matches = re.findall(pattern, input_str, re.IGNORECASE)
        print(f"Input: {input_str} -> Matches: {matches}")
        assert matches == expected or (not matches and not expected), f"Failed for {input_str}: Got {matches}, expected {expected}"

if __name__ == "__main__":
    try:
        test_regex()
        print("\nAll regex test cases passed!")
    except AssertionError as e:
        print(f"\nRegex test failed: {e}")
