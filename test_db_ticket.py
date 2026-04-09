import asyncio
from database import get_pool
import base64

async def main():
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM withdrawals ORDER BY created_at DESC LIMIT 1")
    
    if row:
        ticket = dict(row)
        print(f"Latest Ticket ID: {ticket['id']}")
        print(f"Destination: {ticket['stellar_address']}")
        print(f"Amount: {ticket['amount']}")
        print(f"Nonce: {ticket['nonce']}")
        sig = ticket.get('signature')
        print(f"Signature length: {len(sig) if sig else 0}")
        if sig:
            print(f"Signature: {sig[:40]}...")
            
            # Reconstruct and verify
            import stellar_utils as stellar
            
            test_sig = stellar.sign_withdrawal(ticket['stellar_address'], ticket['amount'], ticket['nonce'])
            print(f"Locally signed (b64): {test_sig[:40]}...")
            
            # Print hexes for comparison
            try:
                ticket_hex = base64.b64decode(sig).hex()
                print(f"Ticket Hex: {ticket_hex[:40]}...")
            except Exception as e:
                print(f"Failed to decode ticket signature: {e}")
                    
            test_hex = base64.b64decode(test_sig).hex()
            print(f"Test Hex:   {test_hex[:40]}...")
            
            if test_sig == sig:
                print("\n✅ MATCHES NEW STYLE A perfectly!")
                print("This means the bot generated the ticket using the correct, up-to-date code.")
            else:
                print("\n❌ MISMATCH!")
                print("The db ticket was NOT signed using the updated code.")
                print("This means the bot was running an older version when this ticket was created.")
    else:
        print("No tickets found.")

if __name__ == "__main__":
    asyncio.run(main())
