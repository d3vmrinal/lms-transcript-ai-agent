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

OLLAMA_MODEL = "qwen2.5:3b"


print()

print("🧠 Loading embedding model...")

embedder = SentenceTransformer(MODEL_NAME)

print("🗄️ Connecting to Chroma...")

client = chromadb.PersistentClient(path=r"C:\LMS_VectorDB")

collection = client.get_collection(COLLECTION_NAME)

print("✅ RAG Ready")

import json

with open("term_mapping.json", "r") as f:

    TERM_MAPPING = json.load(f)

# ==========================
# Conversation Memory
# ==========================

current_lecture_id = None

current_context = ""

chat_history = []

current_sources = []

current_course = None

current_module = None


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
""",
            }
        ],
        options={"temperature": 0},
    )

    return decision["message"]["content"].strip().upper() == "YES"


def build_filter(course, module, term_courses):

    if course and module:

        return {"$and": [{"course_name": course}, {"module_name": module}]}

    elif course:

        return {"course_name": course}

    else:

        return {"course_name": {"$in": term_courses}}


def normalize_term(term):

    normalized = term.strip().casefold()

    for mapped_term in TERM_MAPPING:

        if mapped_term.strip().casefold() == normalized:

            return mapped_term

    return term.strip()


while True:

    print()

    print("Terms:", ", ".join(TERM_MAPPING.keys()))

    term_raw = input("Select Term (mandatory, or /bye to quit): ").strip()

    if term_raw.lower() == "/bye":

        print("\n👋 Goodbye")

        break

    selected_term = normalize_term(term_raw)

    while selected_term not in TERM_MAPPING:

        term_raw = input(
            "Invalid term. Select Term (mandatory, or /bye to quit): "
        ).strip()

        if term_raw.lower() == "/bye":

            print("\n👋 Goodbye")

            exit()

        selected_term = normalize_term(term_raw)

    available_courses = TERM_MAPPING[selected_term]

    print("\nCourses:")

    for i, c in enumerate(available_courses, 1):

        print(f"  {i}. {c}")

    print(f"  0. All courses in {selected_term}")

    course_choice = input("Select course number: ").strip()

    course_input = ""

    if course_choice != "0" and course_choice.isdigit():

        idx = int(course_choice) - 1

        if 0 <= idx < len(available_courses):

            course_input = available_courses[idx]

    module_input = ""

    if course_input:

        modules = sorted(
            set(
                m["module_name"]
                for m in collection.get(
                    where={"course_name": course_input}, include=["metadatas"]
                )["metadatas"]
            )
        )

        print("\nModules:")

        for i, m in enumerate(modules, 1):

            print(f"  {i}. {m}")

        print("  0. All modules")

        mod_choice = input("Select module number: ").strip()

        if mod_choice != "0" and mod_choice.isdigit():

            idx = int(mod_choice) - 1

            if 0 <= idx < len(modules):

                module_input = modules[idx]

    selected_course = course_input if course_input else None

    selected_module = module_input if module_input else None

    print()

    question = input("Ask a question (/bye to quit): ")

    if question.lower() == "/bye":

        print("\n👋 Goodbye")

        break

    print()

    start_time = time.time()

    scope_changed = (
        selected_course != current_course or selected_module != current_module
    )

    if (not scope_changed) and should_use_memory(question, current_context):

        print("🧠 Using Cached Lecture")

        context = current_context

        sources = current_sources

        best_lecture_id = current_lecture_id

    else:

        question_embedding = embedder.encode(question).tolist()

        where_filter = build_filter(selected_course, selected_module, available_courses)

        query_kwargs = {"query_embeddings": [question_embedding], "n_results": TOP_K}

        if where_filter:

            query_kwargs["where"] = where_filter

        results = collection.query(**query_kwargs)

        print("\nTop Retrieval Results:\n")

        for i in range(len(results["metadatas"][0])):

            meta = results["metadatas"][0][i]

            print(
                f"{i+1}.",
                meta["lecture_title"],
                "|",
                meta["lecture_id"],
                "| Distance:",
                round(results["distances"][0][i], 4),
            )

        documents = results["documents"][0]

        metadatas = results["metadatas"][0]

        distances = results["distances"][0]

        from collections import defaultdict

        lecture_scores = defaultdict(float)

        lecture_meta = {}

        for meta, dist in zip(metadatas, distances):

            lecture_scores[meta["lecture_id"]] += 2 - dist

            lecture_meta[meta["lecture_id"]] = meta

        if not lecture_scores:

            print(
                "\n❌ No matching content found for this scope. Try broadening your course/module selection.\n"
            )

            continue

        best_lecture_id = max(lecture_scores, key=lecture_scores.get)

        print(f"\n📚 Best Lecture: {best_lecture_id}")

        lecture_results = collection.get(where={"lecture_id": best_lecture_id})

        lecture_chunks = sorted(
            zip(lecture_results["documents"], lecture_results["metadatas"]),
            key=lambda x: x[1]["chunk_index"],
        )

        context = ""

        sources = []

        for doc, meta in lecture_chunks:

            context += "\n\n" + doc

            sources.append(
                {
                    "lecture": meta["lecture_title"],
                    "lecture_id": meta["lecture_id"],
                    "chunk": meta["chunk_index"],
                    "distance": "Expanded",
                }
            )

        current_context = context

        current_sources = sources

        current_lecture_id = best_lecture_id

        current_course = selected_course

        current_module = selected_module

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
    - If the question asks for a "short", "brief", "small", or "quick" answer, respond in 3-5 sentences maximum, no bullet points.
    - If the question does not request brevity, answer in full detail as instructed above.

    Question:
    {question}

    Transcript:
    {context}

    Answer:
    """

    print("🤖 Generating answer...\n")

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        keep_alive="30m",
    )

    answer = response["message"]["content"]

    elapsed = round(time.time() - start_time, 2)

    context_size = len(context)

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

        print(f"{i+1}.", source["lecture"])

        print("   Lecture ID:", source["lecture_id"])

        print("   Chunk:", source["chunk"])

        print("   Distance:", source["distance"])

    print()
    print("=" * 70)
    print("📊 RAG ANALYTICS")
    print("=" * 70)

    print("Question:", question)

    print("Chunks Retrieved:", 1)

    print("Model:", OLLAMA_MODEL)

    print("Embedding Model:", MODEL_NAME)

    print("Context Size:", context_size, "chars")

    print("Response Time:", f"{elapsed}s")
