import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB", "faceattend")


async def migrate():
    client = AsyncIOMotorClient(MONGO_URI)
    db     = client[DB_NAME]

    # Count students with existing embeddings
    total = await db["students"].count_documents({"face_encoding": {"$exists": True, "$ne": None}})
    print(f"Found {total} students with existing face embeddings.")

    if total == 0:
        print("Nothing to migrate. Exiting.")
        return

    confirm = input(
        f"\n⚠️  This will clear face_encoding for {total} students.\n"
        f"They will need to re-enroll via the video enrollment feature.\n"
        f"Type 'yes' to confirm: "
    ).strip()

    if confirm.lower() != "yes":
        print("Aborted.")
        return

    result = await db["students"].update_many(
        {"face_encoding": {"$exists": True}},
        {"$unset": {"face_encoding": ""}}
    )

    print(f"✅ Cleared face_encoding from {result.modified_count} student documents.")
    print("Students will be prompted to re-enroll on next login.")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
