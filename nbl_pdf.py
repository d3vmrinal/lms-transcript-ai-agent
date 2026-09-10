import os
import json

from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    PageBreak,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

# Initialize default styles for reportlab
styles = getSampleStyleSheet()


INPUT_FOLDER = "cleaned_output"

OUTPUT_FOLDER = "notebooklm_pdfs"

MAX_WORDS_PER_PDF = 30000

import re


def lecture_sort_key(lecture_id):

    if "__" not in lecture_id:

        return [9999]

    lecture_part = lecture_id.split("__")[1]

    numbers = re.findall(
        r"\d+",
        lecture_part
    )

    return [

        int(x)

        for x in numbers
    ]

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


def choose_course():

    courses = sorted([

        d for d in os.listdir(INPUT_FOLDER)

        if os.path.isdir(
            os.path.join(
                INPUT_FOLDER,
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
        INPUT_FOLDER,
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


print()

print("1. Generate Single Module")

print("2. Generate Entire Course")

mode = input(
    "\nSelect option: "
)

course = choose_course()

if mode == "1":

    modules_to_process = [

        choose_module(course)
    ]

else:

    course_path = os.path.join(
        INPUT_FOLDER,
        course
    )

    modules_to_process = sorted([

        d

        for d in os.listdir(
            course_path
        )

        if os.path.isdir(
            os.path.join(
                course_path,
                d
            )
        )
    ])


course_output = os.path.join(
    OUTPUT_FOLDER,
    course
)

os.makedirs(
    course_output,
    exist_ok=True
)

grand_total_words = 0

grand_total_pdfs = 0

grand_total_lectures = 0


for module in modules_to_process:

    print(
        f"\n📦 Processing {module}"
    )

    module_path = os.path.join(
        INPUT_FOLDER,
        course,
        module
    )

    files = [

        f

        for f in os.listdir(
            module_path
        )

        if f.endswith(".json")
    ]

    lectures = []

    for file in files:

        file_path = os.path.join(
            module_path,
            file
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            content = data.get(
                "cleaned_content",
                ""
            )

            if not content.strip():

                continue

            lectures.append({

                "lecture": data.get(
                    "lecture",
                    ""
                ),

                "sublecture": data.get(
                    "sublecture"
                ),

                "lecture_id": data.get(
                    "lecture_id",
                    ""
                ),

                "content": content,

                "word_count": len(
                    content.split()
                )
            })

        except Exception as e:

            print(
                f"❌ Failed: {file}"
            )

            print(e)

    lectures.sort(

        key=lambda x:

        lecture_sort_key(
            x["lecture_id"]
        )
    )

    pdf_parts = []

    current_part = []

    current_words = 0

    for lecture in lectures:

        words = lecture[
            "word_count"
        ]

        if (

            current_words + words

            > MAX_WORDS_PER_PDF

            and

            len(current_part) > 0

        ):

            pdf_parts.append(
                current_part
            )

            current_part = []

            current_words = 0

        current_part.append(
            lecture
        )

        current_words += words

    if len(current_part) > 0:

        pdf_parts.append(
            current_part
        )

    module_output = os.path.join(
        course_output,
        module
    )

    os.makedirs(
        module_output,
        exist_ok=True
    )

    for part_index, part in enumerate(pdf_parts):

        pdf_name = (
            f"Part_{part_index+1}.pdf"
        )

        pdf_path = os.path.join(
            module_output,
            pdf_name
        )

        doc = SimpleDocTemplate(
            pdf_path
        )

        story = []

        story.append(

            Paragraph(
                f"Course: {course}",
                styles["Title"]
            )
        )

        story.append(

            Paragraph(
                f"Module: {module}",
                styles["Heading2"]
            )
        )

        story.append(

            Paragraph(
                f"Generated At: {datetime.now()}",
                styles["Normal"]
            )
        )

        story.append(
            Spacer(
                1,
                20
            )
        )

        story.append(

            Paragraph(
                "TABLE OF CONTENTS",
                styles["Heading1"]
            )
        )

        seen_lectures = set()

        for lec in part:

            lecture_name = lec["lecture"]

            if lecture_name not in seen_lectures:

                seen_lectures.add(
                    lecture_name
                )

                story.append(

                    Paragraph(
                        lecture_name,
                        styles["Heading3"]
                    )
                )

            sublecture = lec.get(
                "sublecture"
            )

            if sublecture:

                story.append(

                    Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;• {sublecture}",
                        styles["Normal"]
                    )
                )

        story.append(
            PageBreak()
        )

        current_parent = None

        for lecture in part:

            if lecture["lecture"] != current_parent:

                current_parent = lecture["lecture"]

                story.append(

                    Paragraph(
                        lecture["lecture"],
                        styles["Heading1"]
                    )
                )

                story.append(
                    Spacer(1, 10)
                )

            sublecture_title = lecture.get(
                "sublecture"
            )

            if sublecture_title:

                story.append(

                    Paragraph(
                        sublecture_title,
                        styles["Heading2"]
                    )
                )

            else:

                story.append(

                    Paragraph(
                        lecture["lecture"],
                        styles["Heading2"]
                    )
                )
            
            story.append(

                Paragraph(
                    f"Lecture ID: {lecture['lecture_id']}",
                    styles["Normal"]
                )
            )

            story.append(

                Paragraph(
                    f"Words: {lecture['word_count']}",
                    styles["Normal"]
                )
            )

            story.append(
                Spacer(
                    1,
                    10
                )
            )

            story.append(

                Paragraph(
                    lecture["content"],
                    styles["BodyText"]
                )
            )

            story.append(
                Spacer(1, 20)
            )

        doc.build(
            story
        )

        grand_total_pdfs += 1

        print(
            f"✅ {module} -> {pdf_name}"
        )

    grand_total_words += sum(

        x["word_count"]

        for x in lectures
    )

    grand_total_lectures += len(
        lectures
    )

print("\n========================")
print("📚 NOTEBOOKLM PDF REPORT")
print("========================")

print(
    "Course:",
    course
)

print(
    "Modules Processed:",
    len(modules_to_process)
)

print(
    "Lectures Processed:",
    grand_total_lectures
)

print(
    "PDFs Created:",
    grand_total_pdfs
)

print(
    "Total Words:",
    grand_total_words
)

print("\n📂 Output Folder:")

print(course_output)