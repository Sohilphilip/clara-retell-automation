import re


def normalize_transcript(raw_text: str) -> str:
    """
    Cleans raw transcript text automatically.
    Removes timestamps, speaker labels, payment data, and noise.
    """

    text = raw_text

    # 1️⃣ Remove timestamps like: Speaker 1: 00:00
    text = re.sub(r"Speaker\s*\d+:\s*\d+:\d+", "", text)

    # 2️⃣ Remove speaker labels like: Speaker 1:
    text = re.sub(r"Speaker\s*\d+:", "", text)

    # 3️⃣ Remove credit card numbers (xxxx-xxxx-xxxx-xxxx)
    text = re.sub(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", "", text)

    # 4️⃣ Remove CSC or CVV
    text = re.sub(r"CSC\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"CVV\s*\d+", "", text, flags=re.IGNORECASE)

    # 5️⃣ Remove expiration formats like 03/29
    text = re.sub(r"\b\d{2}/\d{2}\b", "", text)

    # 6️⃣ Remove expiration references like "0329 expiration"
    text = re.sub(r"\b\d{4}\b(?=\s*(expiration|exp))", "", text, flags=re.IGNORECASE)

    # 7️⃣ Remove credit card discussion blocks
    text = re.sub(
        r"credit card[\s\S]*?(?=(kickoff|thank you|bye))",
        "",
        text,
        flags=re.IGNORECASE
    )

    # 8️⃣ Remove leftover timestamp fragments like ":25"
    text = re.sub(r"\n\s*:\d+\s*", "\n", text)

    # 9️⃣ Remove excessive blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def main():

    input_file = "dataset/demo_calls/bens_demo.txt"
    output_file = "dataset/demo_calls/bens_demo_clean.txt"

    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned = normalize_transcript(raw_text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("Transcript normalized successfully.")
    print("Clean file saved to:", output_file)


if __name__ == "__main__":
    main()