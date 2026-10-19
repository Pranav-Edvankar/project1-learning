import sys
import tiktoken

# Ensure UTF-8 output encoding on Windows terminals to display emojis properly
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

def run_experiment():
    # Use cl100k_base encoding (used by GPT-4 and modern chat models)
    encoding_name = "cl100k_base"
    enc = tiktoken.get_encoding(encoding_name)
    
    print("=" * 75)
    print(f" Tiktoken Experiment ({encoding_name})")
    print("=" * 75)
    
    # 5 required categories with specific test cases
    test_cases = [
        # Category 1: Normal words
        ("Normal words", "hello world"),
        ("Normal words (single)", "apple"),
        
        # Category 2: Punctuation
        ("Punctuation", "?!!..."),
        ("Punctuation with words", "Hello, world!"),
        
        # Category 3: Whitespace
        ("Whitespace (leading spaces)", "   test"),
        ("Whitespace (word comparison)", "apple"),
        ("Whitespace (leading space word)", " apple"),
        ("Whitespace (multiple spaces)", "apple    banana"),
        
        # Category 4: Numbers
        ("Numbers (sequence)", "123456"),
        ("Numbers (short)", "42"),
        ("Numbers (long)", "1234567890"),
        
        # Category 5: Emojis
        ("Emojis (pair)", "🔥🚀"),
        ("Emojis (single)", "🔥"),
    ]
    
    header = f"{'Category':<32} | {'Input':<20} | {'Tokens':<6} | {'Token IDs'}"
    print(header)
    print("-" * 75)
    
    for category, text in test_cases:
        tokens = enc.encode(text)
        print(f"{category:<32} | {repr(text):<20} | {len(tokens):<6} | {tokens}")
        
    print("-" * 75)
    print("\n" + "=" * 75)
    print(" Detailed Sub-Word / Byte Breakdown")
    print("=" * 75)
    
    # Show how tokens break down into subwords/bytes
    for category, text in test_cases:
        tokens = enc.encode(text)
        # Decode individual token bytes for inspection
        token_pieces = [enc.decode_single_token_bytes(t) for t in tokens]
        print(f"\n[{category}] Input: {repr(text)}")
        print(f"  Count: {len(tokens)} token(s)")
        print(f"  IDs:   {tokens}")
        print(f"  Bytes: {token_pieces}")
        try:
            decoded_strs = [enc.decode([t]) for t in tokens]
            print(f"  Text chunks: {decoded_strs}")
        except Exception:
            pass

if __name__ == "__main__":
    run_experiment()
