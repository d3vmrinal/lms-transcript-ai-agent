import os
import json

import subprocess


MODULE_REPORTS = "module_reports"
OUTPUT_FOLDER = "output"

refresh = input(
    "\nRefresh module tree first? (y/n): "
).lower()

if refresh == "y":

    print(
        "\n🔄 Refreshing module tree...\n"
    )

    subprocess.run(
        ["py", "module_tree.py"]
    )

def choose_course():
    
    courses = sorted([

        d for d in os.listdir(MODULE_REPORTS)

        if os.path.isdir(
            os.path.join(
                MODULE_REPORTS,
                d
            )
        )
    ])

    print("\nAvailable Courses:\n")

    for i, course in enumerate(courses):

        print(
            f"{i + 1}. {course}"
        )

    choice = int(
        input(
            "\nSelect course: "
        )
    )

    return courses[
        choice - 1
    ]


def choose_module(course):

    course_path = os.path.join(
        MODULE_REPORTS,
        course
    )

    modules = sorted([

        d for d in os.listdir(course_path)

        if os.path.isdir(
            os.path.join(
                course_path,
                d
            )
        )
    ])

    print("\nAvailable Modules:\n")

    for i, module in enumerate(modules):

        print(
            f"{i + 1}. {module}"
        )

    choice = int(
        input(
            "\nSelect module: "
        )
    )

    return modules[
        choice - 1
    ]


course = choose_course()

output_course = None

course_keyword = course.split("_")[0]

for folder in os.listdir(OUTPUT_FOLDER):

    if folder.startswith(course_keyword):

        output_course = folder
        break

if output_course is None:

    output_course = course

module = choose_module(course)


tree_path = os.path.join(
    MODULE_REPORTS,
    course,
    module,
    "module_tree.json"
)

with open(
    tree_path,
    "r",
    encoding="utf-8"
) as f:

    tree_data = json.load(f)


lectures = sorted(

    tree_data["lectures"],

    key=lambda x: x.get(
        "lecture_id",
        ""
    )

)


expected_ids = {}

actual_ids = set()

video_without_transcript = []

non_vectorizable = []

actually_missing = []

extracted = []


for lecture in lectures:

    lecture_id = lecture.get(
        "lecture_id",
        ""
    )

    expected_ids[
        lecture_id
    ] = lecture

print("\nMATCHED OUTPUT COURSE:")
print(output_course)

output_module_path = os.path.join(
    OUTPUT_FOLDER,
    output_course,
    module
)

print(output_module_path)

if os.path.exists(
    output_module_path
):

    for file in os.listdir(
        output_module_path
    ):

        if not file.endswith(".json"):
            continue

        file_path = os.path.join(
            output_module_path,
            file
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            lecture_id = data.get(
                "lecture_id",
                ""
            )

            if lecture_id:

                actual_ids.add(
                    lecture_id
                )

        except:

            pass


for lecture_id, lecture in expected_ids.items():

    lecture_type = lecture.get(
        "type",
        ""
    )

    has_transcript = lecture.get(
        "has_transcript",
        False
    )

    if lecture_id in actual_ids:

        extracted.append(
            lecture
        )

        continue

    if (
        lecture_type == "VIDEO"
        and not has_transcript
    ):

        video_without_transcript.append(
            lecture
        )

        continue

    if lecture_type in [

        "QUIZ",

        "HANDOUT",

        "FORUM",

        "ACTIVITY"

    ]:

        non_vectorizable.append(
            lecture
        )

        continue

    actually_missing.append(
        lecture
    )


current_parent = None


for lecture in lectures:

    parent = lecture.get(
        "lecture",
        ""
    )

    child = lecture.get(
        "sublecture"
    )

    if not child:

        child = lecture.get(
            "lecture",
            ""
        )

    status = lecture.get(
        "status",
        ""
    )

    transcript = lecture.get(
        "has_transcript",
        False
    )

    if parent != current_parent:

        current_parent = parent

        print(
            f"\n📘 {parent}"
        )

    lecture_id = lecture.get(
        "lecture_id",
        ""
    )

    if lecture_id in actual_ids:

        icon = "✅"

    elif (
        lecture.get(
            "type"
        ) == "VIDEO"
        and
        not lecture.get(
            "has_transcript",
            False
        )
    ):

        icon = "📹"

    elif lecture.get(
        "type"
    ) in [

        "QUIZ",

        "HANDOUT",

        "FORUM",

        "ACTIVITY"

    ]:

        icon = "🟡"

    else:

        icon = "❌"

    print(
        f"   └── {icon} {child}"
    )

    print(
        f"       Transcript: {transcript}"
    )


print("\n========================")
print("📊 KNOWLEDGE BASE STATUS")
print("========================")

print(
    "Expected Units:",
    len(expected_ids)
)

print(
    "✅ Extracted:",
    len(extracted)
)

print(
    "📹 Videos Without Transcript:",
    len(video_without_transcript)
)

print(
    "🟡 Non Vectorizable:",
    len(non_vectorizable)
)

print(
    "❌ Actually Missing:",
    len(actually_missing)
)


print("\n========================")
print("📹 VIDEOS WITHOUT TRANSCRIPT")
print("========================")

if len(
    video_without_transcript
) == 0:

    print(
        "✅ None"
    )

else:

    for lecture in video_without_transcript:

        print(
            lecture.get(
                "sublecture"
            )
            or
            lecture.get(
                "lecture"
            )
        )


print("\n========================")
print("❌ ACTUALLY MISSING")
print("========================")

if len(
    actually_missing
) == 0:

    print(
        "✅ None"
    )

else:

    for lecture in actually_missing:

        print(
            lecture.get(
                "sublecture"
            )
            or
            lecture.get(
                "lecture"
            )
        )


print("\n========================")
print("🚀 RECOMMENDATION")
print("========================")

if len(
    actually_missing
) == 0:

    print(
        "✅ No rerun needed."
    )

    print(
        "All expected lecture units exist in output."
    )

else:

    print(
        f"⚠️ {len(actually_missing)} lecture(s) missing."
    )

    print(
        "Run lms_bot.py again."
    )