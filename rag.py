import time
import chromadb
import ollama

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-base-en-v1.5"

COLLECTION_NAME = "lms_knowledge_base"

TOP_K = 10

MAX_DISTANCE = 0.95

MAX_CONTEXT_CHUNKS = 5

MAX_CHARS_PER_CHUNK = 3000

OLLAMA_MODEL = "qwen2.5:7b"


print()

print("🧠 Loading embedding model...")

embedder = SentenceTransformer(
    MODEL_NAME
)

print("🗄️ Connecting to Chroma...")

client = chromadb.PersistentClient(
    path=r"C:\LMS_VectorDB"
)

collection = client.get_collection(
    COLLECTION_NAME
)

print("✅ RAG Ready")

# ==========================
# Conversation Memory
# ==========================

current_lecture_id = None

current_context = ""

chat_history = []

current_sources = []

def should_use_memory(question, current_context):

    if current_context == "":

        return False

    decision = ollama.chat(

        model=OLLAMA_MODEL,

        messages=[

            {

                "role": "user",

                "content": f"""
You are deciding whether a user's question refers to the previous lecture.

Previous lecture exists.

Question:
{question}

Reply ONLY one word.

YES = follow-up question.

NO = new topic.

Answer:
"""
            }

        ],

        options={

            "temperature": 0

        }

    )

    return decision["message"]["content"].strip().upper() == "YES"

while True:

    print()

    question = input(
        "Ask a question (/bye to quit): "
    )

    if question.lower() == "/bye":

        print(
            "\n👋 Goodbye"
        )

        break

    print()

    start_time = time.time()

    if should_use_memory(

        question,

        current_context

    ):

        print("🧠 Using Cached Lecture")

        context = current_context

        sources = current_sources
        
        best_lecture_id = current_lecture_id

    else:

        question_embedding = embedder.encode(
            question
        ).tolist()

        results = collection.query(

            query_embeddings=[

                question_embedding

            ],

            n_results=TOP_K

        )

        print("\nTop Retrieval Results:\n")

        for i in range(len(results["metadatas"][0])):

            meta = results["metadatas"][0][i]

            print(

                f"{i+1}.",

                meta["lecture_title"],

                "|",

                meta["lecture_id"],

                "| Distance:",

                round(results["distances"][0][i], 4)

            )

        documents = results["documents"][0]

        metadatas = results["metadatas"][0]

        distances = results["distances"][0]

        from collections import defaultdict

        lecture_scores = defaultdict(float)

        lecture_meta = {}

        for meta, dist in zip(

            metadatas,

            distances

        ):

            lecture_scores[

                meta["lecture_id"]

            ] += (2 - dist)

            lecture_meta[

                meta["lecture_id"]

            ] = meta

        best_lecture_id = max(

            lecture_scores,

            key=lecture_scores.get

        )

        print(f"\n📚 Best Lecture: {best_lecture_id}")

        lecture_results = collection.get(

            where={

                "lecture_id":

                best_lecture_id

            }

        )

        lecture_chunks = sorted(

            zip(

                lecture_results["documents"],

                lecture_results["metadatas"]

            ),

            key=lambda x:

            x[1]["chunk_index"]

        )

        context = ""

        sources = []

        for doc, meta in lecture_chunks:

            context += "\n\n" + doc

            sources.append({

                "lecture":
                meta["lecture_title"],

                "lecture_id":
                meta["lecture_id"],

                "chunk":
                meta["chunk_index"],

                "distance":
                "Expanded"

            })
        
        current_context = context

        current_sources = sources
        
        current_lecture_id = best_lecture_id
        
    


    prompt = f"""
    You are an academic tutor answering questions from LMS lecture transcripts.

    Use ONLY the transcript below.

    Instructions:

    - Answer directly.
    - Explain concepts in simple language.
    - If multiple points are mentioned, use bullet points.
    - If the transcript gives a definition, quote it as closely as possible.
    - Do not add facts that are not supported by the transcript.
    - If the transcript partially answers the question, say what is available.
    - Only reply "I could not find the answer in the LMS knowledge base." if the transcript truly contains no relevant information.

    Question:
    {question}

    Transcript:
    {context}

    Answer:
    """


    print("🤖 Generating answer...\n")


    response = ollama.chat(

        model=OLLAMA_MODEL,
        messages=[

            {
                "role": "user",
                "content": prompt
            }
        ],
        keep_alive="30m"
    )


    answer = response["message"]["content"]


    elapsed = round(
        time.time() - start_time,
        2
    )

    context_size = len(
        context
    )

    print("=" * 70)
    print("📚 ANSWER")
    print("=" * 70)

    print()
    print(answer)
    print()


    print("=" * 70)
    print("📖 SOURCES")
    print("=" * 70)

    for i, source in enumerate(sources):

        print()

        print(
            f"{i+1}.",
            source["lecture"]
        )

        print(
            "   Lecture ID:",
            source["lecture_id"]
        )

        print(
            "   Chunk:",
            source["chunk"]
        )

        print(
            "   Distance:",
            source["distance"]
        )


    print()
    print("=" * 70)
    print("📊 RAG ANALYTICS")
    print("=" * 70)

    print(
        "Question:",
        question
    )

    print(
        "Chunks Retrieved:",
        1
    )

    print(
        "Model:",
        OLLAMA_MODEL
    )

    print(
        "Embedding Model:",
        MODEL_NAME
    )

    print(
        "Context Size:",
        context_size,
        "chars"
    )

    print(
        "Response Time:",
        f"{elapsed}s"
    )