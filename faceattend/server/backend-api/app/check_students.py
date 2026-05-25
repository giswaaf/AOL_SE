import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smart-attendance")
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database()

async def run():
    students = await db.students.find({}).to_list(None)
    print(f"Found {len(students)} students in DB.")
    
    if not students:
        return
        
    student = students[0]
    print(f"Student: {student.get('name')} (UserId: {student.get('userId')})")
    
    subjects = await db.subjects.find({}).to_list(None)
    print(f"Found {len(subjects)} subjects in DB.")
    
    if not subjects:
        return
        
    # Enroll the student in the first 5 subjects
    for subj in subjects[:5]:
        subj_id = subj["_id"]
        # Check if already enrolled
        already_enrolled = any(s.get("student_id") == student["userId"] for s in subj.get("students", []))
        if not already_enrolled:
            await db.students.update_one(
                {"_id": student["_id"]},
                {"$addToSet": {"subjects": subj_id}}
            )
            await db.subjects.update_one(
                {"_id": subj_id},
                {"$push": {
                    "students": {
                        "student_id": student["userId"],
                        "name": student.get("name", "Unknown"),
                        "verified": True,
                        "attendance": {
                            "present": 0,
                            "absent": 0,
                            "total": 0,
                            "percentage": 0
                        }
                    }
                }}
            )
            print(f"Enrolled student in subject: {subj.get('name')}")
        else:
            print(f"Student already enrolled in subject: {subj.get('name')}")

if __name__ == "__main__":
    asyncio.run(run())
