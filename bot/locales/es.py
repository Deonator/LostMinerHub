TEXTS = {

"banned_alert": "🚫 Has sido baneado del bot.",

"banned_message": "🚫 Has sido baneado del bot por un administrador.",

"status_online": "🟢 En línea",

"status_offline": "⚫ Fuera de línea",

"status_pending": "⏳ En moderación",

"status_approved": "✅ Aprobado",

"status_rejected": "❌ Rechazado",

"privacy_private": "🔒 Cerrado",

"privacy_public": "🔓 Abierto",

"time_less_than_minute": "menos de un minuto",

"time_unit_hour": "h",

"time_unit_minute": "min",

"time_unit_second": "seg",

"avatar_status_pending": "🖼 Avatar: ⏳ en moderación",

"avatar_status_approved": "🖼 Avatar: ✅ disponible",

"avatar_status_none": "🖼 Avatar: ninguno",

"time_remaining_suffix": "⏱ restante: <b>{time}</b>",

"value_none": "ninguno",

"pwd_hidden_requires_approval": "🔒 oculta (requiere aprobación)",

"pwd_hidden": "🔒 oculta",

"server_card_template": """
🖥 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Contraseña: <code>{password}</code>
📋 Estado: {status_label}
🔐 Tipo: {privacy_badge}
{avatar_line}
📶 {online_line}
""",

"public_server_card_template": """
🗂 <b>Servidores LostMiner</b> <code>{page}/{total}</code>

🖥 <b>{name}</b> {privacy_badge}
📝 {description}
🌐 <code>{ip}</code>
🔑 Contraseña: {pwd_line}
📶 {status_badge}
""",

"btn_servers": "🗂 Servidores",

"btn_my_server": "🛠 Mi servidor",

"btn_create_server": "➕ Crear servidor",

"btn_cancel": "❌ Cancelar",

"btn_admin": "🔐 Admin",

"btn_logs": "📋 Registros",

"btn_global_ban": "🚫 Baneo global",

"btn_global_unban": "✅ Desbaneo global",

"btn_banlist": "📋 Lista de baneados",

"nav_prev": "◀️",

"nav_next": "▶️",

"btn_manage": "⚙️ Gestionar",

"btn_unsubscribe": "🔕 Cancelar suscripción",

"btn_subscribe": "🔔 Suscribirse",

"btn_request_password": "🔑 Solicitar contraseña",

"btn_view_password": "🔑 Ver contraseña",

"btn_turn_off": "⚫ Apagar",

"btn_turn_on": "🟢 Encender por 1 hora",

"btn_make_public": "🔓 Hacer público",

"btn_make_private": "🔒 Cerrar servidor",

"btn_avatar_pending": "🖼 Avatar (⏳ en moderación)",

"btn_avatar_change": "🖼 Cambiar avatar",

"btn_avatar_upload": "🖼 Subir avatar",

"btn_change_password": "🔑 Cambiar contraseña",

"btn_server_banlist": "🚫 Lista de baneados del servidor",

"btn_delete_server": "🗑 Eliminar servidor",

"btn_confirm_delete": "✅ Sí, eliminar",

"btn_grant_password": "✅ Dar contraseña",

"btn_reject_password": "❌ Rechazar",

"btn_ban_by_id": "➕ Banear por ID",

"btn_back": "◀️ Atrás",

"btn_unban_user": "🔓 Desbanear {user_id} ({date})",

"btn_approve": "✅ Aprobar",

"btn_reject": "❌ Rechazar",

"no_approved_servers": "📭 Todavía no hay servidores aprobados.",

"invalid_data": "❌ Datos incorrectos.",

"no_servers": "📭 No hay servidores.",

"manage_hint": "Gestiona tu servidor con /my_server",

"server_not_found": "❌ Servidor no encontrado.",

"cant_subscribe_own": "❌ No puedes suscribirte a tu propio servidor.",

"log_unsubscribed": "@{username} canceló la suscripción a \"{name}\"",

"log_subscribed": "@{username} se suscribió a \"{name}\"",

"unsubscribed": "🔕 Has cancelado la suscripción al servidor.",

"subscribed": "🔔 ¡Te has suscrito! Recibirás una notificación cuando el servidor esté en línea.",

"no_password": "Este servidor no tiene contraseña.",

"banned_by_owner": "🚫 Has sido baneado por el propietario de este servidor.",

"password_message": """
🔑 Contraseña del servidor «{name}»:
<code>{password}</code>

<i>Te recomendamos eliminar este mensaje después de leerlo.</i>
""",

"password_sent": "✅ Contraseña enviada por mensaje privado.",

"password_send_failed": "❌ No se pudo enviar la contraseña. Escríbele al bot en privado e inténtalo de nuevo.",

"owner_password_requested": """
🔐 <b>¡Alguien ha solicitado la contraseña de tu servidor!</b>

🖥 Servidor: <b>{name}</b>
👤 Usuario: {username}
🆔 ID: <code>{user_id}</code>
""",

"log_password_requested": "{username} recibió la contraseña del servidor \"{name}\"",

"request_already_sent": "⏳ La solicitud ya fue enviada. Espera la aprobación del propietario.",

"request_sent": "📨 Solicitud enviada. Espera la aprobación del propietario.",

"owner_private_password_requested": """
🔐 <b>¡Solicitud de contraseña de servidor cerrado!</b>

🖥 Servidor: <b>{name}</b>
👤 Usuario: {username}
🆔 ID: <code>{user_id}</code>

¿Darle la contraseña a este usuario?
""",

"log_private_password_requested": "{username} solicitó la contraseña del servidor cerrado \"{name}\"",

"request_not_found": "❌ Solicitud no encontrada.",

"request_already_processed": "Esta solicitud ya fue procesada.",

"no_access": "❌ Sin acceso.",

"password_granted_message": """
✅ <b>¡El propietario te ha dado la contraseña!</b>

🖥 Servidor: <b>{name}</b>
🔑 Contraseña: <code>{password}</code>

<i>Te recomendamos eliminar este mensaje después de leerlo.</i>
""",

"password_delivery_failed": """
⚠️ No se pudo entregar la contraseña al usuario <code>{user_id}</code> — es posible que haya bloqueado al bot.

La solicitud sigue activa, intenta dar la contraseña de nuevo.
""",

"password_delivery_failed_alert": "❌ No se pudo entregar la contraseña.",

"log_password_request_approved": "Solicitud de contraseña #{request_id} para el servidor «{name}» aprobada",

"password_granted_edit": "✅ Contraseña entregada al usuario <code>{user_id}</code>.",

"password_granted_alert": "✅ Contraseña entregada.",

"log_password_request_rejected": "Solicitud de contraseña #{request_id} para el servidor «{name}» rechazada",

"password_request_rejected_notify": """
❌ <b>El propietario rechazó tu solicitud de contraseña.</b>

🖥 Servidor: <b>{name}</b>
""",

"password_request_rejected_edit": "❌ Solicitud de contraseña de <code>{user_id}</code> rechazada.",

"password_request_rejected_alert": "❌ Solicitud rechazada.",

"already_has_server": """
❌ Ya tienes un servidor activo. Solo puedes crear uno.

Gestiónalo con /my_server
""",

"create_step1": """
🛠 <b>Creación de servidor</b>

Paso 1/4 — Introduce el <b>nombre</b> del servidor:
<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"please_send_text": "❌ Por favor, envía texto.",

"name_too_long": "❌ El nombre es demasiado largo (máx. 64 caracteres). Inténtalo de nuevo:",

"create_step2": "Paso 2/4 — Introduce la <b>descripción</b> del servidor:",

"description_too_long": "❌ La descripción es demasiado larga (máx. 512 caracteres). Inténtalo de nuevo:",

"create_step3": "Paso 3/4 — Introduce la <b>dirección IP</b> del servidor:",

"create_step4": """
Paso 4/4 — Introduce la <b>contraseña</b> para entrar al servidor
(o escribe <code>ninguna</code> si no hay contraseña):
""",

"log_server_created": "@{username} creó el servidor \"{name}\"",

"server_submitted": """
✅ <b>¡Servidor enviado a moderación!</b>

📛 Nombre: {name}
🌐 Dirección: <code>{ip}</code>

Espera la aprobación del administrador.
""",

"admin_new_server": """
🔔 <b>¡Nuevo servidor en moderación!</b>

📛 {name}
🌐 <code>{ip}</code>

Usa /admin para revisarlo.
""",

"no_own_server": "❌ No tienes ningún servidor.\nCréalo con el comando /create",

"avatar_caption": "🖼 <b>Avatar del servidor</b>",

"server_turned_on_alert": "🟢 ¡Servidor encendido por 1 hora!",

"log_server_online": "El servidor «{name}» fue encendido por su propietario",

"pwd_hint_request": "🔑 Solicitar contraseña — botón en /servers",

"pwd_hint_hidden": "🔒 oculta — botón en /servers",

"subscriber_notify": """
🟢 <b>¡El servidor «{name}» está en línea!</b>

🌐 <code>{ip}</code>
🔑 Contraseña: {pwd_hint}

⏱ Estará en línea por 1 hora más.
""",

"server_turned_off_alert": "⚫ El servidor está apagado.",

"log_server_offline": "El servidor «{name}» fue apagado por su propietario",

"change_password_prompt": """
🔑 Introduce la nueva contraseña del servidor
(o escribe <code>ninguna</code> para quitar la contraseña):

<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"label_private": "cerrado 🔒",

"label_public": "abierto 🔓",

"server_type_changed_alert": "Ahora el servidor está {label}.",

"log_server_type_changed": "El servidor «{name}» pasó a estar {type}",

"banlist_header": "🚫 <b>Lista de baneados del servidor «{name}»</b>\n\n",

"banlist_count": "Usuarios baneados: <b>{count}</b>",

"banlist_empty": "No hay usuarios baneados.",

"ban_prompt": """
🚫 <b>Banear usuario en el servidor «{name}»</b>

Envía el <b>ID de Telegram</b> del usuario que quieres banear:
<i>Para cancelar, pulsa ❌ Cancelar o /cancel</i>
""",

"avatar_already_pending": "⏳ El avatar ya está en moderación. Espera la decisión del administrador.",

"avatar_upload_prompt": """
🖼 <b>Subir avatar</b>

Envía una foto — se enviará a moderación.
Una vez aprobada, el avatar aparecerá en la ficha del servidor.

<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"delete_confirm_prompt": """
🗑 <b>¿Eliminar el servidor «{name}»?</b>

Esta acción es irreversible. Se eliminarán todos los suscriptores y solicitudes de contraseña.
""",

"server_deleted_message": """
🗑 El servidor <b>«{name}»</b> ha sido eliminado.

Puedes crear un nuevo servidor con el comando /create
""",

"server_deleted_alert": "✅ Servidor eliminado.",

"server_delete_failed": "❌ No se pudo eliminar el servidor.",

"delete_cancelled_alert": "Eliminación cancelada.",

"unknown_action_alert": "❌ Acción desconocida.",

"state_error": "❌ Algo salió mal. Inténtalo de nuevo con /my_server",

"log_password_changed": "Se cambió la contraseña del servidor «{name}»",

"password_updated": "✅ Contraseña actualizada: {password}\n\nGestión del servidor: /my_server",

"enter_numeric_id_retry": "❌ Introduce un ID de Telegram numérico. Inténtalo de nuevo:",

"cant_ban_self": "❌ No puedes banearte a ti mismo.",

"cant_ban_admin": "❌ No puedes banear a un administrador.",

"log_server_ban": "El usuario {user_id} fue baneado en el servidor «{name}»",

"server_ban_success": """
🚫 El usuario <code>{user_id}</code> ha sido baneado en el servidor <b>«{name}»</b>.
No podrá solicitar la contraseña.

Lista de baneados: /my_server → 🚫 Lista de baneados del servidor
""",

"server_ban_notify": """
🚫 Has sido baneado en el servidor <b>«{name}»</b>.
Ya no puedes solicitar la contraseña de este servidor.
""",

"already_banned": "⚠️ El usuario <code>{user_id}</code> ya está baneado en este servidor.",

"ban_record_not_found": "Registro no encontrado.",

"log_server_unban": "El usuario {user_id} fue desbaneado en el servidor «{name}»",

"server_unban_notify": """
✅ Has sido desbaneado en el servidor <b>«{name}»</b>.
Ahora puedes volver a solicitar la contraseña.
""",

"unbanned_alert": "✅ Desbaneado.",

"avatar_not_photo": "❌ Por favor, envía una <b>foto</b> (no un archivo).\nPara cancelar, pulsa ❌ Cancelar.",

"log_avatar_uploaded": "El avatar del servidor «{name}» fue enviado a moderación",

"avatar_submitted": "📨 <b>¡Avatar enviado a moderación!</b>\n\nUna vez aprobado por el administrador, aparecerá en la ficha del servidor.",

"admin_new_avatar": """
🖼 <b>¡Nuevo avatar en moderación!</b>

🖥 Servidor: <b>{name}</b>
👤 Propietario: <code>{owner_id}</code>

Usa /admin para revisarlo.
""",

"no_permission": "❌ No tienes permisos para este comando.",

"no_pending_moderation": "✅ No hay solicitudes de moderación.",

"pending_servers_count": "🔍 <b>Servidores en moderación: {count}</b>",

"admin_server_card": """
📛 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Contraseña: <code>{password}</code>
👤 Propietario: <code>{owner_id}</code>
🕐 Creado: {created_at}
""",

"pending_avatars_count": "🖼 <b>Avatares en moderación: {count}</b>",

"avatar_moderation_caption": """
🖼 Avatar del servidor <b>«{name}»</b>
👤 Propietario: <code>{owner_id}</code>
""",

"avatar_upload_failed": "⚠️ No se pudo cargar el avatar del servidor «{name}».",

"server_approved_edit": "✅ Servidor <b>«{name}»</b> aprobado.",

"server_approved_notify": """
✅ <b>¡Tu servidor «{name}» ha sido aprobado!</b>
Ahora es visible en la lista /servers
Gestiónalo con /my_server
""",

"server_rejected_edit": "❌ Servidor <b>«{name}»</b> rechazado.",

"server_rejected_notify": """
❌ <b>Tu servidor «{name}» ha sido rechazado.</b>

Elimínalo y crea uno nuevo con el comando /create
""",

"avatar_already_processed": "El avatar ya fue procesado.",

"avatar_approved_edit": "✅ El avatar del servidor <b>«{name}»</b> ha sido aprobado.",

"avatar_approved_alert": "✅ Avatar aprobado.",

"avatar_approved_notify": """
✅ <b>¡El avatar de tu servidor ha sido aprobado!</b>

🖥 Servidor: <b>{name}</b>
Ahora se muestra en /my_server.
""",

"avatar_rejected_edit": "❌ El avatar del servidor <b>«{name}»</b> ha sido rechazado.",

"avatar_rejected_alert": "❌ Avatar rechazado.",

"avatar_rejected_notify": """
❌ <b>El avatar de tu servidor ha sido rechazado.</b>

🖥 Servidor: <b>{name}</b>
Puedes subir otro con /my_server.
""",

"global_ban_success": "🚫 El usuario <code>{user_id}</code> ha sido baneado globalmente.",

"global_ban_notify": "🚫 <b>Has sido baneado del bot por un administrador.</b>",

"already_globally_banned": "⚠️ El usuario <code>{user_id}</code> ya está baneado.",

"global_unban_success": "✅ El usuario <code>{user_id}</code> ha sido desbaneado.",

"global_unban_notify": "✅ <b>Tu baneo ha sido levantado. Puedes volver a usar el bot.</b>",

"not_globally_banned": "⚠️ El usuario <code>{user_id}</code> no estaba baneado.",

"global_ban_prompt": "🚫 <b>Baneo global</b>\n\nIntroduce el ID de Telegram del usuario:\n<i>Para cancelar: /cancel</i>",

"global_unban_prompt": "✅ <b>Desbaneo global</b>\n\nIntroduce el ID de Telegram del usuario:\n<i>Para cancelar: /cancel</i>",

"global_ban_prompt_btn": "🚫 <b>Baneo global</b>\n\nIntroduce el ID de Telegram del usuario:\n<i>Para cancelar: /cancel o ❌ Cancelar</i>",

"global_unban_prompt_btn": "✅ <b>Desbaneo global</b>\n\nIntroduce el ID de Telegram del usuario:\n<i>Para cancelar: /cancel o ❌ Cancelar</i>",

"enter_numeric_id": "❌ Introduce el ID de Telegram numérico:",

"global_banlist_empty": "✅ La lista global de baneados está vacía.",

"global_banlist_header": "🚫 <b>Lista global de baneados ({count}):</b>\n",

"global_banlist_entry": "• <code>{user_id}</code>  desde {date}",

"logs_empty": "📋 El registro está vacío.",

"logs_header": "📋 <b>Registro de eventos (últimos 40):</b>\n",

"logs_entry": "<code>{datetime}</code> {label}\n   👤 {actor}{server}{details}",

"logs_truncated": "\n\n<i>...truncado</i>",

"nothing_to_cancel": "No hay nada que cancelar.",

"action_cancelled": "🚫 Acción cancelada.",

"btn_edit_server": "✏️ Editar datos",

"btn_edit_pending": "✏️ Cambios (⏳ en moderación)",

"edit_pending_line": "✏️ Cambios: ⏳ en moderación",

"edit_menu": """
✏️ <b>¿Qué quieres cambiar en el servidor «{name}»?</b>

Los cambios solo se aplicarán después de ser revisados por un administrador.
""",

"btn_edit_name": "📛 Nombre",

"btn_edit_description": "📝 Descripción",

"btn_edit_ip": "🌐 Dirección IP",

"edit_already_pending": "⏳ El servidor ya tiene cambios en moderación. Espera la decisión del administrador.",

"edit_prompt_name": """
📛 Introduce el nuevo <b>nombre</b> del servidor (máx. 64 caracteres):

<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"edit_prompt_description": """
📝 Introduce la nueva <b>descripción</b> del servidor (máx. 512 caracteres):

<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"edit_prompt_ip": """
🌐 Introduce la nueva <b>dirección IP</b> del servidor:

<i>Para cancelar, pulsa ❌ Cancelar o escribe /cancel</i>
""",

"log_edit_requested": "@{username} propuso un nuevo valor para el campo «{field}» del servidor «{name}»",

"edit_submitted": """
📨 <b>¡Cambio enviado a moderación!</b>

Una vez aprobado por el administrador, el nuevo valor aparecerá en la ficha del servidor.
""",

"admin_new_edit": """
✏️ <b>¡Nueva edición en moderación!</b>

🖥 Servidor: <b>{name}</b>
👤 Propietario: <code>{owner_id}</code>

{diff}

Usa /admin para revisarlo.
""",

"edit_diff_line": "<b>{field}:</b>\n  antes: {old}\n  ahora: {new}",

"field_name": "Nombre",

"field_description": "Descripción",

"field_ip": "Dirección IP",

"pending_edits_count": "✏️ <b>Ediciones en moderación: {count}</b>",

"admin_edit_card": """
✏️ <b>Edición del servidor «{name}»</b>
👤 Propietario: <code>{owner_id}</code>

{diff}
""",

"edit_already_processed": "El cambio ya fue procesado o no existe.",

"edit_approved_edit": "✅ Los cambios del servidor <b>«{name}»</b> han sido aprobados.",

"edit_approved_alert": "✅ Cambios aprobados.",

"edit_approved_notify": """
✅ <b>¡Los cambios de tu servidor han sido aprobados!</b>

🖥 Servidor: <b>{name}</b>
Los nuevos datos ya se muestran en la ficha.
""",

"edit_rejected_edit": "❌ Los cambios del servidor <b>«{name}»</b> han sido rechazados.",

"edit_rejected_alert": "❌ Cambios rechazados.",

"edit_rejected_notify": """
❌ <b>Los cambios de tu servidor han sido rechazados.</b>

🖥 Servidor: <b>{name}</b>
Los datos anteriores siguen vigentes. Puedes proponer una nueva edición con /my_server.
""",

}
