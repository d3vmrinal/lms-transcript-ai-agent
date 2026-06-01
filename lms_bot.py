from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime
import hashlib

DEBUG = False

# =============================
# 🔥 CONTENT CLASSIFIER
# =============================

def classify_content(title):

    t = title.lower()

    if any(x in t for x in [
        "quiz",
        "assessment",
        "mcq",
        "cla",
        "questions",
    ]):
        return "QUIZ"

    if any(x in t for x in [
        "discussion",
        "forum",
        "instructions",
    ]):
        return "FORUM"

    if any(x in t for x in [
        "handout",
        "pdf",
        "slides",
        "notes",
        "pre-read",
        "pre-reads",
        "reading",
    ]):
        return "HANDOUT"

    if any(x in t for x in [
        "game",
        "match",
        "activity",
        "exercise",
        "interlude",
    ]):
        return "ACTIVITY"

    if "welcome" in t:
        return "INTRO"

    return "VIDEO"

def transcript_expected(content_type):

    return content_type == "VIDEO"

def normalize_status(status):

    mapping = {
        "SUCCESS": "SUCCESS",
        "SKIPPED": "SKIPPED",
        "DUPLICATE": "DUPLICATE",
        "EMPTY_WARNING": "EMPTY",
        "NON_TRANSCRIPT": "NON_TRANSCRIPT",
    }

    return mapping.get(status, "UNKNOWN")

def save_failure_log(failure_data):

    log_path = "logs/failures.json"

    existing_logs = []

    if os.path.exists(log_path):

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                existing_logs = json.load(f)

        except:
            existing_logs = []

    existing_logs.append(failure_data)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(existing_logs, f, indent=4)

BASE_DIR = "output"
os.makedirs(BASE_DIR, exist_ok=True)


