import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId

# Setup MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smart-attendance")
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database()

MAJORS = {
    "SE": [
        ("Software Architecture", "SE101"),
        ("Agile Methodologies", "SE102"),
        ("Software Testing", "SE103"),
        ("Requirements Engineering", "SE104"),
        ("DevOps and CI/CD", "SE105")
    ],
    "CS": [
        ("Data Structures", "CS101"),
        ("Algorithms", "CS102"),
        ("Operating Systems", "CS103"),
        ("Computer Networks", "CS104"),
        ("Artificial Intelligence", "CS105")
    ],
    "IT": [
        ("Database Management", "IT101"),
        ("Web Development", "IT102"),
        ("Cybersecurity", "IT103"),
        ("Cloud Computing", "IT104"),
        ("System Administration", "IT105")
    ]
}

async def seed():
    # Find the teacher
    teacher = await db.teachers.find_one({})
    if not teacher:
        print("No teacher found in database! Please create a teacher account first.")
        return
    
    teacher_id = teacher.get("userId") or teacher.get("user_id")
    print(f"Adding subjects for teacher ID: {teacher_id}")
    
    for major, subjects in MAJORS.items():
        for name, code in subjects:
            # Check if subject exists
            existing = await db.subjects.find_one({"code": code})
            if existing:
                subj_id = existing["_id"]
                if teacher_id not in existing.get("professor_ids", []):
                    await db.subjects.update_one({"_id": subj_id}, {"$addToSet": {"professor_ids": teacher_id}})
            else:
                result = await db.subjects.insert_one({
                    "name": name,
                    "code": code,
                    "professor_ids": [teacher_id],
                    "students": [],
                    "location": None
                })
                subj_id = result.inserted_id
            
            # Add to teacher's subjects list
            await db.teachers.update_one(
                {"_id": teacher["_id"]},
                {"$addToSet": {"subjects": subj_id}}
            )
            print(f"Added {major} subject: {name} ({code})")

    print("Successfully seeded subjects!")

if __name__ == "__main__":
    asyncio.run(seed())
