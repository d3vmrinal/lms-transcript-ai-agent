import json

term_mapping = {
    "Term 1": ["", "Course B", "Course C"],
    "Term 2": ["Course D", "Course E", "Course F"],
    "Term 3": ["Course G", "Course H", "Course I"],
    "Term 4": [
        "Digital Marketing Strategy",
        "Operations Management",
        "New Product Development",
        "Sustainability Measures for SMEs",
        "People, Work and Organisations",
        "Exploring Society & Social Structure",
        "Introduction to Strategic Management",
    ],
    "Term 5": ["Entrepreneurial Hypothesis Testing", "Course N", "Course O"],
    "Term 6": ["Course P", "Course Q", "Course R"],
}

with open("term_mapping.json", "w") as f:
    json.dump(term_mapping, f, indent=2)
