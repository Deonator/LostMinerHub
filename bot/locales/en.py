TEXTS = {

"banned_alert": "🚫 You have been banned from the bot.",

"banned_message": "🚫 You have been banned from the bot by an administrator.",

"status_online": "🟢 Online",

"status_offline": "⚫ Offline",

"status_pending": "⏳ Under moderation",

"status_approved": "✅ Approved",

"status_rejected": "❌ Rejected",

"privacy_private": "🔒 Closed",

"privacy_public": "🔓 Open",

"time_less_than_minute": "less than a minute",

"time_unit_hour": "h",

"time_unit_minute": "min",

"time_unit_second": "sec",

"avatar_status_pending": "🖼 Avatar: ⏳ pending moderation",

"avatar_status_approved": "🖼 Avatar: ✅ present",

"avatar_status_none": "🖼 Avatar: none",

"time_remaining_suffix": "⏱ remaining: <b>{time}</b>",

"value_none": "none",

"pwd_hidden_requires_approval": "🔒 hidden (requires approval)",

"pwd_hidden": "🔒 hidden",

"server_card_template": """
🖥 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Password: <code>{password}</code>
📋 Status: {status_label}
🔐 Type: {privacy_badge}
{avatar_line}
📶 {online_line}
""",

"public_server_card_template": """
🗂 <b>LostMiner Servers</b> <code>{page}/{total}</code>

🖥 <b>{name}</b> {privacy_badge}
📝 {description}
🌐 <code>{ip}</code>
🔑 Password: {pwd_line}
📶 {status_badge}
""",

"btn_servers": "🗂 Servers",

"btn_my_server": "🛠 My Server",

"btn_create_server": "➕ Create Server",

"btn_cancel": "❌ Cancel",

"btn_admin": "🔐 Admin",

"btn_logs": "📋 Logs",

"btn_global_ban": "🚫 G-ban",

"btn_global_unban": "✅ G-unban",

"btn_banlist": "📋 Ban List",

"nav_prev": "◀️",

"nav_next": "▶️",

"btn_manage": "⚙️ Manage",

"btn_unsubscribe": "🔕 Unsubscribe",

"btn_subscribe": "🔔 Subscribe",

"btn_request_password": "🔑 Request Password",

"btn_view_password": "🔑 View Password",

"btn_turn_off": "⚫ Turn off",

"btn_turn_on": "🟢 Turn on for 1 hour",

"btn_make_public": "🔓 Make public",

"btn_make_private": "🔒 Close server",

"btn_avatar_pending": "🖼 Avatar (⏳ pending)",

"btn_avatar_change": "🖼 Change avatar",

"btn_avatar_upload": "🖼 Upload avatar",

"btn_change_password": "🔑 Change password",

"btn_server_banlist": "🚫 Server banlist",

"btn_delete_server": "🗑 Delete server",

"btn_confirm_delete": "✅ Yes, delete",

"btn_grant_password": "✅ Grant password",

"btn_reject_password": "❌ Reject",

"btn_ban_by_id": "➕ Ban by ID",

"btn_back": "◀️ Back",

"btn_unban_user": "🔓 Unban {user_id} ({date})",

"btn_approve": "✅ Approve",

"btn_reject": "❌ Reject",

"no_approved_servers": "📭 There are no approved servers yet.",

"invalid_data": "❌ Incorrect data.",

"no_servers": "📭 There are no servers.",

"manage_hint": "Manage your server via /my_server",

"server_not_found": "❌ Server not found.",

"cant_subscribe_own": "❌ Cannot subscribe to your server.",

"log_unsubscribed": "@{username} unsubscribed from "{name}",

"log_subscribed": "@{username} subscribed to "{name}",

"unsubscribed": "🔕 You have unsubscribed from the server.",

"subscribed": "🔔 You have subscribed! Get a notification when the server is online.",

"no_password": "This server has no password.",

"banned_by_owner": "🚫 You have been banned by the owner of this server.",

"password_message": """
🔑 Server password for "{name}":
<code>{password}</code>

<i>We recommend deleting this message after reading.</i>
""",

"password_sent": "✅ Password sent via private message.",

"password_send_failed": "❌ Failed to send password. Message the bot in private and try again.",

"owner_password_requested": """
🔐 <b>Someone has requested your server password!</b>

🖥 Server: <b>{name}</b>
👤 User: {username}
🆔 ID: <code>{user_id}</code>
""",

"log_password_requested": "{username} received the password for server "{name}"",

"request_already_sent": "⏳ Request already sent. Wait for owner approval.",

"request_sent": "📨Request sent. Await owner approval.",

"owner_private_password_requested": """
🔐 <b>Requesting a private server password!</b>

🖥 Server: <b>{name}</b>
👤 User: {username}
🆔 ID: <code>{user_id}</code>

Give this user a password?
""",

"log_private_password_requested": "{username} requested a password for the private server "{name}"",

"request_not_found": "❌ Request not found.",

"request_already_processed": "This request has already been processed.",

"no_access": "❌ No access.",

"password_granted_message": """
✅ <b>The owner has given you a password!</b>

🖥 Server: <b>{name}</b>
🔑 Password: <code>{password}</code>

<i>We recommend deleting this message after reading.</i>
""",

"password_delivery_failed": """
⚠️ Failed to deliver password to user <code>{user_id}</code> - they may have blocked the bot.

The request remains active, try issuing your password again.
""",

"password_delivery_failed_alert": "❌ Failed to deliver password.",

"log_password_request_approved": "Password request #{request_id} for server '{name}' approved.",

"password_granted_edit": "✅ Password issued to user <code>{user_id}</code>.",

"password_granted_alert": "✅ Password issued.",

"log_password_request_rejected": "Password request #{request_id} for server '{name}' rejected.",

"password_request_rejected_notify": """
❌ <b>The owner rejected your password request.</b>

🖥 Server: <b>{name}</b>
""",

"password_request_rejected_edit": "❌ Password request from <code>{user_id}</code> rejected.",

"password_request_rejected_alert": "❌ Request rejected.",

"already_has_server": """
❌ You already have an active server. You can only create one.

Manage it via /my_server
""",

"create_step1": """
🛠 <b>Creating a server</b>

Step 1/4 — Enter a <b>server name</b>:
<i>To cancel, click ❌ Cancel or type /cancel</i>
""",

"please_send_text": "❌ Please send text.",

"name_too_long": "❌ The name is too long (max. 64 characters). Try again:",

"create_step2": "Step 2/4 — Enter a server <b>description</b>:",

"description_too_long": "❌ The description is too long (max. 512 characters). Try again:",

"create_step3": "Step 3/4 — Enter the server's IP address:",

"create_step4": """
Step 4/4 — Enter your password to log in to the server
(or enter none if there is no password):
""",

"log_server_created": "@{username} created the server "{name}"",

"server_submitted": """
✅ <b>Server submitted for moderation!</b>

📛 Name: {name}
🌐 Address: <code>{ip}</code>

Wait for administrator approval.
""",

"admin_new_server": """
🔔 <b>New server under moderation!</b>

📛 {name}
🌐 <code>{ip}</code>

Use /admin to check.
""",

"no_own_server": "❌ You don't have a server.\nCreate one with the /create command",

"avatar_caption": "🖼 <b>Server avatar</b>",

"server_turned_on_alert": "🟢 Server turned on for 1 hour!",

"log_server_online": "Server "{name}" has been turned on by its owner",

"pwd_hint_request": "🔑 Request password — button in /servers",

"pwd_hint_hidden": "🔒 Hidden — button in /servers",

"subscriber_notify": """
🟢 <b>Server "{name}" is now online!</b>

🌐 <code>{ip}</code>
🔑 Password: {pwd_hint}

⏱ Will be online for another 1 hour.
""",

"server_turned_off_alert": "⚫ The server is offline.",

"log_server_offline": "Server "{name}" has been turned off by its owner.",

"change_password_prompt": """
🔑 Enter a new server password
(or type <code>no</code> to remove the password):

<i>To cancel, click ❌ Cancel or type /cancel</i>
""",

"label_private": "closed 🔒",

"label_public": "open 🔓",

"server_type_changed_alert": "Server is now {label}.",

"log_server_type_changed": "Server "{name}" has become {type}",

"banlist_header": "🚫 <b>Server ban list "{name}"</b>\n\n",

"banlist_count": "Banned users: <b>{count}</b>",

"banlist_empty": "No banned users.",

"ban_prompt": """
🚫 <b>Ban user on server "{name}"</b>

Send the <b>Telegram ID</b> of the user you want to ban:
<i>To cancel, click ❌ Cancel or /cancel</i>
""",

"avatar_already_pending": "⏳ Your avatar is already being moderated. Wait for the administrator's decision.",

"avatar_upload_prompt": """
🖼 <b>Upload avatar</b>

Submit a photo – it will be sent for moderation.
Once approved, your avatar will appear on the server card.

<i>To cancel, click the ❌ Cancel button or type /cancel</i>
""",

"delete_confirm_prompt": """
🗑 <b>Delete server "{name}"?</b>

This action is irreversible. All subscribers and password requests will be deleted.
""",

"server_deleted_message": """
🗑 Server <b>"{name}"</b> has been deleted.

You can create a new server with the /create command
""",

"server_deleted_alert": "✅ Server deleted.",

"server_delete_failed": "❌ Failed to delete server.",

"delete_cancelled_alert": "Deletion canceled.",

"unknown_action_alert": "❌ Unknown action.",

"state_error": "❌ Something went wrong. Try again via /my_server",

"log_password_changed": "The password for server "{name}" has been changed",

"password_updated": "✅ Password updated: {password}\n\nServer management: /my_server",

"enter_numeric_id_retry": "❌ Enter your numeric Telegram ID. Try again:",

"cant_ban_self": "❌ You can't ban yourself.",

"cant_ban_admin": "❌ You can't ban an administrator.",

"log_server_ban": "User {user_id} has been banned on server "{name}",

"server_ban_success": """
🚫 User <code>{user_id}</code> has been banned on server <b>"{name}"</b>.
They won't be able to request a password.

Ban List: /my_server → 🚫 Server Ban List
""",

"server_ban_notify": """
🚫 You have been banned from server <b>"{name}"</b>.
You can no longer request a password for this server.
""",

"already_banned": "⚠️ User <code>{user_id}</code> is already banned from this server.",

"ban_record_not_found": "Record not found.",

"log_server_unban": "User {user_id} has been unbanned from server "{name}"",

"server_unban_notify": """
✅ You have been unbanned from server <b>"{name}"</b>.
You can now request a password again.
""",

"unbanned_alert": "✅ Unbanned.",

"avatar_not_photo": "❌ Please send a <b>photo</b> (not a file).\nTo cancel, click ❌ Cancel.",

"log_avatar_uploaded": "Server avatar "{name}" has been sent for moderation.",

"avatar_submitted": "📨 <b>Avatar has been sent for moderation!</b>\n\nAfter approval by the administrator, it will appear on the server card.",

"admin_new_avatar": """
🖼 <b>New avatar is being moderated!</b>

🖥 Server: <b>{name}</b>
👤 Owner: <code>{owner_id}</code>

Use /admin to verify.
""",

"no_permission": "❌ You don't have permissions for this command.",

"no_pending_moderation": "✅ No moderation requests.",

"pending_servers_count": "🔍 <b>Servers pending moderation: {count}</b>",

"admin_server_card": """
📛 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Password: <code>{password}</code>
👤 Owner: <code>{owner_id}</code>
🕐 Created: {created_at}
""",

"pending_avatars_count": "🖼 <b>Avatars pending moderation: {count}</b>",

"avatar_moderation_caption": """
🖼 Server Avatar <b>«{name}»</b>
👤 Owner: <code>{owner_id}</code>
""",

"avatar_upload_failed": "⚠️ Failed to upload server avatar "{name}".",

"server_approved_edit": "✅ Server <b>«{name}»</b> approved.",

"server_approved_notify": """
✅ <b>Your server "{name}" has been approved!</b>
It is now visible in the /servers list
Manage it via /my_server
""",

"server_rejected_edit": "❌ Server <b>«{name}»</b> rejected.",

"server_rejected_notify": """
❌ <b>Your server "{name}" Rejected.

Delete it and create a new one with the /create command
""",

"avatar_already_processed": "Your avatar has already been processed.",

"avatar_approved_edit": "✅ Your server avatar <b>«{name}»</b> has been approved.",

"avatar_approved_alert": "✅ Your avatar has been approved.",

"avatar_approved_notify": """
✅ <b>Your server avatar has been approved!</b>

🖥 Server: <b>{name}</b>
It is now displayed in /my_server.
""",

"avatar_rejected_edit": "❌ The server avatar <b>"{name}"</b> has been rejected.",

"avatar_rejected_alert": "❌ Avatar rejected.",

"avatar_rejected_notify": """
❌ <b>Your server avatar has been rejected.</b>

🖥 Server: <b>{name}</b>
You can upload a different one via /my_server.
""",
"global_ban_success": "🚫 User <code>{user_id}</code> has been globally banned.",

"global_ban_notify": "🚫 <b>You have been banned from the bot by an administrator.</b>",

"already_globally_banned": "⚠️ User <code>{user_id}</code> has already been banned.",

"global_unban_success": "✅ User <code>{user_id}</code> has been unbanned.",

"global_unban_notify": "✅ <b>Your ban has been lifted. You can use the bot again.</b>",

"not_globally_banned": "⚠️ User <code>{user_id}</code> has not been banned.",

"global_ban_prompt": "🚫 <b>Global ban</b>\n\nEnter Telegram User ID:\n<i>To cancel: /cancel</i>",

"global_unban_prompt": "✅ <b>Global unban</b>\n\nEnter Telegram user ID:\n<i>To cancel: /cancel</i>",

"global_ban_prompt_btn": "🚫 <b>Global ban</b>\n\nEnter Telegram user ID:\n<i>To cancel: /cancel or ❌ Cancel</i>",

"global_unban_prompt_btn": "✅ <b>Global unban</b>\n\nEnter Telegram user ID:\n<i>To cancel: /cancel or ❌ Cancel</i>",

"enter_numeric_id": "❌ Enter numeric Telegram ID:",

"global_banlist_empty": "✅ Global The ban list is empty.",

"global_banlist_header": "🚫 <b>Global ban list ({count}):</b>\n",

"global_banlist_entry": "• <code>{user_id}</code> since {date}",

"logs_empty": "📋 Log is empty.",

"logs_header": "📋 <b>Event log (last 40):</b>\n",

"logs_entry": "<code>{datetime}</code> {label}\n 👤 {actor}{server}{details}",

"logs_truncated": "\n\n<i>...truncated</i>",

"nothing_to_cancel": "Nothing to cancel.",

"action_cancelled": "🚫 Action canceled.",

"btn_edit_server": "✏️ Edit data",

"btn_edit_pending": "✏️ Changes (⏳ pending)",

"edit_pending_line": "✏️ Changes: ⏳ pending",

"edit_menu": """
✏️ <b>What should I change on the server "{name}"?</b>

Changes will only take effect after being reviewed by an administrator.
""",

"btn_edit_name": "📛 Name",

"btn_edit_description": "📝 Description",

"btn_edit_ip": "🌐 IP address",

"edit_already_pending": "⏳ The server already has changes pending moderation. Wait for the administrator's decision.",

"edit_prompt_name": """
📛 Enter a new server <b>name</b> (max. 64 characters):

<i>To cancel, click ❌ Cancel or type /cancel</i>
""",

"edit_prompt_description": """
📝 Enter a new server <b>description</b> (max. 512 characters):

<i>To cancel, click ❌ Cancel or type /cancel</i>
""",

"edit_prompt_ip": """
🌐 Enter a new server <b>IP address</b>:

<i>To cancel, click ❌ Cancel or type /cancel</i>
""",

"log_edit_requested": "@{username} proposed a new value for field "{field}" for server "{name}"",

"edit_submitted": """
📨 <b>Change submitted for moderation!</b>

After approval by the administrator, the new value will appear on the server card.
""",

"admin_new_edit": """
✏️ <b>New edit pending moderation!</b>

🖥 Server: <b>{name}</b>
👤 Owner: <code>{owner_id}</code>

{diff}

Use /admin to check.
""",

"edit_diff_line": "<b>{field}:</b>\n was: {old}\n now: {new}",

"field_name": "Name",

"field_description": "Description",

"field_ip": "IP address",

"pending_edits_count": "✏️ <b>Edits pending moderation: {count}</b>",

"admin_edit_card": """
✏️ <b>Edit for server "{name}"</b>
👤 Owner: <code>{owner_id}</code>

{diff}
""",

"edit_already_processed": "Change already processed or missing.",

"edit_approved_edit": "✅ Changes to server <b>"{name}"</b> approved.",

"edit_approved_alert": "✅ Changes approved.",

"edit_approved_notify": """
✅ <b>Your server's changes have been approved!</b>

🖥 Server: <b>{name}</b>
New data is already showing on the card.
""",

"edit_rejected_edit": "❌ Server changes <b>"{name}"</b> rejected.",

"edit_rejected_alert": "❌ Changes rejected.",

"edit_rejected_notify": """
❌ <b>Your server's changes were rejected.</b>

🖥 Server: <b>{name}</b>
The previous data remains valid. You can submit a new edit via /my_server.
""",

}
