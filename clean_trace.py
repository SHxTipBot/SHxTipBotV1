LOG = """\n2026-03-25 20:57:07,873 | shx_tip_bot | INFO | COMMAND | /airdrop | User: limpy37 Total: 18 Claims: 8 Mins: 1 Hrs: None Days: 1
2026-03-25 21:00:14,276 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 21:06:59,703 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 143.15ms
2026-03-25 21:10:58,739 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 21:21:59,758 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 135.84ms
2026-03-25 21:26:35,112 | shx_tip_bot | INFO | COMMAND | /link | User: limpy37 (768342085644320799)
2026-03-25 21:26:50,394 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:27:11,635 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:27:21,271 | shx_tip_bot | INFO | COMMAND | /balance | User: dogegecko (887682978392702997)
2026-03-25 21:29:26,766 | shx_tip_bot | INFO | COMMAND | /withdraw | User: dogegecko (887682978392702997) | Amount: 25
2026-03-25 21:29:30,239 | shx_tip_bot.stellar | ERROR | Error checking allowance for GAHO2LQH: 'str' object has no attribute 'i128'
2026-03-25 21:29:30,241 | shx_tip_bot.stellar | INFO | Auto-approving House Account (GAHO2LQH) for Soroban tipping...
2026-03-25 21:29:37,782 | shx_tip_bot.stellar | ERROR | Soroban Submit Error: AAAAAAAwcQn////7AAAAAA==
2026-03-25 21:31:09,684 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:32:17,521 | shx_tip_bot | INFO | COMMAND | /withdraw | User: dogegecko (887682978392702997) | Amount: 25
2026-03-25 21:32:20,410 | shx_tip_bot.stellar | ERROR | Error checking allowance for GAHO2LQH: 'str' object has no attribute 'i128'
2026-03-25 21:32:20,411 | shx_tip_bot.stellar | INFO | Auto-approving House Account (GAHO2LQH) for Soroban tipping...
2026-03-25 21:32:27,796 | shx_tip_bot.stellar | ERROR | Soroban Submit Error: AAAAAAAwcQn////7AAAAAA==
2026-03-25 21:33:30,986 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:34:08,638 | shx_tip_bot.database | INFO | Database connection pool established.
2026-03-25 21:34:10,257 | shx_tip_bot | INFO | Bot online as SHxTipBot#1167 (ID: 1479701624334057512)
2026-03-25 21:34:10,257 | shx_tip_bot | INFO | Guild: 1480437856773210183 | Network: testnet
2026-03-25 21:34:10,295 | shx_tip_bot.database | INFO | Database initialized successfully.
2026-03-25 21:34:10,295 | shx_tip_bot.web | INFO | Web application started.
2026-03-25 21:34:10,411 | shx_tip_bot.database | INFO | Database connection pool closed.
2026-03-25 21:34:10,411 | shx_tip_bot.web | INFO | Web application stopped.
2026-03-25 21:34:12,017 | shx_tip_bot.database | INFO | Database connection pool established.
2026-03-25 21:34:13,494 | shx_tip_bot.database | INFO | Database initialized successfully.
2026-03-25 21:34:13,700 | shx_tip_bot | INFO | Synced 9 guild slash commands.
2026-03-25 21:34:14,106 | shx_tip_bot | INFO | Cleared global slash commands.
2026-03-25 21:34:14,111 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 174.17ms
2026-03-25 21:34:14,113 | shx_tip_bot.stellar | INFO | Starting deposit monitor for GAHO2LQH... from cursor now
2026-03-25 21:36:37,761 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:36:37,771 | shx_tip_bot | INFO | COMMAND | /link | User: dogegecko (887682978392702997)
2026-03-25 21:36:38,150 | shx_tip_bot | ERROR | App command error on link: Command 'link' raised an exception: NotFound: 404 Not Found (error code: 10062): Unknown interaction
Traceback (most recent call last):
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\commands.py", line 859, in _do_call
    return await self._callback(interaction, **params)  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\bot.py", line 124, in link_command
    await interaction.response.defer(ephemeral=True)
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\interactions.py", line 892, in defer
    response = await adapter.create_interaction_response(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\webhook\async_.py", line 224, in request
    raise NotFound(response, data)
discord.errors.NotFound: 404 Not Found (error code: 10062): Unknown interaction

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\tree.py", line 1302, in _call
    await command._invoke_with_namespace(interaction, namespace)
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\commands.py", line 884, in _invoke_with_namespace
    return await self._do_call(interaction, transformed_values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot\venv\Lib\site-packages\discord\app_commands\commands.py", line 877, in _do_call
    raise CommandInvokeError(self, e) from e
discord.app_commands.errors.CommandInvokeError: Command 'link' raised an exception: NotFound: 404 Not Found (error code: 10062): Unknown interaction
2026-03-25 21:36:59,803 | shx_tip_bot | INFO | HEARTBEAT | Bot Healthy | Latency: 128.90ms
\n"""