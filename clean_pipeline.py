import os
import json
import re
from datetime import datetime

RAW_OUTPUT_FOLDER = "output"

CLEANED_OUTPUT_FOLDER = "cleaned_output"

os.makedirs(CLEANED_OUTPUT_FOLDER, exist_ok=True)

processed_files = 0
skipped_files = 0
empty_files = 0

forced_transcript_files = []

content_lengths = []


def clean_text(text):

    if not text:
        return ""

    text = text.replace("\u00a0", " ")

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"\n+", "\n", text)

    text = text.strip()

    return text


for root, dirs, files in os.walk(RAW_OUTPUT_FOLDER):

    for file in files:

        if not file.endswith(".json"):
            continue

        raw_path = os.path.join(root, file)

        try:

            with open(raw_path, "r", encoding="utf-8") as f:

                data = json.load(f)

            content = data.get("content", "")

            vectorizable = data.get("vectorizable", False)

            has_transcript = data.get("has_transcript", False)

            if has_transcript and not vectorizable:

                forced_transcript_files.append(
                    {
                        "course": data.get("course", "Unknown"),
                        "module": data.get("module", "Unknown"),
                        "lecture": data.get("lecture", file)
                    }
                )

            if not vectorizable and not has_transcript:

                skipped_files += 1
                continue

            cleaned_content = clean_text(content)

            if len(cleaned_content.strip()) == 0:

                empty_files += 1
                continue

            data["cleaned_content"] = cleaned_content

            data["cleaned_at"] = datetime.now().isoformat()

            data["cleaned_content_length"] = len(cleaned_content)

            content_lengths.append(len(cleaned_content))

            relative_path = os.path.relpath(root, RAW_OUTPUT_FOLDER)

            cleaned_folder = os.path.join(
                CLEANED_OUTPUT_FOLDER,
                relative_path
            )

            os.makedirs(cleaned_folder, exist_ok=True)

            cleaned_path = os.path.join(
                cleaned_folder,
                file
            )

            with open(
                cleaned_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            processed_files += 1

            print(f"✅ Cleaned: {file}")

        except Exception as e:

            print(f"❌ Failed: {file}")
            print(e)


print("\n========================")
print("🧹 CLEANING REPORT")
print("========================")

print("✅ Processed Files:", processed_files)

print("⏭️ Skipped Non-Vectorizable:", skipped_files)

print(
    "🚨 Transcript Found But Marked Non-Vectorizable:",
    len(forced_transcript_files)
)

print("⚠️ Empty Cleaned Files:", empty_files)

if len(content_lengths) > 0:

    print(
        "🧠 Average Cleaned Length:",
        sum(content_lengths) // len(content_lengths)
    )

    print(
        "📏 Largest Cleaned File:",
        max(content_lengths)
    )

    print(
        "📉 Smallest Cleaned File:",
        min(content_lengths)
    )

if forced_transcript_files:

    print("\n🚨 Transcript Override Files:")

    for item in forced_transcript_files:

        print(
            f"   • {item['course']} "
            f"→ {item['module']} "
            f"→ {item['lecture']}"
        )

print("\n📂 Cleaned output saved to:")
print(CLEANED_OUTPUT_FOLDER)