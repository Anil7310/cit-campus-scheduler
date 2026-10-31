import json
import csv
import os
import random

def generate():
    os.makedirs('starter-pack', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('docs', exist_ok=True)

    # 1. ROOMS (27)
    rooms = [
        {"id": "AUD", "name": "Main Auditorium", "type": "auditorium", "capacity": 450, "accessible": True, "features": ["projector", "ac", "sound_system", "stage"], "maintenance_windows": [{"day": "Wed", "start_period": "P8", "end_period": "P9"}]},
        {"id": "OAT", "name": "Open Air Theatre", "type": "open_air_theatre", "capacity": 600, "accessible": True, "features": ["stage", "sound_system"], "maintenance_windows": []},
        {"id": "SH-1", "name": "Seminar Hall 1", "type": "seminar_hall", "capacity": 160, "accessible": True, "features": ["projector", "ac", "sound_system"], "maintenance_windows": []},
        {"id": "SH-2", "name": "Seminar Hall 2", "type": "seminar_hall", "capacity": 150, "accessible": False, "features": ["projector", "ac", "sound_system"], "maintenance_windows": [{"day": "Fri", "start_period": "P7", "end_period": "P9"}]},
        {"id": "LH-1", "name": "Lecture Hall 1", "type": "lecture_hall", "capacity": 150, "accessible": True, "features": ["projector", "ac"], "maintenance_windows": []},
        {"id": "LH-2", "name": "Lecture Hall 2", "type": "lecture_hall", "capacity": 150, "accessible": True, "features": ["projector", "ac"], "maintenance_windows": []},
        {"id": "LH-3", "name": "Lecture Hall 3", "type": "lecture_hall", "capacity": 140, "accessible": False, "features": ["projector", "ac"], "maintenance_windows": []},
        {"id": "LH-4", "name": "Lecture Hall 4", "type": "lecture_hall", "capacity": 140, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "LH-5", "name": "Lecture Hall 5", "type": "lecture_hall", "capacity": 130, "accessible": True, "features": ["projector", "ac"], "maintenance_windows": []},
        {"id": "LH-6", "name": "Lecture Hall 6", "type": "lecture_hall", "capacity": 130, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-1", "name": "Classroom 1", "type": "classroom", "capacity": 80, "accessible": True, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-2", "name": "Classroom 2", "type": "classroom", "capacity": 80, "accessible": True, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-3", "name": "Classroom 3", "type": "classroom", "capacity": 80, "accessible": True, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-4", "name": "Classroom 4", "type": "classroom", "capacity": 80, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-5", "name": "Classroom 5", "type": "classroom", "capacity": 80, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-6", "name": "Classroom 6", "type": "classroom", "capacity": 80, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-7", "name": "Classroom 7", "type": "classroom", "capacity": 75, "accessible": True, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-8", "name": "Classroom 8", "type": "classroom", "capacity": 75, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-9", "name": "Classroom 9", "type": "classroom", "capacity": 75, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "CR-10", "name": "Classroom 10", "type": "classroom", "capacity": 75, "accessible": False, "features": ["projector"], "maintenance_windows": []},
        {"id": "LAB-CS1", "name": "Computing Lab 1", "type": "computer_lab", "capacity": 80, "accessible": True, "features": ["computers", "ac", "projector"], "maintenance_windows": []},
        {"id": "LAB-CS2", "name": "Computing Lab 2", "type": "computer_lab", "capacity": 80, "accessible": False, "features": ["computers", "ac", "projector"], "maintenance_windows": []},
        {"id": "LAB-PHY", "name": "Physics Laboratory", "type": "physics_lab", "capacity": 75, "accessible": True, "features": ["dark_room", "optical_benches"], "maintenance_windows": []},
        {"id": "LAB-CHE", "name": "Chemistry Laboratory", "type": "chemistry_lab", "capacity": 75, "accessible": True, "features": ["fume_hoods"], "maintenance_windows": []},
        {"id": "LAB-EE", "name": "Electrical Machines Lab", "type": "electrical_lab", "capacity": 75, "accessible": False, "features": ["workbenches", "oscilloscopes"], "maintenance_windows": []},
        {"id": "LAB-ME", "name": "Mechanical Workshop", "type": "mechanical_lab", "capacity": 75, "accessible": True, "features": ["lathes", "cnc"], "maintenance_windows": []},
        {"id": "LAB-CE", "name": "Civil Survey & Material Lab", "type": "civil_lab", "capacity": 75, "accessible": True, "features": ["utm_machine"], "maintenance_windows": []}
    ]

    # 2. FACULTY (40)
    departments = ["CSE", "ECE", "ME", "CE", "EE", "BS"]
    faculty_names = [
        ("F01", "Dr. A. Sharma", "CSE"), ("F02", "Dr. B. Das", "CSE"), ("F03", "Prof. C. Patra", "CSE"), ("F04", "Dr. D. Sen", "CSE"),
        ("F05", "Prof. E. Naik", "CSE"), ("F06", "Dr. F. Mohanty", "CSE"), ("F07", "Dr. G. Mishra", "CSE"), ("F08", "Prof. H. Sahoo", "CSE"),
        ("F09", "Dr. I. Jena", "ECE"), ("F10", "Prof. J. Panda", "ECE"), ("F11", "Dr. K. Pradhan", "ECE"), ("F12", "Dr. L. Rout", "ECE"),
        ("F13", "Prof. M. Behera", "ECE"), ("F14", "Dr. N. Swain", "ECE"), ("F15", "Dr. O. Tripathy", "ECE"), ("F16", "Prof. P. Samal", "ECE"),
        ("F17", "Dr. Q. Biswal", "ME"), ("F18", "Prof. R. Panigrahi", "ME"), ("F19", "Dr. S. Nayak", "ME"), ("F20", "Dr. T. Barik", "ME"),
        ("F21", "Prof. U. Acharya", "ME"), ("F22", "Dr. V. Nanda", "ME"), ("F23", "Dr. W. Kar", "ME"), ("F24", "Prof. X. Sethi", "ME"),
        ("F25", "Dr. Y. Khatua", "CE"), ("F26", "Prof. Z. Majhi", "CE"), ("F27", "Dr. AA. Parija", "CE"), ("F28", "Dr. AB. Padhi", "CE"),
        ("F29", "Prof. AC. Dalai", "CE"), ("F30", "Dr. AD. Sarangi", "CE"), ("F31", "Dr. AE. Mallick", "CE"), ("F32", "Prof. AF. Bisi", "CE"),
        ("F33", "Dr. AG. Paul", "EE"), ("F34", "Prof. AH. Ray", "EE"), ("F35", "Dr. AI. Dora", "EE"), ("F36", "Dr. AJ. Giri", "EE"),
        ("F37", "Dr. AK. Choudhury", "BS"), ("F38", "Prof. AL. Hota", "BS"), ("F39", "Dr. AM. Pothal", "BS"), ("F40", "Dr. AN. Muduli", "BS")
    ]

    faculty = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    for i, (fid, name, dept) in enumerate(faculty_names):
        # some unavailability and preferences
        unavail = []
        if i % 5 == 0:
            unavail.append({"day": days[i % 5], "periods": ["P1", "P2"]})
        if i % 7 == 0:
            unavail.append({"day": "Fri", "periods": ["P8", "P9"]})
        
        avoid = []
        if i % 3 == 0:
            avoid.append("P1")
        if i % 4 == 0:
            avoid.append("P9")

        faculty.append({
            "id": fid,
            "name": name,
            "department": dept,
            "daily_limit_hours": 4,
            "unavailability": unavail,
            "avoid_periods": avoid
        })

    # 3. STUDENT GROUPS (14)
    # 4 Year 1 (sections A to D), 5 Year 2 (branches), 5 Year 3 (branches)
    student_groups = [
        {"id": "Y1-A", "name": "First Year Section A", "year": 1, "size": 72, "accessible_required": False},
        {"id": "Y1-B", "name": "First Year Section B", "year": 1, "size": 70, "accessible_required": True}, # Needs accessible
        {"id": "Y1-C", "name": "First Year Section C", "year": 1, "size": 70, "accessible_required": False},
        {"id": "Y1-D", "name": "First Year Section D", "year": 1, "size": 68, "accessible_required": False},
        {"id": "Y2-CSE", "name": "Second Year CSE", "year": 2, "size": 65, "accessible_required": False},
        {"id": "Y2-ECE", "name": "Second Year ECE", "year": 2, "size": 65, "accessible_required": False},
        {"id": "Y2-ME", "name": "Second Year ME", "year": 2, "size": 64, "accessible_required": False},
        {"id": "Y2-CE", "name": "Second Year CE", "year": 2, "size": 62, "accessible_required": False},
        {"id": "Y2-EE", "name": "Second Year EE", "year": 2, "size": 62, "accessible_required": False},
        {"id": "Y3-CSE", "name": "Third Year CSE", "year": 3, "size": 60, "accessible_required": False},
        {"id": "Y3-ECE", "name": "Third Year ECE", "year": 3, "size": 60, "accessible_required": False},
        {"id": "Y3-ME", "name": "Third Year ME", "year": 3, "size": 58, "accessible_required": False},
        {"id": "Y3-CE", "name": "Third Year CE", "year": 3, "size": 56, "accessible_required": False},
        {"id": "Y3-EE", "name": "Third Year EE", "year": 3, "size": 58, "accessible_required": False}
    ]

    # 4. COURSES (62)
    courses = []
    # Y1 courses (10 courses)
    y1_codes = [
        ("MA101", "Linear Algebra & Calculus", "BS", 1),
        ("PH101", "Engineering Physics", "BS", 1),
        ("CH101", "Engineering Chemistry", "BS", 1),
        ("CS101", "Programming for Problem Solving", "CSE", 1),
        ("ME101", "Engineering Graphics & Workshop", "ME", 1),
        ("EE101", "Basic Electrical & Electronics", "EE", 1),
        ("HS101", "Communication Skills in English", "BS", 1),
        ("PH102", "Physics Lab", "BS", 1),
        ("CH102", "Chemistry Lab", "BS", 1),
        ("CS102", "Programming Lab", "CSE", 1)
    ]
    for code, name, dept, yr in y1_codes:
        courses.append({"code": code, "name": name, "department": dept, "year": yr, "credits": 3 if "Lab" not in name else 2})

    # Y2 core courses (5 depts * 5 courses = 25 courses)
    dept_y2 = {
        "CSE": [("CS201", "Data Structures"), ("CS202", "Computer Organization"), ("CS203", "Discrete Math"), ("CS204", "Object Oriented Java"), ("CS205", "Data Structures Lab")],
        "ECE": [("EC201", "Digital Electronics"), ("EC202", "Signals & Systems"), ("EC203", "Network Theory"), ("EC204", "Electromagnetic Fields"), ("EC205", "Digital Electronics Lab")],
        "ME": [("ME201", "Thermodynamics"), ("ME202", "Strength of Materials"), ("ME203", "Manufacturing Science"), ("ME204", "Fluid Mechanics"), ("ME205", "Manufacturing Lab")],
        "CE": [("CE201", "Surveying"), ("CE202", "Fluid Mechanics Civil"), ("CE203", "Solid Mechanics"), ("CE204", "Building Materials"), ("CE205", "Surveying Practice Lab")],
        "EE": [("EE201", "Electrical Machines I"), ("EE202", "Control Systems"), ("EE203", "Analog Electronics"), ("EE204", "Power Systems I"), ("EE205", "Electrical Machines Lab")]
    }
    for dept, clist in dept_y2.items():
        for code, name in clist:
            courses.append({"code": code, "name": name, "department": dept, "year": 2, "credits": 3 if "Lab" not in name else 2})

    # Y3 core & electives (5 depts * 5-6 courses = 27 courses) -> 10 + 25 + 27 = 62 courses!
    dept_y3 = {
        "CSE": [("CS301", "Operating Systems"), ("CS302", "Database Management Systems"), ("CS303", "Compiler Design"), ("CS304", "DBMS Lab"), ("CS305A", "Machine Learning (Elective)"), ("CS305B", "Cloud Computing (Elective)")],
        "ECE": [("EC301", "Microprocessors & Microcontrollers"), ("EC302", "Analog Communication"), ("EC303", "VLSI Design"), ("EC304", "Microcontroller Lab"), ("EC305A", "Digital Signal Processing (Elective)"), ("EC305B", "Optical Networks (Elective)")],
        "ME": [("ME301", "Heat Transfer"), ("ME302", "Design of Machine Elements"), ("ME303", "Kinematics of Machinery"), ("ME304", "Heat Transfer Lab"), ("ME305", "Automobile Engineering (Elective)")],
        "CE": [("CE301", "Structural Analysis"), ("CE302", "Geotechnical Engineering"), ("CE303", "Environmental Engineering"), ("CE304", "Geotech Lab"), ("CE305", "Transportation Engineering (Elective)")],
        "EE": [("EE301", "Electrical Machines II"), ("EE302", "Power Electronics"), ("EE303", "Microprocessors for EE"), ("EE304", "Power Electronics Lab"), ("EE305", "Renewable Energy Systems (Elective)")]
    }
    for dept, clist in dept_y3.items():
        for code, name in clist:
            courses.append({"code": code, "name": name, "department": dept, "year": 3, "credits": 3 if "Lab" not in name else 2})

    assert len(courses) == 62, f"Expected 62 courses, got {len(courses)}"

    # 5. SESSIONS TO SCHEDULE (189 sessions, 243 teaching hours)
    # Labs: exactly 27 labs * 3 hours = 81 hours
    # Combined / 2-hour lectures: 27 sessions * 2 hours = 54 hours
    # 1-hour lectures/tutorials: 135 sessions * 1 hour = 135 hours
    # Total sessions = 27 + 27 + 135 = 189 sessions!
    # Total hours = 81 + 54 + 108 = 243 hours! (Wait: 81 + 54 + 108 = 243 -> 27*3 + 27*2 + 108*1 = 243!)
    # Let's verify: 27 labs (81h) + 27 two-hour (54h) + 135 one-hour (135h) would be 270.
    # To get 189 sessions and 243 hours:
    # Let L = 3-hour sessions, D = 2-hour sessions, S = 1-hour sessions.
    # L + D + S = 189
    # 3*L + 2*D + 1*S = 243
    # Subtracting gives: 2*L + D = 54.
    # If L = 27 (the 3-hr labs), then 2*(27) + D = 54 => D = 0, S = 189 - 27 = 162.
    # 27*3 + 162*1 = 81 + 162 = 243 hours!
    # Exactly 27 3-hour labs (81h) + 162 1-hour sessions (162h) = 189 sessions, 243 hours!
    # OR: If L=21 (63h), D=12 (24h), S=156 (156h) -> 21+12+156 = 189, 63+24+156 = 243!
    # Let's check lab counts: 7 labs across 14 groups.
    # 27 3-hour lab sessions is natural and fits into the timetable!
    # Let L = 27 (three-hour labs), S = 162 (one-hour lectures/tutorials).
    # Total sessions = 189. Total hours = 27*3 + 162*1 = 81 + 162 = 243 hours.
    # Perfect!

    sessions = []
    sid_counter = 1

    # Generate 27 Lab Sessions (3 hours each = 81 hours)
    # Y1 labs: CS102 (CS lab), PH102 (Physics lab), CH102 (Chemistry lab) for sections A, B, C, D (12 lab sessions)
    lab_defs_y1 = [
        ("CS102", "computer_lab", ["F01", "F02", "F03", "F04"]),
        ("PH102", "physics_lab", ["F37", "F38", "F37", "F38"]),
        ("CH102", "chemistry_lab", ["F39", "F40", "F39", "F40"])
    ]
    for ccode, rtype, flist in lab_defs_y1:
        for idx, g in enumerate(["Y1-A", "Y1-B", "Y1-C", "Y1-D"]):
            sessions.append({
                "id": f"S{sid_counter:03d}",
                "course_code": ccode,
                "session_type": "lab",
                "duration_hours": 3,
                "required_room_type": rtype,
                "student_groups": [g],
                "faculty_ids": [flist[idx]],
                "accessible_required": (g == "Y1-B"),
                "elective_basket": None,
                "fixed_slot": None
            })
            sid_counter += 1

    # Y2 labs: 1 per branch (CS205, EC205, ME205, CE205, EE205) = 5 labs
    y2_lab_defs = [
        ("CS205", "computer_lab", "Y2-CSE", "F05"),
        ("EC205", "electrical_lab", "Y2-ECE", "F11"),
        ("ME205", "mechanical_lab", "Y2-ME", "F19"),
        ("CE205", "civil_lab", "Y2-CE", "F27"),
        ("EE205", "electrical_lab", "Y2-EE", "F35")
    ]
    for ccode, rtype, g, fid in y2_lab_defs:
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": ccode,
            "session_type": "lab",
            "duration_hours": 3,
            "required_room_type": rtype,
            "student_groups": [g],
            "faculty_ids": [fid],
            "accessible_required": False,
            "elective_basket": None,
            "fixed_slot": None
        })
        sid_counter += 1

    # Y3 labs: 2 per branch for CSE/ECE, 2 for ME/CE/EE = 10 labs -> 12 + 5 + 10 = 27 labs!
    y3_lab_defs = [
        ("CS304", "computer_lab", "Y3-CSE", "F06"),
        ("CS304", "computer_lab", "Y3-CSE", "F07"), # Project/Advanced Lab
        ("EC304", "electrical_lab", "Y3-ECE", "F12"),
        ("EC304", "electrical_lab", "Y3-ECE", "F13"),
        ("ME304", "mechanical_lab", "Y3-ME", "F20"),
        ("ME304", "mechanical_lab", "Y3-ME", "F21"),
        ("CE304", "civil_lab", "Y3-CE", "F28"),
        ("CE304", "civil_lab", "Y3-CE", "F29"),
        ("EE304", "electrical_lab", "Y3-EE", "F36"),
        ("EE304", "electrical_lab", "Y3-EE", "F33")
    ]
    for ccode, rtype, g, fid in y3_lab_defs:
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": ccode,
            "session_type": "lab",
            "duration_hours": 3,
            "required_room_type": rtype,
            "student_groups": [g],
            "faculty_ids": [fid],
            "accessible_required": False,
            "elective_basket": None,
            "fixed_slot": None
        })
        sid_counter += 1

    assert len(sessions) == 27, f"Expected 27 labs, got {len(sessions)}"

    # Now generate 162 one-hour lecture/tutorial sessions
    # Remaining to 189 is exactly 162.
    # Distribute among groups:
    # 14 groups. 162 / 14 ~ 11.5 sessions per group.
    # Let's create:
    # - Combined lectures for Y1: e.g. MA101, PH101 in Lecture Halls for (Y1-A, Y1-B) and (Y1-C, Y1-D)
    # - Core lectures for Y2 & Y3 branches
    # - Elective baskets for Y3 (e.g. CS305A and CS305B in basket 'BASKET-Y3-CSE')
    # - Some fixed slots
    
    # Y1 Combined Lectures:
    # MA101: 3 lectures for (Y1-A, Y1-B), 3 lectures for (Y1-C, Y1-D) = 6 sessions
    for pair, fid, acc in [([ "Y1-A", "Y1-B" ], "F37", True), ([ "Y1-C", "Y1-D" ], "F38", False)]:
        for l in range(3):
            sessions.append({
                "id": f"S{sid_counter:03d}",
                "course_code": "MA101",
                "session_type": "lecture",
                "duration_hours": 1,
                "required_room_type": "lecture_hall",
                "student_groups": pair,
                "faculty_ids": [fid],
                "accessible_required": acc,
                "elective_basket": None,
                "fixed_slot": {"day": "Mon", "period": "P2"} if (l == 0 and acc) else None # fixed slot sample
            })
            sid_counter += 1

    # PH101: 3 lectures for (Y1-A, Y1-B), 3 for (Y1-C, Y1-D) = 6 sessions
    for pair, fid, acc in [([ "Y1-A", "Y1-B" ], "F39", True), ([ "Y1-C", "Y1-D" ], "F40", False)]:
        for l in range(3):
            sessions.append({
                "id": f"S{sid_counter:03d}",
                "course_code": "PH101",
                "session_type": "lecture",
                "duration_hours": 1,
                "required_room_type": "lecture_hall",
                "student_groups": pair,
                "faculty_ids": [fid],
                "accessible_required": acc,
                "elective_basket": None,
                "fixed_slot": None
            })
            sid_counter += 1

    # CH101: 3 lectures for (Y1-A, Y1-B), 3 for (Y1-C, Y1-D) = 6 sessions
    for pair, fid, acc in [([ "Y1-A", "Y1-B" ], "F39", True), ([ "Y1-C", "Y1-D" ], "F40", False)]:
        for l in range(3):
            sessions.append({
                "id": f"S{sid_counter:03d}",
                "course_code": "CH101",
                "session_type": "lecture",
                "duration_hours": 1,
                "required_room_type": "lecture_hall",
                "student_groups": pair,
                "faculty_ids": [fid],
                "accessible_required": acc,
                "elective_basket": None,
                "fixed_slot": None
            })
            sid_counter += 1

    # Individual Y1 section courses: CS101 (2 lec + 1 tut), ME101 (2 lec), EE101 (2 lec), HS101 (1 tut)
    # Total per Y1 group = 5 + 3 = 8 sessions. For 4 groups = 32 sessions.
    y1_indiv = [
        ("CS101", "lecture", ["F01", "F02", "F03", "F04"]),
        ("CS101", "tutorial", ["F01", "F02", "F03", "F04"]),
        ("ME101", "lecture", ["F17", "F18", "F17", "F18"]),
        ("EE101", "lecture", ["F33", "F34", "F33", "F34"]),
        ("HS101", "tutorial", ["F37", "F38", "F37", "F38"])
    ]
    for ccode, stype, flist in y1_indiv:
        for idx, g in enumerate(["Y1-A", "Y1-B", "Y1-C", "Y1-D"]):
            sessions.append({
                "id": f"S{sid_counter:03d}",
                "course_code": ccode,
                "session_type": stype,
                "duration_hours": 1,
                "required_room_type": "classroom",
                "student_groups": [g],
                "faculty_ids": [flist[idx]],
                "accessible_required": (g == "Y1-B"),
                "elective_basket": None,
                "fixed_slot": None
            })
            sid_counter += 1

    # Y2 Core Sessions:
    # 5 branches (Y2-CSE, Y2-ECE, Y2-ME, Y2-CE, Y2-EE)
    # Each branch has 4 core courses. 3 sessions per course = 12 sessions per branch.
    # 5 * 12 = 60 sessions.
    y2_branch_courses = {
        "Y2-CSE": [("CS201", "F01"), ("CS202", "F02"), ("CS203", "F03"), ("CS204", "F04")],
        "Y2-ECE": [("EC201", "F09"), ("EC202", "F10"), ("EC203", "F11"), ("EC204", "F14")],
        "Y2-ME":  [("ME201", "F17"), ("ME202", "F18"), ("ME203", "F19"), ("ME204", "F22")],
        "Y2-CE":  [("CE201", "F25"), ("CE202", "F26"), ("CE203", "F27"), ("CE204", "F30")],
        "Y2-EE":  [("EE201", "F33"), ("EE202", "F34"), ("EE203", "F35"), ("EE204", "F36")]
    }
    for g, clist in y2_branch_courses.items():
        for ccode, fid in clist:
            for s_num in range(3):
                sessions.append({
                    "id": f"S{sid_counter:03d}",
                    "course_code": ccode,
                    "session_type": "lecture" if s_num < 2 else "tutorial",
                    "duration_hours": 1,
                    "required_room_type": "classroom",
                    "student_groups": [g],
                    "faculty_ids": [fid],
                    "accessible_required": False,
                    "elective_basket": None,
                    "fixed_slot": None
                })
                sid_counter += 1

    # Y3 Core & Elective Sessions:
    # Current session count so far: 27 labs + 18 combined + 20 indiv + 60 y2 = 125 sessions.
    # Target is 189 sessions. We need 189 - 125 = 64 sessions for Y3!
    # Y3 has 5 branches.
    # Let's allocate ~12-14 sessions per branch (core lectures + tutorials + elective baskets).
    y3_branch_courses = {
        "Y3-CSE": [("CS301", "F05", 3), ("CS302", "F06", 3), ("CS303", "F07", 3)], # 9 core sessions
        "Y3-ECE": [("EC301", "F13", 3), ("EC302", "F15", 3), ("EC303", "F16", 3)], # 9 core sessions
        "Y3-ME":  [("ME301", "F21", 3), ("ME302", "F23", 3), ("ME303", "F24", 3), ("ME305", "F18", 3)], # 12 core/el
        "Y3-CE":  [("CE301", "F29", 3), ("CE302", "F31", 3), ("CE303", "F32", 3), ("CE305", "F26", 3)], # 12 core/el
        "Y3-EE":  [("EE301", "F33", 3), ("EE302", "F34", 3), ("EE303", "F35", 3), ("EE305", "F36", 3)]  # 12 core/el
    }
    for g, clist in y3_branch_courses.items():
        for ccode, fid, count in clist:
            for s_num in range(count):
                sessions.append({
                    "id": f"S{sid_counter:03d}",
                    "course_code": ccode,
                    "session_type": "lecture" if s_num < 2 else "tutorial",
                    "duration_hours": 1,
                    "required_room_type": "classroom",
                    "student_groups": [g],
                    "faculty_ids": [fid],
                    "accessible_required": False,
                    "elective_basket": None,
                    "fixed_slot": None
                })
                sid_counter += 1

    # That added 9 + 9 + 12 + 12 + 12 = 54 sessions.
    # Total now: 125 + 54 = 179 sessions.
    # Remaining: 189 - 179 = 10 sessions!
    # These 10 sessions are the ELECTIVE BASKETS for Y3-CSE and Y3-ECE!
    # Basket 1: Y3-CSE (CS305A & CS305B) -> 3 slots * 2 sessions = 6 sessions
    # Basket 2: Y3-ECE (EC305A & EC305B) -> 2 slots * 2 sessions = 4 sessions
    # 6 + 4 = 10 sessions!
    for slot_idx in range(3):
        basket_id = f"BASKET-Y3-CSE-SLOT{slot_idx+1}"
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": "CS305A",
            "session_type": "lecture",
            "duration_hours": 1,
            "required_room_type": "classroom",
            "student_groups": ["Y3-CSE"],
            "faculty_ids": ["F07"],
            "accessible_required": False,
            "elective_basket": basket_id,
            "fixed_slot": None
        })
        sid_counter += 1
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": "CS305B",
            "session_type": "lecture",
            "duration_hours": 1,
            "required_room_type": "classroom",
            "student_groups": ["Y3-CSE"],
            "faculty_ids": ["F08"],
            "accessible_required": False,
            "elective_basket": basket_id,
            "fixed_slot": None
        })
        sid_counter += 1

    for slot_idx in range(2):
        basket_id = f"BASKET-Y3-ECE-SLOT{slot_idx+1}"
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": "EC305A",
            "session_type": "lecture",
            "duration_hours": 1,
            "required_room_type": "classroom",
            "student_groups": ["Y3-ECE"],
            "faculty_ids": ["F15"],
            "accessible_required": False,
            "elective_basket": basket_id,
            "fixed_slot": None
        })
        sid_counter += 1
        sessions.append({
            "id": f"S{sid_counter:03d}",
            "course_code": "EC305B",
            "session_type": "lecture",
            "duration_hours": 1,
            "required_room_type": "classroom",
            "student_groups": ["Y3-ECE"],
            "faculty_ids": ["F16"],
            "accessible_required": False,
            "elective_basket": basket_id,
            "fixed_slot": None
        })
        sid_counter += 1

    assert len(sessions) == 189, f"Expected 189 sessions, got {len(sessions)}"
    total_hours = sum(s["duration_hours"] for s in sessions)
    assert total_hours == 243, f"Expected 243 teaching hours, got {total_hours}"
    print(f"Verified: {len(sessions)} sessions, {total_hours} teaching hours!")

    # 6. MIDSEM EXAMS (41)
    # 41 exams for the courses, duration 2 hours
    exams = []
    # Pick 41 key lecture courses across years 1, 2, and 3
    exam_courses = [
        # Y1 (7 exams)
        ("MA101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("PH101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("CH101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("CS101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("ME101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("EE101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        ("HS101", ["Y1-A", "Y1-B", "Y1-C", "Y1-D"], 280),
        # Y2 CSE (4 exams)
        ("CS201", ["Y2-CSE"], 65), ("CS202", ["Y2-CSE"], 65), ("CS203", ["Y2-CSE"], 65), ("CS204", ["Y2-CSE"], 65),
        # Y2 ECE (4 exams)
        ("EC201", ["Y2-ECE"], 65), ("EC202", ["Y2-ECE"], 65), ("EC203", ["Y2-ECE"], 65), ("EC204", ["Y2-ECE"], 65),
        # Y2 ME (4 exams)
        ("ME201", ["Y2-ME"], 64), ("ME202", ["Y2-ME"], 64), ("ME203", ["Y2-ME"], 64), ("ME204", ["Y2-ME"], 64),
        # Y2 CE (4 exams)
        ("CE201", ["Y2-CE"], 62), ("CE202", ["Y2-CE"], 62), ("CE203", ["Y2-CE"], 62), ("CE204", ["Y2-CE"], 62),
        # Y2 EE (4 exams)
        ("EE201", ["Y2-EE"], 62), ("EE202", ["Y2-EE"], 62), ("EE203", ["Y2-EE"], 62), ("EE204", ["Y2-EE"], 62),
        # Y3 CSE (3 exams)
        ("CS301", ["Y3-CSE"], 60), ("CS302", ["Y3-CSE"], 60), ("CS303", ["Y3-CSE"], 60),
        # Y3 ECE (3 exams)
        ("EC301", ["Y3-ECE"], 60), ("EC302", ["Y3-ECE"], 60), ("EC303", ["Y3-ECE"], 60),
        # Y3 ME (3 exams)
        ("ME301", ["Y3-ME"], 58), ("ME302", ["Y3-ME"], 58), ("ME303", ["Y3-ME"], 58),
        # Y3 CE (3 exams)
        ("CE301", ["Y3-CE"], 56), ("CE302", ["Y3-CE"], 56), ("CE303", ["Y3-CE"], 56),
        # Y3 EE (2 exams) -> total 7 + 20 + 14 = 41 exams!
        ("EE301", ["Y3-EE"], 58), ("EE302", ["Y3-EE"], 58)
    ]
    assert len(exam_courses) == 41, f"Expected 41 exams, got {len(exam_courses)}"
    for idx, (ccode, grps, scount) in enumerate(exam_courses):
        exams.append({
            "id": f"EXAM{idx+1:02d}",
            "course_code": ccode,
            "student_groups": grps,
            "student_count": scount,
            "duration_hours": 2,
            "preferred_room_types": ["auditorium", "lecture_hall", "classroom"]
        })

    # 7. SPECTRA WEEK BOOKING REQUESTS (25)
    # Original message texts in English and Hinglish
    # 1 cancelled request (BK25)
    bookings = [
        {"id": "BK01", "requester_name": "Spectra Core Committee", "requester_role": "club", "category": "institute_event", "title": "Spectra Opening Ceremony", "original_text": "Need Auditorium for grand inaugural event of Spectra fest on Wednesday afternoon.", "day": "Wed", "start_period": "P6", "end_period": "P8", "preferred_room": "AUD", "required_room_type": "auditorium", "expected_attendance": 350, "features_needed": ["stage", "sound_system", "projector"]},
        {"id": "BK02", "requester_name": "Robotics Club", "requester_role": "club", "category": "club_event", "title": "RoboWars Arena Setup", "original_text": "OAT chahiye Friday dopahar RoboWars competition ke liye with sound setup.", "day": "Fri", "start_period": "P7", "end_period": "P9", "preferred_room": "OAT", "required_room_type": "open_air_theatre", "expected_attendance": 250, "features_needed": ["stage", "sound_system"]},
        {"id": "BK03", "requester_name": "Dr. A. Sharma", "requester_role": "faculty", "category": "guest_lecture", "title": "Distinguished AI Lecture", "original_text": "Seminar Hall 1 required on Tuesday 10 AM for visiting professor from IIT.", "day": "Tue", "start_period": "P3", "end_period": "P4", "preferred_room": "SH-1", "required_room_type": "seminar_hall", "expected_attendance": 120, "features_needed": ["projector", "ac"]},
        {"id": "BK04", "requester_name": "Coding Club", "requester_role": "club", "category": "club_event", "title": "24-Hour Hackathon Pre-Briefing", "original_text": "Bhai evening me Computing Lab 1 book kar do for 2 hours (18:00 to 20:00).", "day": "Thu", "start_period": "P10", "end_period": "P11", "preferred_room": "LAB-CS1", "required_room_type": "computer_lab", "expected_attendance": 60, "features_needed": ["computers"]},
        {"id": "BK05", "requester_name": "ECE Dept Coordinator", "requester_role": "coordinator", "category": "department_event", "title": "ECE Alumni Interaction", "original_text": "We need Seminar Hall 2 on Thursday P3-P4 for department alumni talk.", "day": "Thu", "start_period": "P3", "end_period": "P4", "preferred_room": "SH-2", "required_room_type": "seminar_hall", "expected_attendance": 100, "features_needed": ["projector"]},
        {"id": "BK06", "requester_name": "Music Society", "requester_role": "club", "category": "club_event", "title": "Acoustic Night Rehearsal", "original_text": "OAT book kar do Thursday evening P10 to P12 music rehearsal ke liye.", "day": "Thu", "start_period": "P10", "end_period": "P12", "preferred_room": "OAT", "required_room_type": "open_air_theatre", "expected_attendance": 80, "features_needed": ["stage"]},
        {"id": "BK07", "requester_name": "Dean Student Affairs", "requester_role": "admin", "category": "institute_event", "title": "Inter-College Debate Finals", "original_text": "Seminar Hall 1 is needed on Monday 14:00-16:00 (P6-P7) for National Debate.", "day": "Mon", "start_period": "P6", "end_period": "P7", "preferred_room": "SH-1", "required_room_type": "seminar_hall", "expected_attendance": 140, "features_needed": ["ac", "sound_system"]},
        {"id": "BK08", "requester_name": "Literary Club", "requester_role": "club", "category": "club_event", "title": "Poetry Slam", "original_text": "CR-1 or CR-2 chahiye Tuesday evening P10-P11 for open mic.", "day": "Tue", "start_period": "P10", "end_period": "P11", "preferred_room": "CR-1", "required_room_type": "classroom", "expected_attendance": 45, "features_needed": ["projector"]},
        {"id": "BK09", "requester_name": "Mech Dept Coordinator", "requester_role": "coordinator", "category": "department_event", "title": "CAD Design Showcase", "original_text": "Mechanical workshop required on Wednesday morning P2-P4.", "day": "Wed", "start_period": "P2", "end_period": "P4", "preferred_room": "LAB-ME", "required_room_type": "mechanical_lab", "expected_attendance": 50, "features_needed": ["lathes"]},
        {"id": "BK10", "requester_name": "Dance Club", "requester_role": "club", "category": "club_event", "title": "Spectra Dance Troupe Practice", "original_text": "Auditorium stage chahiye Monday P10-P12 for dance rehearsal.", "day": "Mon", "start_period": "P10", "end_period": "P12", "preferred_room": "AUD", "required_room_type": "auditorium", "expected_attendance": 30, "features_needed": ["stage"]},
        {"id": "BK11", "requester_name": "Dr. I. Jena", "requester_role": "faculty", "category": "guest_lecture", "title": "Semiconductor Industry Roadmap", "original_text": "Lecture Hall 1 requested on Friday P3-P4 for Intel guest speaker.", "day": "Fri", "start_period": "P3", "end_period": "P4", "preferred_room": "LH-1", "required_room_type": "lecture_hall", "expected_attendance": 110, "features_needed": ["projector"]},
        {"id": "BK12", "requester_name": "Photography Club", "requester_role": "club", "category": "club_event", "title": "Annual Photo Exhibition", "original_text": "Seminar Hall 2 corridor and hall on Wednesday P6-P8.", "day": "Wed", "start_period": "P6", "end_period": "P8", "preferred_room": "SH-2", "required_room_type": "seminar_hall", "expected_attendance": 90, "features_needed": ["ac"]},
        {"id": "BK13", "requester_name": "Civil Dept Coordinator", "requester_role": "coordinator", "category": "department_event", "title": "Smart Cities Workshop", "original_text": "Lecture Hall 3 for Civil department workshop on Thursday P6-P8.", "day": "Thu", "start_period": "P6", "end_period": "P8", "preferred_room": "LH-3", "required_room_type": "lecture_hall", "expected_attendance": 80, "features_needed": ["projector"]},
        {"id": "BK14", "requester_name": "Spectra Tech Team", "requester_role": "club", "category": "club_event", "title": "LAN Gaming Tournament - Valorant", "original_text": "Computing Lab 2 chahiye Friday shaam 17:00 se 21:00 (P9 to P12).", "day": "Fri", "start_period": "P9", "end_period": "P12", "preferred_room": "LAB-CS2", "required_room_type": "computer_lab", "expected_attendance": 70, "features_needed": ["computers"]},
        {"id": "BK15", "requester_name": "Dr. Q. Biswal", "requester_role": "faculty", "category": "guest_lecture", "title": "Electric Mobility Trends", "original_text": "Seminar Hall 1 on Wednesday P2-P3 for Tata Motors Tech talk.", "day": "Wed", "start_period": "P2", "end_period": "P3", "preferred_room": "SH-1", "required_room_type": "seminar_hall", "expected_attendance": 130, "features_needed": ["sound_system"]},
        {"id": "BK16", "requester_name": "Dramatics Society", "requester_role": "club", "category": "club_event", "title": "Street Play Rehearsal", "original_text": "OAT chahiye Tuesday subah P1-P2 play practice ke liye.", "day": "Tue", "start_period": "P1", "end_period": "P2", "preferred_room": "OAT", "required_room_type": "open_air_theatre", "expected_attendance": 40, "features_needed": ["stage"]},
        {"id": "BK17", "requester_name": "Training & Placement Cell", "requester_role": "admin", "category": "institute_event", "title": "Campus Placement Drive - Amazon", "original_text": "Auditorium required on Tuesday full morning P1-P5 for PPT and online test briefing.", "day": "Tue", "start_period": "P1", "end_period": "P5", "preferred_room": "AUD", "required_room_type": "auditorium", "expected_attendance": 380, "features_needed": ["projector", "sound_system"]},
        {"id": "BK18", "requester_name": "IEEE Student Branch", "requester_role": "club", "category": "club_event", "title": "PCB Design Hands-on Workshop", "original_text": "Electrical Lab chahiye Saturday ya Friday shaam P8-P9.", "day": "Fri", "start_period": "P8", "end_period": "P9", "preferred_room": "LAB-EE", "required_room_type": "electrical_lab", "expected_attendance": 50, "features_needed": ["oscilloscopes"]},
        {"id": "BK19", "requester_name": "Dr. Y. Khatua", "requester_role": "faculty", "category": "guest_lecture", "title": "Seismic Disaster Mitigation", "original_text": "Lecture Hall 2 on Monday P8-P9 for Guest Lecture from NDMA.", "day": "Mon", "start_period": "P8", "end_period": "P9", "preferred_room": "LH-2", "required_room_type": "lecture_hall", "expected_attendance": 100, "features_needed": ["projector"]},
        {"id": "BK20", "requester_name": "Sports Committee", "requester_role": "club", "category": "club_event", "title": "Spectra Chess Championship", "original_text": "Classroom CR-3 chahiye Thursday P6-P8 for chess matches.", "day": "Thu", "start_period": "P6", "end_period": "P8", "preferred_room": "CR-3", "required_room_type": "classroom", "expected_attendance": 40, "features_needed": ["ac"]},
        {"id": "BK21", "requester_name": "EE Dept Coordinator", "requester_role": "coordinator", "category": "department_event", "title": "Smart Grid Demo", "original_text": "Seminar Hall 2 on Tuesday P6-P7 for department project demos.", "day": "Tue", "start_period": "P6", "end_period": "P7", "preferred_room": "SH-2", "required_room_type": "seminar_hall", "expected_attendance": 80, "features_needed": ["projector"]},
        {"id": "BK22", "requester_name": "Spectra Core Committee", "requester_role": "club", "category": "institute_event", "title": "Star Night Musical Band", "original_text": "Open Air Theatre on Friday 18:00 to 22:00 (P10 to P13) for celebrity band night.", "day": "Fri", "start_period": "P10", "end_period": "P13", "preferred_room": "OAT", "required_room_type": "open_air_theatre", "expected_attendance": 550, "features_needed": ["stage", "sound_system"]},
        {"id": "BK23", "requester_name": "Astronomy Club", "requester_role": "club", "category": "club_event", "title": "Night Sky Observation", "original_text": "OAT on Wednesday evening P11-P13 for telescope viewing.", "day": "Wed", "start_period": "P11", "end_period": "P13", "preferred_room": "OAT", "required_room_type": "open_air_theatre", "expected_attendance": 70, "features_needed": []},
        {"id": "BK24", "requester_name": "Dr. AK. Choudhury", "requester_role": "faculty", "category": "guest_lecture", "title": "Quantum Mechanics & Computing", "original_text": "Seminar Hall 1 on Thursday P7-P8 for Physics Colloquium.", "day": "Thu", "start_period": "P7", "end_period": "P8", "preferred_room": "SH-1", "required_room_type": "seminar_hall", "expected_attendance": 90, "features_needed": ["projector"]},
        {"id": "BK25", "requester_name": "Fine Arts Club", "requester_role": "club", "category": "club_event", "title": "Origami Workshop (Cancelled)", "original_text": "CR-5 on Wednesday P3-P4. Please note this request has been cancelled by the club.", "day": "Wed", "start_period": "P3", "end_period": "P4", "preferred_room": "CR-5", "required_room_type": "classroom", "expected_attendance": 30, "features_needed": [], "status": "cancelled"}
    ]
    assert len(bookings) == 25, f"Expected 25 booking requests, got {len(bookings)}"

    dataset = {
        "metadata": {
            "institution": "Chilika Institute of Technology",
            "version": "1.0.0",
            "academic_year": "2026-2027",
            "semester": "Odd",
            "teaching_week": 7
        },
        "rooms": rooms,
        "faculty": faculty,
        "student_groups": student_groups,
        "courses": courses,
        "sessions": sessions,
        "exams": exams,
        "booking_requests": bookings
    }

    # Write cit_public.json to starter-pack and data
    for path in ['starter-pack/cit_public.json', 'data/cit_public.json']:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)
    print("Saved cit_public.json to starter-pack/ and data/")

    # Generate CSV files in starter-pack/csv/
    os.makedirs('starter-pack/csv', exist_ok=True)
    os.makedirs('data/csv', exist_ok=True)

    # rooms.csv
    for folder in ['starter-pack/csv', 'data/csv']:
        with open(f'{folder}/rooms.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "type", "capacity", "accessible", "features"])
            writer.writeheader()
            for r in rooms:
                writer.writerow({
                    "id": r["id"],
                    "name": r["name"],
                    "type": r["type"],
                    "capacity": r["capacity"],
                    "accessible": r["accessible"],
                    "features": ";".join(r["features"])
                })

        with open(f'{folder}/faculty.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "department", "daily_limit_hours", "avoid_periods"])
            writer.writeheader()
            for fac in faculty:
                writer.writerow({
                    "id": fac["id"],
                    "name": fac["name"],
                    "department": fac["department"],
                    "daily_limit_hours": fac["daily_limit_hours"],
                    "avoid_periods": ";".join(fac["avoid_periods"])
                })

        with open(f'{folder}/student_groups.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "year", "size", "accessible_required"])
            writer.writeheader()
            for g in student_groups:
                writer.writerow(g)

        with open(f'{folder}/courses.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["code", "name", "department", "year", "credits"])
            writer.writeheader()
            for c in courses:
                writer.writerow(c)

        with open(f'{folder}/sessions.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "course_code", "session_type", "duration_hours", "required_room_type", "student_groups", "faculty_ids", "accessible_required", "elective_basket"])
            writer.writeheader()
            for s in sessions:
                writer.writerow({
                    "id": s["id"],
                    "course_code": s["course_code"],
                    "session_type": s["session_type"],
                    "duration_hours": s["duration_hours"],
                    "required_room_type": s["required_room_type"],
                    "student_groups": ";".join(s["student_groups"]),
                    "faculty_ids": ";".join(s["faculty_ids"]),
                    "accessible_required": s["accessible_required"],
                    "elective_basket": s["elective_basket"] or ""
                })

    # Sample disruption
    sample_disruption = {
        "disruptions": [
            {
                "id": "DISRUPT-01",
                "type": "faculty_leave",
                "faculty_id": "F03",
                "day": "Tue",
                "start_period": "P1",
                "end_period": "P4",
                "reason": "Medical leave for Dr. C. Patra"
            },
            {
                "id": "DISRUPT-02",
                "type": "room_closure",
                "room_id": "CR-2",
                "day": "Thu",
                "start_period": "P1",
                "end_period": "P9",
                "reason": "Emergency roof ceiling and electrical maintenance"
            },
            {
                "id": "DISRUPT-03",
                "type": "new_session",
                "session": {
                    "id": "S_NEW_01",
                    "course_code": "CS301",
                    "session_type": "lecture",
                    "duration_hours": 1,
                    "required_room_type": "classroom",
                    "student_groups": ["Y3-CSE"],
                    "faculty_ids": ["F05"],
                    "accessible_required": False
                },
                "reason": "Extra makeup lecture on Operating Systems before midsems"
            }
        ]
    }
    with open('starter-pack/sample_disruption.json', 'w', encoding='utf-8') as f:
        json.dump(sample_disruption, f, indent=2)
    with open('data/sample_disruption.json', 'w', encoding='utf-8') as f:
        json.dump(sample_disruption, f, indent=2)

    print("Created sample_disruption.json")

if __name__ == '__main__':
    generate()
