from playwright.sync_api import sync_playwright
import json
import os

DEBUG = False

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
        selected_index = course_list[choice - 1][0]

        courses.nth(selected_index).locator("xpath=ancestor::div[2]").click()
        print("✅ Course opened!")

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

        # 🔴 TRY MULTIPLE CLICK METHODS
        try:
            module_trigger.click()
            page.wait_for_timeout(3000)
        except:
            pass

        try:
            module_trigger.click(force=True)
        except:
            pass

        try:
            page.evaluate("(el) => el.click()", module_trigger)
        except:
            pass

        # 🔴 WAIT UNTIL LECTURES ACTUALLY LOAD
        for _ in range(10):
            li_count = page.locator(".collapsible-body li").count()
            # print("🔴 WAIT LOOP → LI COUNT:", li_count)

            if li_count > 5:
                break

            page.wait_for_timeout(1000)

        # =============================
        # 🔥 GET LECTURES (CLEAN)
        # =============================

        selected_module_block = modules.nth(selected_module).locator(
            "xpath=ancestor::li"
        )

        lecture_links = selected_module_block.locator(".collapsible-body li a")

        # =============================
        # 🧪 STEP 0 — EXTRACT ALL LINKS (MAIN + NESTED)
        # =============================

        print("\n🧪 ALL LINKS (RAW — INCLUDING NESTED):\n")

        all_links_debug = []

        for i in range(lecture_links.count()):
            try:
                text = lecture_links.nth(i).inner_text().strip()
                href = lecture_links.nth(i).get_attribute("href")

                print(f"{i+1}. {text}  -->  {href}")

                all_links_debug.append((text, href))

            except:
                pass

        print(f"\n🔍 TOTAL LINKS FOUND: {len(all_links_debug)}")

        # print("\n🔴 DEBUG → LINKS FOUND:", lecture_links.count())

        # for i in range(min(5, lecture_links.count())):
        #   try:
        #       print("→", lecture_links.nth(i).inner_text())
        #   except:
        #       pass

        count = lecture_links.count()
        # print("\nDEBUG → RAW LECTURE COUNT:", count)

        lecture_list = []
        seen = set()

        for i in range(count):
            try:
                text = lecture_links.nth(i).inner_text().strip()

                if text and text not in seen:
                    seen.add(text)
                    lecture_list.append((i, text))

            except:
                pass

        print("\n📚 Available Lectures (CLEAN):\n")

        for idx, (_, text) in enumerate(lecture_list):
            print(f"{idx+1}. {text}")

        # print("\nDEBUG → UNIQUE COUNT:", len(lecture_list))

        # 🔴 AUTO PROCESS ALL LECTURES
        for idx, (original_index, lecture_name) in enumerate(lecture_list):

            print(f"\n🚀 Processing Lecture {idx+1}: {lecture_name}")

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
            # 🔥 STEP — CHECK FOR NESTED LECTURES
            # =============================

            # 🔥 CORRECT NESTED DETECTION (FINAL FIX)

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
                        if "next" in text.lower():
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

                    print(f"\n➡️ Sub Lecture {sub_idx+1}: {sub_name}")

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

                    # 🔴 SAVE FILE
                    # 🔥 STRUCTURED SAVE (JSON)

                    safe_course = (
                        "".join(
                            c
                            for c in course_list[choice - 1][1]
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

                    data = {
                        "course": course_list[choice - 1][1],
                        "module": module_list[selected_module][1],
                        "lecture": lecture_name,
                        "sublecture": sub_name,
                        "content": sub_content,
                    }

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                    print(f"💾 Saved JSON: {file_path}")

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

                # 🔥 SAVE MAIN LECTURE
                safe_course = (
                    "".join(
                        c
                        for c in course_list[choice - 1][1]
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

                data = {
                    "course": course_list[choice - 1][1],
                    "module": module_list[selected_module][1],
                    "lecture": lecture_name,
                    "sublecture": None,
                    "content": main_content,
                }

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                print(f"💾 Saved MAIN JSON: {file_path}")


run()
input("Press Enter to close...")
