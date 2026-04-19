import pandas as pd
import random

def inject_dummy_data():
    # 1. Realistic Student Names/IDs for a Philippines-based context
    students = [
        {"id": "2023-0001", "name": "Juan Dela Cruz"},
        {"id": "2023-0002", "name": "Maria Santos"},
        {"id": "2023-0003", "name": "Jose Rizalino"},
        {"id": "2023-0004", "name": "Elena Garcia"},
        {"id": "2023-0005", "name": "Ricardo Dalisay"},
        {"id": "2023-0006", "name": "Liza Soberano"},
        {"id": "2023-0007", "name": "Antonio Luna"},
        {"id": "2023-0008", "name": "Teresa Magbanua"},
        {"id": "2023-0009", "name": "Ferdinand Magellan"},
        {"id": "2023-0010", "name": "Corazon Aquino"},
        {"id": "2023-0011", "name": "Benigno Ramos"},
        {"id": "2023-0012", "name": "Gabriela Silang"},
        {"id": "2023-0013", "name": "Emilio Aguinaldo"},
        {"id": "2023-0014", "name": "Melchora Aquino"},
        {"id": "2023-0015", "name": "Lapu-Lapu Dimagiba"}
    ]

    for student in students:
        # Create different "types" of students for your Confusion Matrix
        seed = random.random()
        
        if seed < 0.2: # The "At Risk" Student (High Absences, Low Grades)
            absents = random.randint(3, 5)
            quiz = random.randint(50, 70)
            exam = random.randint(50, 70)
        elif seed < 0.4: # The "Lazy Genius" (High Absences, High Grades)
            absents = random.randint(3, 4)
            quiz = random.randint(85, 95)
            exam = random.randint(85, 95)
        else: # The "Stable" Student (Low Absences, Passing Grades)
            absents = random.randint(0, 2)
            quiz = random.randint(75, 90)
            exam = random.randint(75, 95)

        # Participation is calculated based on our new 4-session rule
        participation = ((4 - absents) / 4) * 100
        participation = max(0, participation)

        # Final DB Weighted Grade calculation
        weighted = (participation * 0.2) + (quiz * 0.2) + (quiz * 0.2) + (exam * 0.4)

        # Insert into Supabase (Ensure your table name matches)
        data = {
            "student_id": student["id"],
            "absent_count": absents,
            "participation_score": participation,
            "assignment_score": quiz, # reusing quiz for simplicity
            "quiz_score": quiz,
            "exam_score": exam,
            "total_weighted_grade": weighted
        }

        # Use upsert so it updates them if they already exist
        supabase.table("student_analytics").upsert(data).execute()

    print("✅ 15 Students Injected successfully!")

# To run it, just call the function:
# inject_dummy_data()