def run():
    with sync_playwright() as p:

        browser = p.chromium.launch_persistent_context(
            user_data_dir="user_data",
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=False,
        )

        page = browser.new_page()

        page.goto("https://apps.iimbx.edu.in/learner-dashboard/")

        print("\n🧠 NAV DEBUG")
        print("URL:", page.url)
        print("Inline count:", page.locator("div.subtitles span").count())
        print("Transcript count:", page.locator("ol[id*='transcript']").count())
        print("Frames:", len(page.frames))

        input("Login manually, then press ENTER...")

        page.goto("https://apps.iimbx.edu.in/learner-dashboard/")

        print("\n🧠 NAV DEBUG")
        print("URL:", page.url)
        print("Inline count:", page.locator("div.subtitles span").count())
        print("Transcript count:", page.locator("ol[id*='transcript']").count())
        print("Frames:", len(page.frames))

        input("Press Enter after page loads...")

        # 🔥 COURSES
        page.wait_for_selector("text=Show Progress")
        courses = page.locator("text=Show Progress")

        course_list = []
        for i in range(courses.count()):
            full_text = courses.nth(i).locator("xpath=ancestor::div[2]").inner_text()
            name = full_text.split("\n")[0].strip()
            course_list.append((i, name))

        print("\nAvailable Courses:\n")
        for idx, (_, name) in enumerate(course_list):
            print(f"{idx+1}. {name}")

        choice = int(input("\nEnter course number: "))

        selected_course_name = course_list[choice - 1][1]
        selected_index = course_list[choice - 1][0]

        courses.nth(selected_index).locator("xpath=ancestor::div[2]").click()

        print("✅ Course opened!")
        print("🧠 Selected course:", selected_course_name)

        # 🔥 DEFINE COURSE BASE (CRITICAL FIX)
        course_base = page.url
        print("🧠 Initial course base set:", course_base)

        # 🔥 MODULES
        page.wait_for_selector(".collapsible-trigger")
        modules = page.locator(".collapsible-trigger")

        module_list = []
        print("\n📦 Available Modules:\n")

        for i in range(modules.count()):
            text = modules.nth(i).inner_text().split("\n")[0]
            module_list.append((i, text))
            print(f"{i+1}. {text}")

        # =============================
        # 🔴 DEBUG BLOCK (YOU ASKED HERE)
        # =============================

        choice = int(input("\nSelect module: "))
        selected_module = module_list[choice - 1][0]

        module_trigger = modules.nth(selected_module)
        
        expand_button = module_trigger.locator("button").first

        print("🧪 Scrolling module into view...")

        try:
            expand_button.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

            print("🧪 Clicking module...")
            expand_button.click(timeout=10000)

            print("🧪 Waiting for lectures to appear...")

        except Exception as e:
            print("❌ Module click failed:", str(e))

        # 🔴 WAIT UNTIL LECTURES ACTUALLY LOAD

        lecture_count = 0

        for attempt in range(10):

            print(f"⏳ WAIT LOOP {attempt+1}/10")

            try:
                lecture_count = page.locator(".collapsible-body li").count()
                print("🧪 Lecture count:", lecture_count)

            except Exception as e:
                print("❌ Lecture count read failed:", str(e))

            try:
                expanded_attr = expand_button.get_attribute("aria-expanded")
                print("🧪 aria-expanded:", expanded_attr)

            except Exception as e:
                print("❌ aria-expanded read failed:", str(e))

            if lecture_count > 5:
                print("✅ Lectures loaded successfully")
                break

            print("⏳ Waiting 1 second...")
            page.wait_for_timeout(1000)

        print("🧪 FINAL lecture count:", lecture_count)

        # =============================
        # 🔥 GET LECTURES (CLEAN)
        # =============================

        selected_module_block = modules.nth(selected_module).locator(
            "xpath=ancestor::li"
        )

        lecture_links = selected_module_block.locator(".collapsible-body li a")

        count = lecture_links.count()
        # print("\nDEBUG → RAW LECTURE COUNT:", count)

        # =============================
        # VERIFICATION REGISTRIES
        # =============================

        expected_lectures = []

        lecture_status = {}

        audit_tree = {}
        
        failed_lectures = []
        
        seen_hashes = set()
        
        os.makedirs("logs", exist_ok=True)
        
        content_lengths = []
        
        content_lengths = []

        lecture_list = []
        seen = set()

        for i in range(count):
            try:
                text = lecture_links.nth(i).text_content()

                if text:
                    text = text.strip()

                if text and text not in seen:
                    seen.add(text)

                    lecture_list.append((i, text))

                    expected_lectures.append(text)
                    
                    audit_tree[text] = []

            except:
                pass

        print("\n📚 Available Lectures (CLEAN):\n")

        for idx, (_, text) in enumerate(lecture_list):

            content_type = classify_content(text)

            print(f"{idx+1}. [{content_type}] {text}")

        # print("\nDEBUG → UNIQUE COUNT:", len(lecture_list))

        # 🔴 AUTO PROCESS ALL LECTURES
        for idx, (original_index, lecture_name) in enumerate(lecture_list):

            content_type = classify_content(lecture_name)

            print(f"\n🚀 [{content_type}] Processing Lecture {idx+1}: {lecture_name}")

            # 🔥 ALWAYS RESET TO COURSE PAGE (CRITICAL FIX)
            try:
                if not course_base:
                    print("❌ course_base is EMPTY — skipping")
                    continue

                try:
                    page.goto(course_base)
                    print("🧪 Reset → course page loaded:", page.url)
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print("❌ Failed to reset to course page:", str(e))
                    continue
                print("🧪 Reset → course page loaded:", page.url)
                page.wait_for_timeout(3000)
            except:
                print("❌ Failed to reset to course page")
                continue

            print(f"🧪 Trying to click index: {original_index}")

            print("🧪 REFRESHING LECTURE LOCATOR...")

            # 🔥 FULL REFRESH (CRITICAL FIX)
            print("🧪 WAITING FOR MODULES TO STABILIZE...")

            modules = None

            for _ in range(10):
                temp_modules = page.locator(".collapsible-trigger")
                count = temp_modules.count()

                print("🧪 MODULE WAIT → count:", count)

                if count >= 3:
                    modules = temp_modules
                    break

                page.wait_for_timeout(1000)

            if modules is None:
                print("❌ Modules never loaded — skipping lecture")
                continue

            print("🧪 REFRESH → modules:", modules.count())

            module_trigger = modules.nth(selected_module)

            # 🔥 ENSURE MODULE IS EXPANDED (CRITICAL FIX)
            try:
                # 🔥 VERIFY MODULE EXPANSION (FINAL FIX)
                expanded = False

                for attempt in range(3):
                    try:
                        module_trigger.click()
                        page.wait_for_timeout(2000)

                        lecture_links = module_trigger.locator(
                            "xpath=ancestor::li"
                        ).locator(".collapsible-body li a")

                        count = lecture_links.count()
                        print(f"🧪 Attempt {attempt+1} → lecture count:", count)

                        if count > 5:
                            expanded = True
                            print("✅ Module successfully expanded")
                            break

                    except Exception as e:
                        print("⚠️ Click attempt failed:", str(e))

                if not expanded:
                    print("❌ Module did NOT expand — skipping lecture")
                    
                    failed_lectures.append({
                        "lecture": lecture_name,
                        "reason": "MODULE_NOT_EXPANDED",
                    })
                    
                    save_failure_log({
                        "course": selected_course_name,
                        "module": module_list[selected_module][1],
                        "lecture": lecture_name,
                        "reason": "MODULE_NOT_EXPANDED",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    continue

                page.wait_for_timeout(2000)
            except:
                try:
                    module_trigger.click(force=True)
                    print("🧪 Module force clicked (refresh)")
                except:
                    print("❌ Module click failed during refresh")

            page.wait_for_timeout(2000)

            lecture_links = module_trigger.locator("xpath=ancestor::li").locator(
                ".collapsible-body li a"
            )

            print("🧪 REFRESH → lectures:", lecture_links.count())

            print("🧪 Available lectures now:", lecture_links.count())

            print("🧪 REFRESH → lectures:", lecture_links.count())

            if lecture_links.count() == 0:
                print("❌ NO LECTURES FOUND AFTER REFRESH — skipping safely")
                
                failed_lectures.append({
                    "lecture": lecture_name,
                    "reason": "LECTURES_NOT_VISIBLE",
                })
                
                save_failure_log({
                    "course": selected_course_name,
                    "module": module_list[selected_module][1],
                    "lecture": lecture_name,
                    "reason": "LECTURES_NOT_VISIBLE",
                    "timestamp": datetime.now().isoformat()
                })
                
                continue

            link = lecture_links.nth(original_index)
            print("🧪 Attempting click on:", original_index)
            print("🧪 Total lectures available:", lecture_links.count())

            clicked = False

            try:
                link.scroll_into_view_if_needed()
                link.click(timeout=5000)
                clicked = True
            except:
                print("⚠️ Normal click failed")

            if not clicked:
                try:
                    link.click(force=True)
                    clicked = True
                    print("✅ Force click worked")
                except:
                    print("❌ Force click failed")

            if not clicked:
                try:
                    page.evaluate("(el) => el.click()", link)
                    clicked = True
                    print("✅ JS click worked")
                except:
                    print("❌ JS click failed")

            if not clicked:
                print("❌ ALL CLICK METHODS FAILED — skipping")
                
                failed_lectures.append({
                    "lecture": lecture_name,
                    "reason": "LECTURE_CLICK_FAILED",
                })
                
                save_failure_log({
                    "course": selected_course_name,
                    "module": module_list[selected_module][1],
                    "lecture": lecture_name,
                    "reason": "LECTURE_CLICK_FAILED",
                    "timestamp": datetime.now().isoformat()
                })
                
                continue

            page.wait_for_timeout(3000)

            print("✅ Lecture clicked!")
            print(f"DEBUG → Current URL: {page.url}")

            # 🔥 EXTRACT COURSE BASE URL (CRITICAL FIX)
            current_url = page.url

            if "/block-v1:" in current_url:
                course_base = current_url.split("/block-v1:")[0] + "/home"
            else:
                course_base = current_url

            print("🧠 Extracted course base:", course_base)

            print("\n🧠 FRAME DEBUG START")

            frames = page.frames
            print("🧪 Total frames:", len(frames))

            for i, f in enumerate(frames):
                try:
                    print(f"Frame {i} URL:", f.url)
                except:
                    print(f"Frame {i} URL: ERROR")

            print("🧠 FRAME DEBUG END\n")

            print("🧪 DEBUG → Searching inner blocks...")

            inner_blocks = page.locator("a[href*='type@vertical']")

            print("🧪 Inner block count:", inner_blocks.count())

            for i in range(inner_blocks.count()):
                try:
                    txt = inner_blocks.nth(i).inner_text()
                    href = inner_blocks.nth(i).get_attribute("href")
                    print(f"   → {i}: {txt} | {href}")
                except:
                    pass

            # 🔥 CLICK TRANSCRIPT BUTTON (CRITICAL FIX)
            try:
                btn = page.locator("button.toggle-transcript")

                if btn.count() > 0:
                    btn.first.click()
                    print("✅ Clicked transcript button")

                    try:
                        page.wait_for_selector(
                            "ol[id*='transcript'] span", timeout=10000
                        )
                    except:
                        print("⚠️ Transcript did not load after click")
                else:
                    print("⚠️ No transcript button found")

            except:
                print("⚠️ Transcript click failed")

            # =============================
            # STEP — CHECK FOR NESTED LECTURES
            # =============================

            # CORRECT NESTED DETECTION (FINAL FIX)

            inner_blocks = page.locator("a[href*='type@vertical']")

            sub_lecture_list = []

            print("\n🧪 Checking nested lectures via INNER BLOCKS...")

            if inner_blocks.count() > 1:
                
                if inner_blocks.count() == 1:
                    print("⚠️ Single inner block (treat as main lecture)")
                
                print(f"✅ Nested lectures detected: {inner_blocks.count()}")

                for i in range(inner_blocks.count()):
                    try:
                        text = inner_blocks.nth(i).inner_text().strip()
                        text = text.replace(", Incomplete unit", "")
                        text = text.replace(", Completed unit", "")
                        text = text.strip()

                        clean_text = text.lower()

                        if clean_text in ["next", "previous"]:
                            print(f"⏭️ Ignoring navigation button: {text}")
                            continue

                        href = inner_blocks.nth(i).get_attribute("href")

                        print(f"   → {text}")

                        if text and href:
                            sub_lecture_list.append((i, text, href))

                    except:
                        pass

            else:
                print("⚠️ No nested lectures found")

            # 🔥 ENTER ACTUAL VIDEO BLOCK (CRITICAL FIX)

            try:
                inner_video = page.locator("a[href*='type@vertical']")

                if len(sub_lecture_list) == 0 and inner_blocks.count() > 0:

                    href = inner_blocks.nth(0).get_attribute("href")

                    full_url = "https://apps.iimbx.edu.in" + href

                    print("🌐 Navigating to:", full_url)

                    page.goto(full_url)

                    print("\n🧠 NAV DEBUG")
                    print("URL:", page.url)
                    print("Inline count:", page.locator("div.subtitles span").count())
                    print(
                        "Transcript count:",
                        page.locator("ol[id*='transcript']").count(),
                    )
                    print("Frames:", len(page.frames))

                    page.wait_for_timeout(3000)
                else:
                    print("⚠️ No inner block found")

            except Exception as e:
                print("❌ Inner block navigation failed:", str(e))

            # 🔴 WAIT FOR IFRAME TO LOAD (CRITICAL FIX)
            iframe_count = 0
            for _ in range(10):
                iframe_count = page.locator("iframe").count()
                print(f"DEBUG → iframe count: {iframe_count}")

                if iframe_count == 0:
                    print("❌ NO IFRAME LOADED")

                if iframe_count > 0:
                    break

                page.wait_for_timeout(1000)

            content = ""

            # =============================
            # 🔥 IF SUB LECTURES EXIST → PROCESS THEM
            # =============================
            print("🔁 Returning using course base...")
            if len(sub_lecture_list) >= 1:

                print("🚀 Processing nested lectures...")

                for sub_idx, (sub_i, sub_name, sub_href) in enumerate(sub_lecture_list):

                    sub_type = classify_content(sub_name)

                    print(f"\n➡️ [{sub_type}] Sub Lecture {sub_idx+1}: {sub_name}")

                    full_url = "https://apps.iimbx.edu.in" + sub_href

                    print("🌐 Sub navigating to:", full_url)

                    page.goto(full_url)

                    page.wait_for_timeout(3000)

                    # 🔥 CLICK TRANSCRIPT BUTTON FOR SUB LECTURE
                    try:
                        btn = page.locator("button.toggle-transcript")

                        if btn.count() > 0:
                            btn.first.click()
                            print("✅ Clicked transcript (sub)")

                            try:
                                page.wait_for_selector(
                                    "ol[id*='transcript'] span", timeout=10000
                                )
                            except:
                                print("⚠️ Nested transcript did not load")
                        else:
                            print("⚠️ No transcript button in sub lecture")

                    except:
                        print("⚠️ Transcript click failed (sub)")

                    print("🧪 SUB STEP 1 → Checking INLINE transcript")

                    sub_content = ""
                    found = False

                    # 🔥 INLINE FIRST
                    try:
                        inline = page.locator("div.subtitles span")
                        count = inline.count()

                        print("🧪 Inline count:", count)

                        if count > 0:
                            print("✅ FOUND INLINE (sub)")

                            lines = []

                            for j in range(count):
                                try:
                                    t = inline.nth(j).inner_text().strip()
                                    if len(t) > 5 and t != "[Music]":
                                        lines.append(t)
                                except:
                                    pass

                            sub_content = " ".join(lines)
                            found = True

                    except Exception as e:
                        print("❌ Inline sub error:", str(e))

                    # 🔥 FRAME FALLBACK
                    if not found:

                        print("🧪 SUB STEP 2 → Checking frames")

                        # 🔥 RETRY FRAME EXTRACTION (FIX FOR 2.3)
                        print("🧪 SUB STEP 2 → Checking frames (with retry)")

                        for attempt in range(5):  # try 5 times

                            print(f"⏳ Attempt {attempt+1} → scanning frames...")

                            for idx_f, frame in enumerate(page.frames):

                                try:
                                    transcript = frame.locator(
                                        "ol[id*='transcript'] span"
                                    )
                                    count = transcript.count()

                                    print(f"   → frame {idx_f} count:", count)

                                    if count > 0:
                                        print("✅ FOUND in frame (sub):", idx_f)

                                        lines = []

                                        for j in range(count):
                                            try:
                                                t = (
                                                    transcript.nth(j)
                                                    .inner_text()
                                                    .strip()
                                                )
                                                if len(t) > 5 and t != "[Music]":
                                                    lines.append(t)
                                            except:
                                                pass

                                        sub_content = " ".join(lines)
                                        found = True
                                        break

                                except:
                                    pass

                            if found:
                                break

                            print("⏳ Waiting for transcript to load...")
                            page.wait_for_timeout(2000)  # wait 2 sec before retry

                    if not found:
                        print("⚠️ NO transcript in sub lecture")
                    
                        if len(sub_content.strip()) < 100:

                            sub_type = classify_content(sub_name)

                            if transcript_expected(sub_type):

                                print("⚠️ EMPTY/SHORT transcript warning")

                                lecture_status[sub_name] = "EMPTY_WARNING"

                                audit_tree.setdefault(lecture_name, [])

                                audit_tree[lecture_name].append(
                                    (sub_name, "EMPTY_WARNING")
                                )

                            else:

                                lecture_status[sub_name] = "NON_TRANSCRIPT"

                                audit_tree.setdefault(lecture_name, [])

                                audit_tree[lecture_name].append(
                                    (sub_name, "NON_TRANSCRIPT")
                                )

                    # 🔴 SAVE FILE
                    # 🔥 STRUCTURED SAVE (JSON)

                    safe_course = (
                        "".join(
                            c
                            for c in selected_course_name
                            if c.isalnum() or c in (" ", "_")
                        )
                        .strip()
                        .replace(" ", "_")
                    )
                    safe_module = (
                        "".join(
                            c
                            for c in module_list[selected_module][1]
                            if c.isalnum() or c in (" ", "_")
                        )
                        .strip()
                        .replace(" ", "_")
                    )
                    safe_lecture = (
                        "".join(
                            c for c in lecture_name if c.isalnum() or c in (" ", "_")
                        )
                        .strip()
                        .replace(" ", "_")
                    )
                    safe_sub = (
                        "".join(c for c in sub_name if c.isalnum() or c in (" ", "_"))
                        .strip()
                        .replace(" ", "_")
                    )

                    folder_path = os.path.join(BASE_DIR, safe_course, safe_module)
                    os.makedirs(folder_path, exist_ok=True)

                    file_path = os.path.join(folder_path, f"{safe_sub}.json")
                    
                    if os.path.exists(file_path):
                        print(f"⏭️ Already exists, skipping: {safe_sub}")

                        lecture_status[sub_name] = "SKIPPED"

                        audit_tree.setdefault(lecture_name, [])

                        audit_tree[lecture_name].append(
                            (sub_name, "SKIPPED")
                        )

                        continue
                    
                    lecture_record = {
                        "title": sub_name,
                        "type": classify_content(sub_name),
                        "status": lecture_status.get(sub_name, "UNKNOWN"),
                        "content_length": len(sub_content),
                        "has_transcript": len(sub_content.strip()) >= 100,
                        "video_detected": transcript_expected(sub_type),
                        "iframe_attempts": iframe_count,
                    }
                    
                    content_lengths.append(len(sub_content))
                    
                    content_hash = None

                    if (
                        len(sub_content.strip()) >= 100
                        and transcript_expected(sub_type)
                    ):

                        content_hash = hashlib.md5(
                            sub_content.encode("utf-8")
                        ).hexdigest()

                        if content_hash in seen_hashes:

                            print("♻️ DUPLICATE SUB CONTENT DETECTED")

                            lecture_status[sub_name] = "DUPLICATE"

                            audit_tree.setdefault(lecture_name, [])

                            audit_tree[lecture_name].append(
                                (sub_name, "DUPLICATE")
                            )

                            continue

                        seen_hashes.add(content_hash)

                    data = {
                        "course": selected_course_name,
                        "module": module_list[selected_module][1],

                        "lecture": lecture_name,
                        "sublecture": sub_name,
                        
                        "lecture_id": (
                            selected_course_name
                                .upper()
                                .replace(" ", "_")
                            + "__"
                            + sub_name.split(" ")[0]
                                .replace(".", "_")
                        ),

                        "type": lecture_record["type"],
                        "status": (
                            "SUCCESS"
                            if len(sub_content.strip()) >= 100
                            and transcript_expected(sub_type)

                            else "NON_TRANSCRIPT"
                            if not transcript_expected(sub_type)

                            else "EMPTY"
                        ),
                        
                        "vectorizable": (
                            len(sub_content.strip()) >= 100
                            and transcript_expected(sub_type)
                        ),

                        "content_length": lecture_record["content_length"],
                        "has_transcript": lecture_record["has_transcript"],

                        "source_url": page.url,
                        "extracted_at": datetime.now().isoformat(),
                        "content_hash": content_hash,

                        "content": sub_content,
                    }

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                    print(f"💾 Saved JSON: {file_path}")
                    
                    preview = sub_content[:100].replace("\n", " ")

                    print(f"📝 Preview: {preview}")
                    
                    if len(sub_content.strip()) >= 100:

                        if sub_name not in lecture_status:

                            lecture_status[sub_name] = "SUCCESS"

                            audit_tree.setdefault(lecture_name, [])

                            existing_children = [
                                x[0] for x in audit_tree[lecture_name]
                            ]

                            if sub_name not in existing_children:

                                audit_tree[lecture_name].append(
                                    (sub_name, "SUCCESS")
                                )

                print("🔁 Returning using course base...")

                try:
                    page.goto(course_base)
                    page.wait_for_timeout(4000)

                    print("🧪 After return → URL:", page.url)

                    # 🔥 RE-LOCATE MODULES (FRESH DOM)
                    modules = page.locator(".collapsible-trigger")

                    print("🧪 Modules found:", modules.count())

                    module_trigger = modules.nth(selected_module)

                    print("🧪 Re-clicking module...")

                    try:
                        module_trigger.click()
                    except:
                        try:
                            module_trigger.click(force=True)
                        except:
                            print("❌ Module click failed")

                    # 🔥 WAIT FOR LECTURES TO LOAD PROPERLY
                    for _ in range(10):
                        lecture_count = page.locator(".collapsible-body li a").count()
                        print("🧪 WAIT → Lecture count:", lecture_count)

                        if lecture_count > 5:
                            break

                        page.wait_for_timeout(1000)

                    print("🧪 Lecture count after restore:", lecture_count)

                except Exception as e:
                    print("❌ Return failed:", str(e))

            # =============================
            # 🔥 IF NO SUB-LECTURES → PROCESS MAIN LECTURE
            # =============================

            if len(sub_lecture_list) == 0:

                print("⚠️ No sub-lectures → processing main lecture")

                main_content = ""
                found = False
                main_type = classify_content(lecture_name)

                # 🔥 INLINE FIRST
                try:
                    inline = page.locator("div.subtitles span")
                    count = inline.count()

                    print("🧪 MAIN Inline count:", count)

                    if count > 0:
                        print("✅ FOUND INLINE (main)")

                        lines = []
                        for j in range(count):
                            try:
                                t = inline.nth(j).inner_text().strip()
                                if len(t) > 5 and t != "[Music]":
                                    lines.append(t)
                            except:
                                pass

                        main_content = " ".join(lines)
                        found = True

                except Exception as e:
                    print("❌ Inline main error:", str(e))

                # 🔥 FRAME FALLBACK
                if not found:

                    print("🧪 MAIN → Checking frames")

                    for attempt in range(5):

                        print(f"⏳ Attempt {attempt+1} → scanning frames...")

                        for idx_f, frame in enumerate(page.frames):

                            try:
                                transcript = frame.locator("ol[id*='transcript'] span")
                                count = transcript.count()

                                print(f"   → frame {idx_f} count:", count)

                                if count > 0:
                                    print("✅ FOUND in frame (main):", idx_f)

                                    lines = []

                                    for j in range(count):
                                        try:
                                            t = transcript.nth(j).inner_text().strip()
                                            if len(t) > 5 and t != "[Music]":
                                                lines.append(t)
                                        except:
                                            pass

                                    main_content = " ".join(lines)
                                    found = True
                                    break

                            except:
                                pass

                        if found:
                            break

                        page.wait_for_timeout(2000)

                if not found:
                    print("⚠️ NO transcript in main lecture")
                    
                    if len(main_content.strip()) < 100:

                        main_type = classify_content(lecture_name)

                        if transcript_expected(main_type):

                            print("⚠️ EMPTY/SHORT transcript warning")

                            lecture_status[lecture_name] = "EMPTY_WARNING"

                            audit_tree[lecture_name] = [(lecture_name, "EMPTY_WARNING")]
                            #audit_tree.setdefault(lecture_name, [])

                        else:

                            lecture_status[lecture_name] = "NON_TRANSCRIPT"

                            audit_tree[lecture_name] = [(lecture_name, "NON_TRANSCRIPT")]
                            #audit_tree.setdefault(lecture_name, [])

                # 🔥 SAVE MAIN LECTURE
                safe_course = (
                    "".join(
                        c
                        for c in selected_course_name
                        if c.isalnum() or c in (" ", "_")
                    )
                    .strip()
                    .replace(" ", "_")
                )
                safe_module = (
                    "".join(
                        c
                        for c in module_list[selected_module][1]
                        if c.isalnum() or c in (" ", "_")
                    )
                    .strip()
                    .replace(" ", "_")
                )
                safe_lecture = (
                    "".join(c for c in lecture_name if c.isalnum() or c in (" ", "_"))
                    .strip()
                    .replace(" ", "_")
                )

                folder_path = os.path.join(BASE_DIR, safe_course, safe_module)
                os.makedirs(folder_path, exist_ok=True)

                file_path = os.path.join(folder_path, f"{safe_lecture}.json")
                
                if os.path.exists(file_path):
                    print(f"⏭️ Already exists, skipping: {safe_lecture}")

                    lecture_status[lecture_name] = "SKIPPED"
                    audit_tree[lecture_name] = [(lecture_name, "SKIPPED")]
                    #audit_tree.setdefault(lecture_name, [])

                    continue
                    
                lecture_record = {
                    "title": lecture_name,
                    "type": classify_content(lecture_name),
                    "status": lecture_status.get(lecture_name, "UNKNOWN"),
                    "content_length": len(main_content),
                    "has_transcript": len(main_content.strip()) >= 100,
                    "video_detected": transcript_expected(main_type),
                    "iframe_attempts": iframe_count,
                }    
                
                content_hash = None

                if (
                    len(main_content.strip()) >= 100
                    and transcript_expected(main_type)
                ):

                    content_hash = hashlib.md5(
                        main_content.encode("utf-8")
                    ).hexdigest()

                    if content_hash in seen_hashes:

                        print("♻️ DUPLICATE CONTENT DETECTED")

                        lecture_status[lecture_name] = "DUPLICATE"

                        audit_tree[lecture_name] = [
                            (lecture_name, "DUPLICATE")
                        ]

                        continue

                    seen_hashes.add(content_hash)
                    
                data = {
                    "course": selected_course_name,
                    "module": module_list[selected_module][1],

                    "lecture": lecture_name,
                    "sublecture": None,
                    
                    "lecture_id": (
                        selected_course_name
                            .upper()
                            .replace(" ", "_")
                        + "__"
                        + lecture_name.split(" ")[0]
                            .replace(".", "_")
                    ),
                    
                    "type": lecture_record["type"],

                    "status": (
                        "SUCCESS"
                        if len(main_content.strip()) >= 100
                        and transcript_expected(main_type)

                        else "NON_TRANSCRIPT"
                        if not transcript_expected(main_type)

                        else "EMPTY"
                    ),
                    
                    "vectorizable": (
                        len(main_content.strip()) >= 100
                        and transcript_expected(main_type)
                    ),

                    "content_length": lecture_record["content_length"],
                    "has_transcript": lecture_record["has_transcript"],

                    "source_url": page.url,
                    "extracted_at": datetime.now().isoformat(),
                    "content_hash": content_hash,

                    "content": main_content,
                }

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                print(f"💾 Saved MAIN JSON: {file_path}")
                
                preview = main_content[:100].replace("\n", " ")

                print(f"📝 Preview: {preview}")
                
                if len(main_content.strip()) >= 100:

                    if lecture_name not in lecture_status:

                        lecture_status[lecture_name] = "SUCCESS"

                        audit_tree[lecture_name] = [
                            (lecture_name, "SUCCESS")
                        ]
                    
        # lecture loop ends here                    
                            
        # =============================
        # 🔥 FINAL VERIFICATION REPORT
        # =============================

        successful = []
        skipped = []
        empty = []
        non_transcript = []
        duplicates = []

        for lec, status in lecture_status.items():

            if status == "SUCCESS":
                successful.append(lec)

            elif status == "SKIPPED":
                skipped.append(lec)

            elif status == "EMPTY_WARNING":
                empty.append(lec)

            elif status == "NON_TRANSCRIPT":
                non_transcript.append(lec)
                
            elif status == "DUPLICATE":
                duplicates.append(lec)

        missing_lectures = []

        for lec in expected_lectures:

            if lec in lecture_status:
                continue

            lecture_prefix = lec.split(" ")[0]

            child_found = False

            for processed in lecture_status.keys():

                processed_prefix = processed.split(" ")[0]

                if processed.startswith(lecture_prefix + "."):
                    child_found = True
                    break

            if not child_found:
                missing_lectures.append(lec)
        
        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        safe_course = (
            selected_course_name
                .replace(" ", "_")
                .replace("&", "and")
        )

        safe_module = (
            module_list[selected_module][1]
                .replace(" ", "_")
                .replace(":", "")
                .replace("&", "and")
                .replace("|", "")
                .replace("/", "")
                .replace("\\", "")
                .replace("?", "")
                .replace("*", "")
                .replace("<", "")
                .replace(">", "")
        )

        log_folder = os.path.join(
            "logs",
            safe_course,
            safe_module
        )

        os.makedirs(
            log_folder,
            exist_ok=True
        )
        
        tree_json = {
            "course": selected_course_name,
            "module": module_list[selected_module][1],
            "generated_at": datetime.now().isoformat(),
            "lectures": []
        }

        for parent, children in audit_tree.items():

            lecture_entry = {
                "parent": parent,
                "children": []
            }

            for child_name, child_status in children:

                lecture_entry["children"].append({
                    "title": child_name,
                    "status": child_status
                })

            tree_json["lectures"].append(
                lecture_entry
            )
        
        print("\n========================")
        print("🌳 FULL EXTRACTION TREE")
        print("========================")
        
        tree_json = {
            "course": selected_course_name,
            "module": module_list[selected_module][1],
            "generated_at": datetime.now().isoformat(),
            "lectures": []
        }

        for parent, children in audit_tree.items():

            lecture_entry = {
                "parent": parent,
                "children": []
            }

            for child_name, child_status in children:

                lecture_entry["children"].append({
                    "title": child_name,
                    "status": child_status
                })

            tree_json["lectures"].append(
                lecture_entry
            )

        for parent, children in audit_tree.items():

            print(f"\n📘 {parent}")

            if len(children) == 0:
                print("   └── ⚠️ NO CHILD RECORDS")

            for child_name, status in children:

                icon = "✅"

                if status == "SKIPPED":
                    icon = "⏭️"

                elif status == "EMPTY_WARNING":
                    icon = "⚠️"

                elif status == "NON_TRANSCRIPT":
                    icon = "🟡"

                print(f"   └── {icon} {child_name}")

        print("\n========================")
        print("📊 FINAL EXTRACTION REPORT")
        print("========================")

        parent_count = len(expected_lectures)
        unit_count = len(lecture_status)

        print("📚 Parent Lectures:", parent_count)
        print("🧩 Extracted Units:", unit_count)

        print("✅ Transcript Extracted:", len(successful))
        print("⏭️ Skipped Existing:", len(skipped))
        print("🟡 Non-Transcript Content:", len(non_transcript))
        print("♻️ Duplicate Content:", len(duplicates))
        print("⚠️ Empty/Unexpected:", len(empty))
        print("❌ Missing:", len(missing_lectures))
        print("🚨 Failed Operations:", len(failed_lectures))
        
        print("\n========================")
        print("📈 INGESTION ANALYTICS")
        print("========================")

        if len(content_lengths) > 0:

            avg_length = sum(content_lengths) // len(content_lengths)

            print("🧠 Average Content Length:", avg_length)

            print("📏 Largest Lecture:", max(content_lengths))

            print("📉 Smallest Lecture:", min(content_lengths))

            small_lectures = [x for x in content_lengths if x < 5000]
            huge_lectures = [x for x in content_lengths if x > 250000]

            print("⚠️ Lectures Below 5k Chars:", len(small_lectures))

            print("🚨 Lectures Above 250k Chars:", len(huge_lectures))

        else:

            print("⚠️ No content lengths recorded")
        
        with open(
            "logs/extraction_tree.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                tree_json,
                f,
                indent=4
            )
        
        report_data = {
            "successful": successful,
            "skipped": skipped,
            "empty": empty,
            "non_transcript": non_transcript,
            "duplicates": duplicates,
            "missing": missing_lectures,
            "failed_operations": failed_lectures,
            "generated_at": datetime.now().isoformat()
        }
        
        analytics_data = {

            "average_content_length": (
                sum(content_lengths) // len(content_lengths)
                if len(content_lengths) > 0 else 0
            ),

            "largest_lecture": (
                max(content_lengths)
                if len(content_lengths) > 0 else 0
            ),

            "smallest_lecture": (
                min(content_lengths)
                if len(content_lengths) > 0 else 0
            ),

            "lectures_below_5k": len(
                [x for x in content_lengths if x < 5000]
            ),

            "lectures_above_250k": len(
                [x for x in content_lengths if x > 250000]
            ),

            "total_lectures_analyzed": len(content_lengths),

            "generated_at": datetime.now().isoformat()
        }
        
        report_path = os.path.join(
            log_folder,
            f"extraction_report_{timestamp}.json"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report_data,
                f,
                indent=4
            )

        tree_path = os.path.join(
            log_folder,
            f"extraction_tree_{timestamp}.json"
        )
        
        analytics_path = os.path.join(
            log_folder,
            f"ingestion_analytics_{timestamp}.json"
        )

        with open(
            tree_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                tree_json,
                f,
                indent=4
            )

        with open(
            analytics_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                analytics_data,
                f,
                indent=4
            )

        print(f"\n📝 Extraction tree saved:")
        print(tree_path)

        print(f"\n📊 Extraction report saved:")
        print(report_path)

        print(f"\n📈 Ingestion analytics saved:")
        print(analytics_path)
        
        if len(failed_lectures) > 0:

            print("\n🚨 FAILURE DETAILS:")
            for fail in failed_lectures:

                print(f"   → {fail['lecture']} | {fail['reason']}")

run()
input("Press Enter to close...")
