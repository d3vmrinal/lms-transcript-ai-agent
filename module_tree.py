import os
import json

RAW_OUTPUT_FOLDER = "output"
REPORT_FOLDER = "module_reports"

os.makedirs(REPORT_FOLDER, exist_ok=True)

modules = {}

for root, dirs, files in os.walk(RAW_OUTPUT_FOLDER):

    for file in files:

        if not file.endswith(".json"):
            continue

        file_path = os.path.join(root, file)

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            course = data.get(
                "course",
                "Unknown Course"
            )

            module = data.get(
                "module",
                "Unknown Module"
            )

            key = (course, module)

            if key not in modules:

                modules[key] = {
                    "course": course,
                    "module": module,
                    "lectures": []
                }

            modules[key]["lectures"].append({

                "lecture": data.get("lecture"),

                "sublecture": data.get(
                    "sublecture"
                ),

                "lecture_id": data.get(
                    "lecture_id"
                ),

                "type": data.get(
                    "type"
                ),

                "status": data.get(
                    "status"
                ),

                "vectorizable": data.get(
                    "vectorizable"
                ),

                "has_transcript": data.get(
                    "has_transcript"
                ),

                "content_length": data.get(
                    "content_length"
                )
            })

        except Exception as e:

            print(
                f"❌ Failed to read: {file}"
            )

            print(e)

# ==================================
# BUILD REPORTS
# ==================================

for (course, module), module_data in modules.items():

    lectures = module_data["lectures"]

    total_files = len(lectures)

    video_count = 0
    video_with_transcript = 0
    video_without_transcript = 0

    vectorizable_count = 0

    transcript_override_files = []

    non_lecture_files = []

    for lec in lectures:

        if lec["vectorizable"]:

            vectorizable_count += 1

        if lec["type"] == "VIDEO":

            video_count += 1

            if lec["has_transcript"]:

                video_with_transcript += 1

            else:

                video_without_transcript += 1

                non_lecture_files.append({

                    "lecture": lec["lecture"],

                    "sublecture": lec["sublecture"]
                })

        if (
            lec["has_transcript"]
            and not lec["vectorizable"]
        ):

            transcript_override_files.append({

                "lecture": lec["lecture"],

                "sublecture": lec["sublecture"]
            })

    report = {

        "course": course,

        "module": module,

        "total_files": total_files,

        "video_count": video_count,

        "video_with_transcript":
            video_with_transcript,

        "video_without_transcript":
            video_without_transcript,

        "vectorizable_count":
            vectorizable_count,

        "transcript_override_count":
            len(
                transcript_override_files
            ),

        "non_lecture_count":
            len(
                non_lecture_files
            ),

        "transcript_override_files":
            transcript_override_files,

        "non_lecture_files":
            non_lecture_files
    }

    safe_course = (
        course
        .replace(" ", "_")
        .replace("&", "and")
    )

    safe_module = (
        module
        .replace(" ", "_")
        .replace(":", "")
        .replace("|", "")
        .replace("&", "and")
    )

    output_folder = os.path.join(
        REPORT_FOLDER,
        safe_course,
        safe_module
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    tree_path = os.path.join(
        output_folder,
        "module_tree.json"
    )

    report_path = os.path.join(
        output_folder,
        "module_report.json"
    )

    with open(
        tree_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            module_data,
            f,
            indent=4,
            ensure_ascii=False
        )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"✅ Report Generated: "
        f"{course} -> {module}"
    )

print("\n========================")
print("🌳 MODULE TREE COMPLETE")
print("========================")

print(
    "📂 Reports saved to:"
)

print(REPORT_FOLDER)