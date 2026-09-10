import chromadb

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

COLLECTION_NAME = "lms_knowledge_base"

TOP_K = 5


print()

question = input(
    "Ask a question: "
)

print()

print(
    "Loading embedding model..."
)

model = SentenceTransformer(
    MODEL_NAME
)

question_embedding = model.encode(
    question
).tolist()

print(
    "Connecting to Chroma..."
)

client = chromadb.PersistentClient(
    path="vector_db"
)

collection = client.get_collection(
    COLLECTION_NAME
)

results = collection.query(
    query_embeddings=[
        question_embedding
    ],
    n_results=TOP_K
)

print()

print("=" * 60)
print("TOP RESULTS")
print("=" * 60)

documents = results.get(
    "documents",
    [[]]
)[0]

metadatas = results.get(
    "metadatas",
    [[]]
)[0]

distances = results.get(
    "distances",
    [[]]
)[0]

if not documents:

    print()

    print(
        "❌ No results found."
    )

    exit()

for i in range(
    len(documents)
):

    print()

    print(
        f"RESULT {i + 1}"
    )

    print(
        "-" * 60
    )

    print(
        "Course:",
        metadatas[i].get(
            "course_name",
            ""
        )
    )

    print(
        "Module:",
        metadatas[i].get(
            "module_name",
            ""
        )
    )

    print(
        "Lecture:",
        metadatas[i].get(
            "lecture_title",
            ""
        )
    )

    print(
        "Chunk:",
        metadatas[i].get(
            "chunk_index",
            ""
        )
    )
    
    print(
        "Lecture ID:",
        metadatas[i].get(
            "lecture_id",
            ""
        )
    )

    print(
        "Chunk Words:",
        metadatas[i].get(
            "chunk_word_count",
            ""
        )
    )

    distance = distances[i]

    print(
        "Distance:",
        round(
            distance,
            4
        )
    )

    print()

    preview = documents[i][:400]

    print(
        preview
    )

    if len(
        documents[i]
    ) > 400:

        print(
            "\n...[TRUNCATED]"
        )

    print()

print()

print("=" * 60)
print("📊 QUERY SUMMARY")
print("=" * 60)

best_match = metadatas[0]

best_distance = round(
    distances[0],
    4
)

print(
    "Question:",
    question
)

print(
    "Results Returned:",
    len(documents)
)

print(
    "Best Match Lecture:",
    best_match.get(
        "lecture_title",
        ""
    )
)

print(
    "Best Match ID:",
    best_match.get(
        "lecture_id",
        ""
    )
)

print(
    "Best Distance:",
    best_distance
)

print(
    "Embedding Model:",
    MODEL_NAME
)

print(
    "Top K:",
    TOP_K
)