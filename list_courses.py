import chromadb

client = chromadb.PersistentClient(path=r"C:\LMS_VectorDB")
collection = client.get_collection("lms_knowledge_base")

results = collection.get(include=["metadatas"])
courses = set(m["course_name"] for m in results["metadatas"])

for c in sorted(courses):
    print(c)
