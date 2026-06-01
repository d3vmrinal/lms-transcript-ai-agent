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

documents = results["documents"][0]

metadatas = results["metadatas"][0]

distances = results["distances"][0]

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
        "Distance:",
        round(
            distances[i],
            4
        )
    )

    print()

    print(
        documents[i][:1000]
    )

    print()