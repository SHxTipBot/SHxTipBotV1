import asyncio
import database as db
import requests

async def test_unlink():
    await db.init_db()
    # 1. Create a user and link them
    discord_id = "99999999999999999"
    await db.get_or_create_user(discord_id)
    await db.link_user(discord_id, "GABC1234567890123456789012345678901234567890123456789012")
    
    # 2. Check if linked
    user = await db.get_user_link_details(discord_id)
    print(f"Initial state: {user}")
    
    # 3. Create a token
    token = await db.create_link_token(discord_id)
    print(f"Token created: {token}")
    
    # 4. Call the unlink function directly (matching web.py logic)
    print("Calling unlink_user...")
    await db.unlink_user(discord_id)
    
    # 5. Check result
    user = await db.get_user_link_details(discord_id)
    print(f"Final state: {user}")
    
    if user['stellar_public_key'] is None and user['is_approved'] is False:
        print("SUCCESS: Wallet unlinked correctly in database.")
    else:
        print("FAILURE: Wallet still linked.")

if __name__ == "__main__":
    asyncio.run(test_unlink())
