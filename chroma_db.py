import os
import json
import shutil
from datetime import datetime

import chromadb


# ========================
# CONFIG
# ========================

EMBEDDINGS_FOLDER = "embeddings"

VECTOR_DB_FOLDER = "vector_db"

COLLECTION_NAME = "lms_knowledge_base"


# ========================
# RESET DATABASE
# ========================

if os.path.exists(VECTOR_DB_FOLDER):

    shutil.rmtree(VECTOR_DB_FOLDER)

    print("♻️ Existing vector_db removed")


# ========================
# CREATE CLIENT
# ========================

client = chromadb.PersistentClient(
    path=VECTOR_DB_FOLDER
)


collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


# ========================
# ANALYTICS
# ========================

chunks_indexed = 0

lectures_indexed = 0

courses = set()

modules = set()

failed_files = []


# ========================
# WALK EMBEDDINGS
# ========================

for root, _, files in os.walk(
    EMBEDDINGS_FOLDER
):

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

            if "chunks" not in data:

                continue

            lectures_indexed += 1

            chunks = data.get(
                "chunks",
                []
            )

            ids = []

            embeddings = []

            documents = []

            metadatas = []

            for chunk in chunks:

                chunk_id = chunk.get(
                    "chunk_id"
                )

                embedding = chunk.get(
                    "embedding"
                )

                chunk_text = chunk.get(
                    "chunk_text",
                    ""
                )

                metadata = {

                    "course_name":
                    str(
                        chunk.get(
                            "course_name",
                            ""
                        )
                    ),

                    "module_name":
                    str(
                        chunk.get(
                            "module_name",
                            ""
                        )
                    ),

                    "lecture_title":
                    str(
                        chunk.get(
                            "lecture_title",
                            ""
                        )
                    ),

                    "lecture_id":
                    str(
                        chunk.get(
                            "lecture_id",
                            ""
                        )
                    ),

                    "chunk_index":
                    int(
                        chunk.get(
                            "chunk_index",
                            0
                        )
                    ),

                    "source_type":
                    str(
                        chunk.get(
                            "source_type",
                            ""
                        )
                    )
                }

                ids.append(
                    chunk_id
                )

                embeddings.append(
                    embedding
                )

                documents.append(
                    chunk_text
                )

                metadatas.append(
                    metadata
                )

                courses.add(
                    metadata[
                        "course_name"
                    ]
                )

                modules.add(
                    metadata[
                        "module_name"
                    ]
                )

                chunks_indexed += 1

            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        except Exception as e:

            failed_files.append({

                "file":
                file_path,

                "error":
                str(e)
            })


# ========================
# REPORT
# ========================

report_data = {

    "lectures_indexed":
    lectures_indexed,

    "chunks_indexed":
    chunks_indexed,

    "courses_found":
    len(courses),

    "modules_found":
    len(modules),

    "collection_name":
    COLLECTION_NAME,

    "embedding_dimension":
    384,

    "failed_files":
    failed_files,

    "generated_at":
    datetime.now().isoformat()
}


report_path = os.path.join(
    VECTOR_DB_FOLDER,
    "chroma_report.json"
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


# ========================
# TERMINAL REPORT
# ========================

print()

print("========================")
print("🗄️ CHROMA REPORT")
print("========================")

print(
    "📚 Lectures Indexed:",
    lectures_indexed
)

print(
    "🧩 Chunks Indexed:",
    chunks_indexed
)

print(
    "📖 Courses:",
    len(courses)
)

print(
    "📦 Modules:",
    len(modules)
)

print(
    "🧠 Collection:",
    COLLECTION_NAME
)

print(
    "❌ Failed Files:",
    len(failed_files)
)

if failed_files:

    print()

    print("FAILED FILE DETAILS")

    for failure in failed_files:

        print(
            failure["file"]
        )

        print(
            failure["error"]
        )

        print("-" * 50)

print()

print(
    "📄 Report saved:"
)

print(
    report_path
)