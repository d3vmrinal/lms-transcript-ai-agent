import os
import json
from datetime import datetime

from sentence_transformers import SentenceTransformer


INPUT_FOLDER = "st_chunked_output"

OUTPUT_FOLDER = "embeddings"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


print("🧠 Loading embedding model...")

model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("✅ Model Loaded")


processed_files = 0

processed_chunks = 0

failed_files = []

chunk_sizes = []

small_chunks = []

large_chunks = []

range_1_200 = 0
range_201_400 = 0
range_401_600 = 0
range_601_800 = 0
range_801_1000 = 0
range_1001_plus = 0


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

            chunks = data.get(
                "chunks",
                []
            )

            if len(chunks) == 0:
                continue

            embedded_chunks = []

            for chunk in chunks:

                chunk_text = chunk.get(
                    "chunk_text",
                    ""
                )

                if not chunk_text.strip():
                    continue

                embedding = model.encode(
                    chunk_text
                ).tolist()

                word_count = chunk.get(
                    "chunk_word_count",
                    0
                )

                chunk_sizes.append(
                    word_count
                )

                if word_count <= 200:
                    range_1_200 += 1

                elif word_count <= 400:
                    range_201_400 += 1

                elif word_count <= 600:
                    range_401_600 += 1

                elif word_count <= 800:
                    range_601_800 += 1

                elif word_count <= 1000:
                    range_801_1000 += 1

                else:
                    range_1001_plus += 1


                if word_count < 250:

                    small_chunks.append({

                        "lecture_id":
                        chunk.get(
                            "lecture_id",
                            ""
                        ),

                        "chunk_id":
                        chunk.get(
                            "chunk_id",
                            ""
                        ),

                        "word_count":
                        word_count
                    })


                if word_count > 1000:

                    large_chunks.append({

                        "lecture_id":
                        chunk.get(
                            "lecture_id",
                            ""
                        ),

                        "chunk_id":
                        chunk.get(
                            "chunk_id",
                            ""
                        ),

                        "word_count":
                        word_count
                    })

                embedded_chunk = {

                    **chunk,

                    "embedding_model":
                    EMBEDDING_MODEL,

                    "embedding_dimension":
                    len(embedding),

                    "embedding_created_at":
                    datetime.now().isoformat(),

                    "embedding":
                    embedding
                }

                embedded_chunks.append(
                    embedded_chunk
                )

                processed_chunks += 1

            output_data = {

                "lecture_title":
                chunks[0].get(
                    "lecture_title",
                    ""
                ),

                "lecture_id":
                chunks[0].get(
                    "lecture_id",
                    ""
                ),

                "total_chunks":
                len(embedded_chunks),

                "embedding_model":
                EMBEDDING_MODEL,

                "embedding_dimension":
                384,

                "embedded_at":
                datetime.now().isoformat(),

                "chunks":
                embedded_chunks
            }

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

            print(
                f"✅ Embedded: {file}"
            )

        except Exception as e:

            failed_files.append(
                file
            )

            print(
                f"❌ Failed: {file}"
            )

            print(e)


print("\n========================")
print("🧠 EMBEDDING REPORT")
print("========================")

print(
    "📚 Processed Lectures:",
    processed_files
)

print(
    "🧩 Embedded Chunks:",
    processed_chunks
)

if chunk_sizes:

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

print(
    "❌ Failed Files:",
    len(failed_files)
)

report_data = {

    "lectures_processed":
    processed_files,

    "chunks_embedded":
    processed_chunks,

    "embedding_model":
    EMBEDDING_MODEL,

    "embedding_dimension":
    384,

    "largest_chunk_words":
    max(chunk_sizes) if chunk_sizes else 0,

    "smallest_chunk_words":
    min(chunk_sizes) if chunk_sizes else 0,

    "average_chunk_words":
    (
        sum(chunk_sizes) // len(chunk_sizes)
        if chunk_sizes
        else 0
    ),

    "chunks_below_250":
    len(small_chunks),

    "chunks_above_1000":
    len(large_chunks),

    "distribution_1_200":
    range_1_200,

    "distribution_201_400":
    range_201_400,

    "distribution_401_600":
    range_401_600,

    "distribution_601_800":
    range_601_800,

    "distribution_801_1000":
    range_801_1000,

    "distribution_1001_plus":
    range_1001_plus,

    "small_chunks":
    small_chunks,

    "large_chunks":
    large_chunks,

    "failed_files":
    failed_files,

    "generated_at":
    datetime.now().isoformat()
}

report_path = os.path.join(
    OUTPUT_FOLDER,
    "embedding_report.json"
)

with open(
    report_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report_data,
        f,
        indent=4
    )

print(
    "\n📊 Embedding report saved:"
)

print(
    report_path
)

print(
    "\n📂 Output Folder:"
)

print(
    OUTPUT_FOLDER
)