from playwright.sync_api import sync_playwright
import json
import os

BASE_DIR = "output"
os.makedirs(BASE_DIR, exist_ok=True)


# =============================
# 🔧 UTIL FUNCTIONS
# =============================


def clean_name(text):
    return (
        "".join(c for c in text if c.isalnum() or c in (" ", "_"))
        .strip()
        .replace(" ", "_")
    )


def extract_transcript(page):
    # 🔥 TRY INLINE FIRST
    inline = page.locator("div.subtitles span")
    if inline.count() > 0:
        return " ".join(
            [
                inline.nth(i).inner_text().strip()
                for i in range(inline.count())
                if len(inline.nth(i).inner_text().strip()) > 5
            ]
        )

    # 🔥 FALLBACK → IFRAME
    for _ in range(5):
        for frame in page.frames:
            loc = frame.locator("ol[id*='transcript'] span")
            if loc.count() > 0:
                return " ".join(
                    [
                        loc.nth(i).inner_text().strip()
                        for i in range(loc.count())
                        if len(loc.nth(i).inner_text().strip()) > 5
                    ]
                )
        page.wait_for_timeout(2000)

    return ""


def click_transcript(page):
    try:
        btn = page.locator("button.toggle-transcript")
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_timeout(2000)
    except:
        pass


# =============================
# 🚀 MAIN
# =============================


def run():
    with sync_playwright() as p:

        browser = p.chromium.launch_persistent_context(
            user_data_dir="user_data",
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=False,
        )

        page = browser.new_page()
        page.goto("https://apps.iimbx.edu.in/learner-dashboard/")

        input("Login → Press ENTER")

        # =============================
        # 📚 COURSES
        # =============================
        page.wait_for_selector("text=Show Progress")
        courses = page.locator("text=Show Progress")

        course_list = []
        for i in range(courses.count()):
            name = (
                courses.nth(i)
                .locator("xpath=ancestor::div[2]")
                .inner_text()
                .split("\n")[0]
            )
            course_list.append((i, name))

        for i, (_, name) in enumerate(course_list):
            print(f"{i+1}. {name}")

        choice = int(input("Select course: ")) - 1
        courses.nth(course_list[choice][0]).locator("xpath=ancestor::div[2]").click()

        course_base = page.url

        # =============================
        # 📦 MODULES
        # =============================
        page.wait_for_selector(".collapsible-trigger")
        modules = page.locator(".collapsible-trigger")

        module_list = [
            (i, modules.nth(i).inner_text().split("\n")[0])
            for i in range(modules.count())
        ]

        for i, (_, name) in enumerate(module_list):
            print(f"{i+1}. {name}")

        mod_choice = int(input("Select module: ")) - 1
        module_trigger = modules.nth(module_list[mod_choice][0])
        expanded = False

        for _ in range(5):
            try:
                module_trigger.click()
                page.wait_for_timeout(1500)

                parent_block = module_trigger.locator("xpath=ancestor::li")
                lecture_links = parent_block.locator("ul li a")

                if lecture_links.count() > 5:
                    expanded = True
                    break

            except:
                pass

        if not expanded:
            print("❌ Module did not expand")
            return

        lecture_list = []
        print("🧪 Lecture count after expansion:", lecture_links.count())
        seen = set()

        for i in range(lecture_links.count()):
            text = lecture_links.nth(i).inner_text().strip()
            if text and text not in seen:
                seen.add(text)
                lecture_list.append((i, text))

        # =============================
        # 🔁 PROCESS LECTURES
        # =============================
        for idx, (original_index, lecture_name) in enumerate(lecture_list):

            print(f"\n🚀 {lecture_name}")

            page.goto(course_base)
            page.wait_for_timeout(3000)

            modules = page.locator(".collapsible-trigger")
            module_trigger = modules.nth(mod_choice)
            module_trigger.click()
            page.wait_for_timeout(2000)

            parent_block = module_trigger.locator("xpath=ancestor::li")
            lecture_links = parent_block.locator("ul li a")

            found = False

            for i in range(lecture_links.count()):
                try:
                    text = lecture_links.nth(i).inner_text().strip()
                    print("MATCH CHECK:", text, " | ", lecture_name)
                    if lecture_name.strip() in text.strip():
                        lecture_links.nth(i).scroll_into_view_if_needed()
                        try:
                            lecture_links.nth(i).click()
                        except:
                            page.evaluate("(el) => el.click()", lecture_links.nth(i))
                        found = True
                        print("✅ Clicked:", lecture_name)
                        break

                except:
                    pass

            if not found:
                print("❌ Lecture NOT FOUND:", lecture_name)
                continue

            page.wait_for_timeout(3000)

            click_transcript(page)

            inner_blocks = page.locator("a[href*='type@vertical']")
            sub_lectures = []

            for i in range(inner_blocks.count()):
                try:
                    text = inner_blocks.nth(i).inner_text().strip()
                    href = inner_blocks.nth(i).get_attribute("href")

                    # 🔥 STRICT FILTER
                    if not text or not href:
                        continue

                    if len(text) < 5:
                        continue

                    if "next" in text.lower():
                        continue

                    if not text[0].isdigit():
                        continue

                    sub_lectures.append((text, href))

                except:
                    pass

            if inner_blocks.count() > 1:
                for i in range(inner_blocks.count()):
                    text = inner_blocks.nth(i).inner_text().strip()
                    if "next" in text.lower():
                        continue
                    href = inner_blocks.nth(i).get_attribute("href")
                    if text and href:
                        sub_lectures.append((text, href))

            # =============================
            # 🔁 NESTED
            # =============================
            if sub_lectures:
                for sub_name, sub_href in sub_lectures:
                    page.goto("https://apps.iimbx.edu.in" + sub_href)
                    page.wait_for_timeout(3000)

                    click_transcript(page)
                    content = extract_transcript(page)

                    save_json(
                        course_list[choice][1],
                        module_list[mod_choice][1],
                        lecture_name,
                        sub_name,
                        content,
                    )

            # =============================
            # 🔁 SINGLE
            # =============================
            else:
                if inner_blocks.count() > 0:
                    href = inner_blocks.nth(0).get_attribute("href")
                    page.goto("https://apps.iimbx.edu.in" + href)
                    page.wait_for_timeout(3000)

                click_transcript(page)
                content = extract_transcript(page)

                save_json(
                    course_list[choice][1],
                    module_list[mod_choice][1],
                    lecture_name,
                    None,
                    content,
                )


def save_json(course, module, lecture, sub, content):

    folder = os.path.join(BASE_DIR, clean_name(course), clean_name(module))
    os.makedirs(folder, exist_ok=True)

    name = clean_name(sub if sub else lecture)

    with open(os.path.join(folder, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "course": course,
                "module": module,
                "lecture": lecture,
                "sublecture": sub,
                "content": content,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )


run()
