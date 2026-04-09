import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def finalize_claims():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 1. Update the 25 SHx claim
        # hash: dbe8cad9a5767a3b552efe6a5de8fd371bbdb3bdb96b3f9f48081ae9a8b51e4d
        # id: 0da858282aa288bfea77a87899bdf549
        print("Finishing 25 SHx claim...")
        await conn.execute(
            "UPDATE withdrawals SET status = 'COMPLETED', tx_hash = $1 WHERE id = $2",
            "dbe8cad9a5767a3b552efe6a5de8fd371bbdb3bdb96b3f9f48081ae9a8b51e4d",
            "0da858282aa288bfea77a87899bdf549"
        )
        
        # 2. Update the 100 SHx claim
        # hash: f3c1e9e68034628615e30701d309affcc0433845499daa3ab8d350d9014062f8
        # id: 2a207d8adc3f964f16af11595884dad7
        print("Finishing 100 SHx claim...")
        await conn.execute(
            "UPDATE withdrawals SET status = 'COMPLETED', tx_hash = $1 WHERE id = $2",
            "f3c1e9e68034628615e30701d309affcc0433845499daa3ab8d350d9014062f8",
            "2a207d8adc3f964f16af11595884dad7"
        )
        
        print("DONE. Database successfully updated.")
        await conn.close()
    except Exception as e:
        print(f"Error finalizing claims: {e}")

if __name__ == "__main__":
    asyncio.run(finalize_claims())
