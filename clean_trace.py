LOG = """\n                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.UndefinedColumnError: column "expires_at" of relation "airdrops" does not exist

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\tree.py", line 1302, in _call
    await command._invoke_with_namespace(interaction, namespace)
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\commands.py", line 884, in _invoke_with_namespace
    return await self._do_call(interaction, transformed_values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\commands.py", line 877, in _do_call
    raise CommandInvokeError(self, e) from e
discord.app_commands.errors.CommandInvokeError: Command 'airdrop' raised an exception: UndefinedColumnError: column "expires_at" of relation "airdrops" does not exist
2026-03-24 23:11:13,600 | shx_tip_bot | INFO | Closing bot and cleaning up resources...
2026-03-24 23:11:13,756 | shx_tip_bot.database | INFO | Database connection pool closed.
2026-03-24 23:11:48,166 | shx_tip_bot | INFO | Bot online as SHxTipBot#1167 (ID: 1479701624334057512)
2026-03-24 23:11:48,173 | shx_tip_bot | INFO | Guild: 1480437856773210183 | Network: testnet
2026-03-24 23:11:49,773 | shx_tip_bot.database | INFO | Database connection pool established.
2026-03-24 23:11:51,215 | shx_tip_bot.database | INFO | Database initialized successfully.
2026-03-24 23:11:51,421 | shx_tip_bot | INFO | Synced 7 guild slash commands.
2026-03-24 23:11:51,626 | shx_tip_bot | INFO | Cleared global slash commands.
2026-03-24 23:11:51,628 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 146.43ms
2026-03-24 23:11:51,630 | shx_tip_bot.stellar | INFO | Starting deposit monitor for GAHO2LQH... from cursor now
2026-03-24 23:12:27,161 | shx_tip_bot | INFO | COMMAND | /airdrop | User: limpy37 Total: 17 Claims: 6 Mins: 29
2026-03-24 23:13:01,301 | shx_tip_bot | INFO | COMMAND | /tip | From: limpy37 To: cube.g | Amount: 106
2026-03-24 23:14:19,734 | shx_tip_bot | INFO | COMMAND | /tip | From: limpy37 To: cube.g | Amount: $1
2026-03-24 23:14:57,324 | shx_tip_bot | INFO | COMMAND | /balance | User: cube.g (866491211182505985)
2026-03-24 23:19:30,012 | shx_tip_bot | INFO | COMMAND | /airdrop | User: cube.g Total: 106 Claims: 8 Mins: None
2026-03-24 23:26:51,685 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 141.92ms
2026-03-24 23:27:30,551 | shx_tip_bot | INFO | COMMAND | /link | User: cube.g (866491211182505985)
2026-03-24 23:34:47,166 | shx_tip_bot | INFO | COMMAND | /airdrop | User: cube.g Total: 100 Claims: 7 Mins: 1440
2026-03-24 23:41:51,768 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 142.30ms
2026-03-24 23:43:36,268 | shx_tip_bot | INFO | Closing bot and cleaning up resources...
2026-03-24 23:43:36,299 | shx_tip_bot.database | INFO | Database connection pool closed.
2026-03-24 23:47:00,927 | shx_tip_bot | INFO | Bot online as SHxTipBot#1167 (ID: 1479701624334057512)
2026-03-24 23:47:00,930 | shx_tip_bot | INFO | Guild: 1480437856773210183 | Network: testnet
2026-03-24 23:47:03,334 | shx_tip_bot.database | INFO | Database connection pool established.
2026-03-24 23:47:04,796 | shx_tip_bot.database | INFO | Database initialized successfully.
2026-03-24 23:47:05,032 | shx_tip_bot | INFO | Synced 7 guild slash commands.
2026-03-24 23:47:05,281 | shx_tip_bot | INFO | Cleared global slash commands.
2026-03-24 23:47:05,284 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 137.48ms
2026-03-24 23:47:05,286 | shx_tip_bot.stellar | INFO | Starting deposit monitor for GAHO2LQH... from cursor now
2026-03-24 23:47:29,728 | shx_tip_bot | INFO | COMMAND | /balance | User: cube.g (866491211182505985)
2026-03-25 00:02:05,303 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 140.79ms
2026-03-25 00:10:06,219 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 00:15:08,384 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 00:17:02,105 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 00:17:05,376 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 130.61ms
\n"""