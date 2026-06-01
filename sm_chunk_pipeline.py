import os
import json
import re
from uuid import uuid4
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


INPUT_FOLDER = "cleaned_output"

OUTPUT_FOLDER = "sm_chunked_output"


SIMILARITY_THRESHOLD = 0.50

MAX_CHUNK_WORDS = 1200

MIN_CHUNK_WORDS = 200


os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


processed_files = 0

total_chunks_created = 0

chunk_sizes = []

small_chunks = []

large_chunks = []


def split_into_sentences(text):

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )

    return [
        s.strip()
        for s in sentences
        if s.strip()
    ]


def semantic_chunking(sentences):

    embeddings = model.encode(
        sentences
    )

    chunks = []

    current_chunk = [sentences[0]]

    current_word_count = len(
        sentences[0].split()
    )

    for i in range(1, len(sentences)):

        previous_embedding = embeddings[i - 1]

        current_embedding = embeddings[i]

        similarity = cosine_similarity(
            [previous_embedding],
            [current_embedding]
        )[0][0]

        sentence_word_count = len(
            sentences[i].split()
        )

        if current_word_count >= MAX_CHUNK_WORDS:

            chunk_text = " ".join(
                current_chunk
            )

            chunks.append(
                chunk_text
            )

            current_chunk = [sentences[i]]

            current_word_count = sentence_word_count

        elif similarity >= SIMILARITY_THRESHOLD:

            current_chunk.append(
                sentences[i]
            )

            current_word_count += sentence_word_count

        else:

            chunk_text = " ".join(
                current_chunk
            )

            chunks.append(
                chunk_text
            )

            current_chunk = [sentences[i]]

            current_word_count = sentence_word_count

    if current_chunk:

        chunks.append(
            " ".join(current_chunk)
        )

    merged_chunks = []

    temp_chunk = ""

    for chunk in chunks:

        word_count = len(
            chunk.split()
        )

        if word_count < MIN_CHUNK_WORDS:

            temp_chunk += " " + chunk

        else:

            if temp_chunk:

                merged_chunks.append(
                    temp_chunk.strip()
                )

                temp_chunk = ""

            merged_chunks.append(chunk)

    if temp_chunk:

        merged_chunks.append(
            temp_chunk.strip()
        )

    return merged_chunks


for root, dirs, files in os.walk(INPUT_FOLDER):

    for file in files:

        if not file.endswith(".json"):
            continue

        file_path = os.path.join(
            root,
            file
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            cleaned_content = data.get(
                "cleaned_content",
                ""
            )

            if not cleaned_content.strip():
                continue

            sentences = split_into_sentences(
                cleaned_content
            )

            if len(sentences) == 0:
                continue

            chunks = semantic_chunking(
                sentences
            )

            relative_path = os.path.relpath(
                root,
                INPUT_FOLDER
            )

            output_folder = os.path.join(
                OUTPUT_FOLDER,
                relative_path
            )

            os.makedirs(
                output_folder,
                exist_ok=True
            )

            lecture_chunks = []

            total_chunks = len(chunks)

            for index, chunk_text in enumerate(chunks):

                chunk_word_count = len(
                    chunk_text.split()
                )

                chunk_sizes.append(
                    chunk_word_count
                )

                if chunk_word_count < 250:

                    small_chunks.append({

                        "lecture_file": file,

                        "chunk_index": index + 1,

                        "chunk_word_count": chunk_word_count
                    })
                    
                if chunk_word_count > 1200:

                    large_chunks.append({

                        "lecture_file": file,

                        "chunk_index": index + 1,

                        "chunk_word_count": chunk_word_count
                    })

                chunk_data = {

                    "chunk_id": str(uuid4()),

                    "chunk_index": index + 1,

                    "total_chunks": total_chunks,

                    "chunk_word_count": chunk_word_count,

                    "chunk_char_count": len(
                        chunk_text
                    ),

                    "chunk_strategy": "semantic",

                    "similarity_threshold": SIMILARITY_THRESHOLD,

                    "max_chunk_words": MAX_CHUNK_WORDS,

                    "min_chunk_words": MIN_CHUNK_WORDS,

                    "course_name": data.get(
                        "course",
                        ""
                    ),

                    "module_name": data.get(
                        "module",
                        ""
                    ),

                    "lecture_title": data.get(
                        "lecture",
                        ""
                    ),

                    "lecture_id": data.get(
                        "lecture_id",
                        ""
                    ),

                    "source_type": data.get(
                        "type",
                        ""
                    ),

                    "generated_at": datetime.now().isoformat(),

                    "chunk_text": chunk_text
                }

                lecture_chunks.append(
                    chunk_data
                )

                total_chunks_created += 1

            output_data = {

                "original_lecture_word_count": len(
                    cleaned_content.split()
                ),

                "lecture_title": data.get(
                    "lecture",
                    ""
                ),

                "total_chunks": total_chunks,

                "chunking_strategy": "semantic",

                "chunks": lecture_chunks
            }

            output_path = os.path.join(
                output_folder,
                file
            )

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    output_data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            processed_files += 1

            print(f"✅ Semantic Chunked: {file}")

        except Exception as e:

            print(f"❌ Failed: {file}")

            print(e)


print("\n========================")
print("🧠 SEMANTIC CHUNK REPORT")
print("========================")

print("📚 Processed Lectures:", processed_files)

print("🧩 Total Chunks Created:", total_chunks_created)

if len(chunk_sizes) > 0:

    print(
        "📏 Largest Chunk:",
        max(chunk_sizes)
    )

    print(
        "📉 Smallest Chunk:",
        min(chunk_sizes)
    )

    print(
        "🧠 Average Chunk Size:",
        sum(chunk_sizes) // len(chunk_sizes)
    )

    range_1_200 = len(
        [x for x in chunk_sizes if 1 <= x <= 200]
    )

    range_201_400 = len(
        [x for x in chunk_sizes if 201 <= x <= 400]
    )

    range_401_600 = len(
        [x for x in chunk_sizes if 401 <= x <= 600]
    )

    range_601_1200 = len(
        [x for x in chunk_sizes if 601 <= x <= 1200]
    )

    range_1200_plus = len(
        [x for x in chunk_sizes if x > 1200]
    )

    print("\n📊 CHUNK SIZE DISTRIBUTION")
    print("========================")

    print("1–200 words:", range_1_200)

    print("201–400 words:", range_201_400)

    print("401–600 words:", range_401_600)

    print("601–1200 words:", range_601_1200)

    print("1200+ words:", range_1200_plus)

print("\n⚠️ SMALL CHUNKS (<250 WORDS)")
print("========================")

if len(small_chunks) == 0:

    print("✅ No suspiciously small chunks")

else:

    for chunk in small_chunks:

        print(
            f"{chunk['lecture_file']} | "
            f"Chunk {chunk['chunk_index']} | "
            f"{chunk['chunk_word_count']} words"
        )

print("\n🚨 LARGE CHUNKS (>1200 WORDS)")
print("========================")

if len(large_chunks) == 0:

    print("✅ No oversized chunks")

else:

    for chunk in large_chunks:

        print(
            f"{chunk['lecture_file']} | "
            f"Chunk {chunk['chunk_index']} | "
            f"{chunk['chunk_word_count']} words"
        )

print("\n📂 Output saved to:")
print(OUTPUT_FOLDER)