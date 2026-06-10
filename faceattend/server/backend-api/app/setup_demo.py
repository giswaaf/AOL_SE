import httpx
import asyncio

BASE_URL = "http://localhost:8000/api"

async def run():
    async with httpx.AsyncClient() as client:
        print("Creating Teacher...")
        res = await client.post(f"{BASE_URL}/auth/register", json={
            "name": "Demo Teacher",
            "email": "demo_teacher@test.com",
            "password": "password123",
            "role": "teacher",
            "college_name": "Test College",
            "employee_id": "T001",
            "phone": "1234567890",
            "branch": "CS"
        })
        print("Teacher Register:", res.status_code)
        
        print("Logging in Teacher...")
        res = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "demo_teacher@test.com",
            "password": "password123"
        })
        t_token = res.json().get("token")
        
        print("Adding Subject...")
        res = await client.post(f"{BASE_URL}/settings/add-subject", json={
            "name": "Demo Math 101",
            "code": "M101"
        }, headers={"Authorization": f"Bearer {t_token}"})
        subject_id = res.json().get("subject_id") or res.json().get("_id")
        if not subject_id:
            print("Failed to get subject id:", res.text)
            return
        
        print("Creating Student...")
        res = await client.post(f"{BASE_URL}/auth/register", json={
            "name": "Demo Student",
            "email": "demo_student@test.com",
            "password": "password123",
            "role": "student",
            "college_name": "Test College",
            "roll": "S001",
            "year": "1",
            "branch": "CS"
        })
        print("Student Register:", res.status_code)
        
        print("Logging in Student...")
        res = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "demo_student@test.com",
            "password": "password123"
        })
        s_token = res.json().get("token")
        
        print("Enrolling Student...")
        res = await client.post(f"{BASE_URL}/students/me/subjects?subject_id={subject_id}", headers={
            "Authorization": f"Bearer {s_token}"
        })
        print("Enrollment:", res.status_code)
        
        print("Uploading Face Image...")
        with open("/Users/darrisfelicio/Documents/Face_Attendance/obama.jpg", "rb") as f:
            file_content = f.read()
        res = await client.post(f"{BASE_URL}/students/me/face-image", headers={
            "Authorization": f"Bearer {s_token}"
        }, files={"file": ("obama.jpg", file_content, "image/jpeg")})
        print("Face Upload:", res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(run())
