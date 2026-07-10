TEXTS = {

"banned_alert": "🚫 Você foi banido do bot.",

"banned_message": "🚫 Você foi banido do bot por um administrador.",

"status_online": "🟢 Online",

"status_offline": "⚫ Offline",

"status_pending": "⏳ Em moderação",

"status_approved": "✅ Aprovado",

"status_rejected": "❌ Rejeitado",

"privacy_private": "🔒 Fechado",

"privacy_public": "🔓 Aberto",

"time_less_than_minute": "menos de um minuto",

"time_unit_hour": "h",

"time_unit_minute": "min",

"time_unit_second": "seg",

"avatar_status_pending": "🖼 Avatar: ⏳ em moderação",

"avatar_status_approved": "🖼 Avatar: ✅ disponível",

"avatar_status_none": "🖼 Avatar: nenhum",

"time_remaining_suffix": "⏱ restante: <b>{time}</b>",

"value_none": "nenhuma",

"pwd_hidden_requires_approval": "🔒 oculta (requer aprovação)",

"pwd_hidden": "🔒 oculta",

"server_card_template": """
🖥 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Senha: <code>{password}</code>
📋 Status: {status_label}
🔐 Tipo: {privacy_badge}
{avatar_line}
📶 {online_line}
""",

"public_server_card_template": """
🗂 <b>Servidores LostMiner</b> <code>{page}/{total}</code>

🖥 <b>{name}</b> {privacy_badge}
📝 {description}
🌐 <code>{ip}</code>
🔑 Senha: {pwd_line}
📶 {status_badge}
""",

"btn_servers": "🗂 Servidores",

"btn_my_server": "🛠 Meu servidor",

"btn_create_server": "➕ Criar servidor",

"btn_cancel": "❌ Cancelar",

"btn_admin": "🔐 Admin",

"btn_logs": "📋 Registros",

"btn_global_ban": "🚫 Ban global",

"btn_global_unban": "✅ Desban global",

"btn_banlist": "📋 Lista de banidos",

"nav_prev": "◀️",

"nav_next": "▶️",

"btn_manage": "⚙️ Gerenciar",

"btn_unsubscribe": "🔕 Cancelar inscrição",

"btn_subscribe": "🔔 Inscrever-se",

"btn_request_password": "🔑 Solicitar senha",

"btn_view_password": "🔑 Ver senha",

"btn_turn_off": "⚫ Desligar",

"btn_turn_on": "🟢 Ligar por 1 hora",

"btn_make_public": "🔓 Tornar público",

"btn_make_private": "🔒 Fechar servidor",

"btn_avatar_pending": "🖼 Avatar (⏳ em moderação)",

"btn_avatar_change": "🖼 Trocar avatar",

"btn_avatar_upload": "🖼 Enviar avatar",

"btn_change_password": "🔑 Alterar senha",

"btn_server_banlist": "🚫 Lista de banidos do servidor",

"btn_delete_server": "🗑 Excluir servidor",

"btn_confirm_delete": "✅ Sim, excluir",

"btn_grant_password": "✅ Conceder senha",

"btn_reject_password": "❌ Recusar",

"btn_ban_by_id": "➕ Banir por ID",

"btn_back": "◀️ Voltar",

"btn_unban_user": "🔓 Desbanir {user_id} ({date})",

"btn_approve": "✅ Aprovar",

"btn_reject": "❌ Rejeitar",

"no_approved_servers": "📭 Ainda não há servidores aprovados.",

"invalid_data": "❌ Dados inválidos.",

"no_servers": "📭 Não há servidores.",

"manage_hint": "Gerencie seu servidor pelo /my_server",

"server_not_found": "❌ Servidor não encontrado.",

"cant_subscribe_own": "❌ Você não pode se inscrever no seu próprio servidor.",

"log_unsubscribed": "@{username} cancelou a inscrição em \"{name}\"",

"log_subscribed": "@{username} se inscreveu em \"{name}\"",

"unsubscribed": "🔕 Você cancelou a inscrição no servidor.",

"subscribed": "🔔 Inscrição feita! Você receberá uma notificação quando o servidor ficar online.",

"no_password": "Este servidor não tem senha.",

"banned_by_owner": "🚫 Você foi banido pelo dono deste servidor.",

"password_message": """
🔑 Senha do servidor «{name}»:
<code>{password}</code>

<i>Recomendamos apagar esta mensagem após a leitura.</i>
""",

"password_sent": "✅ Senha enviada por mensagem privada.",

"password_send_failed": "❌ Não foi possível enviar a senha. Fale com o bot no privado e tente novamente.",

"owner_password_requested": """
🔐 <b>Alguém solicitou a senha do seu servidor!</b>

🖥 Servidor: <b>{name}</b>
👤 Usuário: {username}
🆔 ID: <code>{user_id}</code>
""",

"log_password_requested": "{username} recebeu a senha do servidor \"{name}\"",

"request_already_sent": "⏳ Solicitação já enviada. Aguarde a aprovação do dono.",

"request_sent": "📨 Solicitação enviada. Aguarde a aprovação do dono.",

"owner_private_password_requested": """
🔐 <b>Solicitação de senha de servidor fechado!</b>

🖥 Servidor: <b>{name}</b>
👤 Usuário: {username}
🆔 ID: <code>{user_id}</code>

Conceder a senha a este usuário?
""",

"log_private_password_requested": "{username} solicitou a senha do servidor fechado \"{name}\"",

"request_not_found": "❌ Solicitação não encontrada.",

"request_already_processed": "Esta solicitação já foi processada.",

"no_access": "❌ Sem acesso.",

"password_granted_message": """
✅ <b>O dono concedeu a senha!</b>

🖥 Servidor: <b>{name}</b>
🔑 Senha: <code>{password}</code>

<i>Recomendamos apagar esta mensagem após a leitura.</i>
""",

"password_delivery_failed": """
⚠️ Não foi possível entregar a senha ao usuário <code>{user_id}</code> — ele pode ter bloqueado o bot.

A solicitação continua ativa, tente conceder a senha novamente.
""",

"password_delivery_failed_alert": "❌ Não foi possível entregar a senha.",

"log_password_request_approved": "Solicitação de senha #{request_id} do servidor «{name}» aprovada",

"password_granted_edit": "✅ Senha concedida ao usuário <code>{user_id}</code>.",

"password_granted_alert": "✅ Senha concedida.",

"log_password_request_rejected": "Solicitação de senha #{request_id} do servidor «{name}» rejeitada",

"password_request_rejected_notify": """
❌ <b>O dono recusou sua solicitação de senha.</b>

🖥 Servidor: <b>{name}</b>
""",

"password_request_rejected_edit": "❌ Solicitação de senha de <code>{user_id}</code> rejeitada.",

"password_request_rejected_alert": "❌ Solicitação rejeitada.",

"already_has_server": """
❌ Você já tem um servidor ativo. Só é possível criar um.

Gerencie-o pelo /my_server
""",

"create_step1": """
🛠 <b>Criação de servidor</b>

Passo 1/4 — Digite o <b>nome</b> do servidor:
<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"please_send_text": "❌ Por favor, envie um texto.",

"name_too_long": "❌ O nome é muito longo (máx. 64 caracteres). Tente novamente:",

"create_step2": "Passo 2/4 — Digite a <b>descrição</b> do servidor:",

"description_too_long": "❌ A descrição é muito longa (máx. 512 caracteres). Tente novamente:",

"create_step3": "Passo 3/4 — Digite o <b>endereço IP</b> do servidor:",

"create_step4": """
Passo 4/4 — Digite a <b>senha</b> para entrar no servidor
(ou digite <code>nenhuma</code> se não houver senha):
""",

"log_server_created": "@{username} criou o servidor \"{name}\"",

"server_submitted": """
✅ <b>Servidor enviado para moderação!</b>

📛 Nome: {name}
🌐 Endereço: <code>{ip}</code>

Aguarde a aprovação do administrador.
""",

"admin_new_server": """
🔔 <b>Novo servidor em moderação!</b>

📛 {name}
🌐 <code>{ip}</code>

Use /admin para revisar.
""",

"no_own_server": "❌ Você não tem um servidor.\nCrie um com o comando /create",

"avatar_caption": "🖼 <b>Avatar do servidor</b>",

"server_turned_on_alert": "🟢 Servidor ligado por 1 hora!",

"log_server_online": "O servidor «{name}» foi ligado pelo dono",

"pwd_hint_request": "🔑 Solicitar senha — botão em /servers",

"pwd_hint_hidden": "🔒 oculta — botão em /servers",

"subscriber_notify": """
🟢 <b>O servidor «{name}» está online agora!</b>

🌐 <code>{ip}</code>
🔑 Senha: {pwd_hint}

⏱ Ficará online por mais 1 hora.
""",

"server_turned_off_alert": "⚫ O servidor está desligado.",

"log_server_offline": "O servidor «{name}» foi desligado pelo dono",

"change_password_prompt": """
🔑 Digite a nova senha do servidor
(ou digite <code>nenhuma</code> para remover a senha):

<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"label_private": "fechado 🔒",

"label_public": "aberto 🔓",

"server_type_changed_alert": "O servidor agora está {label}.",

"log_server_type_changed": "O servidor «{name}» passou a estar {type}",

"banlist_header": "🚫 <b>Lista de banidos do servidor «{name}»</b>\n\n",

"banlist_count": "Usuários banidos: <b>{count}</b>",

"banlist_empty": "Nenhum usuário banido.",

"ban_prompt": """
🚫 <b>Banir usuário no servidor «{name}»</b>

Envie o <b>ID do Telegram</b> do usuário que deseja banir:
<i>Para cancelar, toque em ❌ Cancelar ou /cancel</i>
""",

"avatar_already_pending": "⏳ O avatar já está em moderação. Aguarde a decisão do administrador.",

"avatar_upload_prompt": """
🖼 <b>Enviar avatar</b>

Envie uma foto — ela será enviada para moderação.
Após a aprovação, o avatar aparecerá na ficha do servidor.

<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"delete_confirm_prompt": """
🗑 <b>Excluir o servidor «{name}»?</b>

Esta ação é irreversível. Todos os inscritos e solicitações de senha serão excluídos.
""",

"server_deleted_message": """
🗑 O servidor <b>«{name}»</b> foi excluído.

Você pode criar um novo servidor com o comando /create
""",

"server_deleted_alert": "✅ Servidor excluído.",

"server_delete_failed": "❌ Não foi possível excluir o servidor.",

"delete_cancelled_alert": "Exclusão cancelada.",

"unknown_action_alert": "❌ Ação desconhecida.",

"state_error": "❌ Algo deu errado. Tente novamente pelo /my_server",

"log_password_changed": "A senha do servidor «{name}» foi alterada",

"password_updated": "✅ Senha atualizada: {password}\n\nGerenciamento do servidor: /my_server",

"enter_numeric_id_retry": "❌ Digite um ID numérico do Telegram. Tente novamente:",

"cant_ban_self": "❌ Você não pode banir a si mesmo.",

"cant_ban_admin": "❌ Você não pode banir um administrador.",

"log_server_ban": "O usuário {user_id} foi banido no servidor «{name}»",

"server_ban_success": """
🚫 O usuário <code>{user_id}</code> foi banido no servidor <b>«{name}»</b>.
Ele não poderá solicitar a senha.

Lista de banidos: /my_server → 🚫 Lista de banidos do servidor
""",

"server_ban_notify": """
🚫 Você foi banido no servidor <b>«{name}»</b>.
Você não pode mais solicitar a senha deste servidor.
""",

"already_banned": "⚠️ O usuário <code>{user_id}</code> já está banido neste servidor.",

"ban_record_not_found": "Registro não encontrado.",

"log_server_unban": "O usuário {user_id} foi desbanido no servidor «{name}»",

"server_unban_notify": """
✅ Você foi desbanido no servidor <b>«{name}»</b>.
Agora você pode solicitar a senha novamente.
""",

"unbanned_alert": "✅ Desbanido.",

"avatar_not_photo": "❌ Por favor, envie uma <b>foto</b> (não um arquivo).\nPara cancelar, toque em ❌ Cancelar.",

"log_avatar_uploaded": "O avatar do servidor «{name}» foi enviado para moderação",

"avatar_submitted": "📨 <b>Avatar enviado para moderação!</b>\n\nApós a aprovação do administrador, ele aparecerá na ficha do servidor.",

"admin_new_avatar": """
🖼 <b>Novo avatar em moderação!</b>

🖥 Servidor: <b>{name}</b>
👤 Dono: <code>{owner_id}</code>

Use /admin para revisar.
""",

"no_permission": "❌ Você não tem permissão para este comando.",

"no_pending_moderation": "✅ Não há solicitações de moderação.",

"pending_servers_count": "🔍 <b>Servidores em moderação: {count}</b>",

"admin_server_card": """
📛 <b>{name}</b>
📝 {description}
🌐 <code>{ip}</code>
🔑 Senha: <code>{password}</code>
👤 Dono: <code>{owner_id}</code>
🕐 Criado em: {created_at}
""",

"pending_avatars_count": "🖼 <b>Avatares em moderação: {count}</b>",

"avatar_moderation_caption": """
🖼 Avatar do servidor <b>«{name}»</b>
👤 Dono: <code>{owner_id}</code>
""",

"avatar_upload_failed": "⚠️ Não foi possível carregar o avatar do servidor «{name}».",

"server_approved_edit": "✅ Servidor <b>«{name}»</b> aprovado.",

"server_approved_notify": """
✅ <b>Seu servidor «{name}» foi aprovado!</b>
Agora ele está visível na lista /servers
Gerencie-o pelo /my_server
""",

"server_rejected_edit": "❌ Servidor <b>«{name}»</b> rejeitado.",

"server_rejected_notify": """
❌ <b>Seu servidor «{name}» foi rejeitado.</b>

Exclua-o e crie um novo com o comando /create
""",

"avatar_already_processed": "O avatar já foi processado.",

"avatar_approved_edit": "✅ O avatar do servidor <b>«{name}»</b> foi aprovado.",

"avatar_approved_alert": "✅ Avatar aprovado.",

"avatar_approved_notify": """
✅ <b>O avatar do seu servidor foi aprovado!</b>

🖥 Servidor: <b>{name}</b>
Ele já está sendo exibido em /my_server.
""",

"avatar_rejected_edit": "❌ O avatar do servidor <b>«{name}»</b> foi rejeitado.",

"avatar_rejected_alert": "❌ Avatar rejeitado.",

"avatar_rejected_notify": """
❌ <b>O avatar do seu servidor foi rejeitado.</b>

🖥 Servidor: <b>{name}</b>
Você pode enviar outro pelo /my_server.
""",

"global_ban_success": "🚫 O usuário <code>{user_id}</code> foi banido globalmente.",

"global_ban_notify": "🚫 <b>Você foi banido do bot por um administrador.</b>",

"already_globally_banned": "⚠️ O usuário <code>{user_id}</code> já está banido.",

"global_unban_success": "✅ O usuário <code>{user_id}</code> foi desbanido.",

"global_unban_notify": "✅ <b>Seu banimento foi removido. Você pode usar o bot novamente.</b>",

"not_globally_banned": "⚠️ O usuário <code>{user_id}</code> não estava banido.",

"global_ban_prompt": "🚫 <b>Ban global</b>\n\nDigite o ID do Telegram do usuário:\n<i>Para cancelar: /cancel</i>",

"global_unban_prompt": "✅ <b>Desban global</b>\n\nDigite o ID do Telegram do usuário:\n<i>Para cancelar: /cancel</i>",

"global_ban_prompt_btn": "🚫 <b>Ban global</b>\n\nDigite o ID do Telegram do usuário:\n<i>Para cancelar: /cancel ou ❌ Cancelar</i>",

"global_unban_prompt_btn": "✅ <b>Desban global</b>\n\nDigite o ID do Telegram do usuário:\n<i>Para cancelar: /cancel ou ❌ Cancelar</i>",

"enter_numeric_id": "❌ Digite o ID numérico do Telegram:",

"global_banlist_empty": "✅ A lista global de banidos está vazia.",

"global_banlist_header": "🚫 <b>Lista global de banidos ({count}):</b>\n",

"global_banlist_entry": "• <code>{user_id}</code>  desde {date}",

"logs_empty": "📋 O registro está vazio.",

"logs_header": "📋 <b>Registro de eventos (últimos 40):</b>\n",

"logs_entry": "<code>{datetime}</code> {label}\n   👤 {actor}{server}{details}",

"logs_truncated": "\n\n<i>...cortado</i>",

"nothing_to_cancel": "Nada para cancelar.",

"action_cancelled": "🚫 Ação cancelada.",

"btn_edit_server": "✏️ Editar dados",

"btn_edit_pending": "✏️ Alterações (⏳ em moderação)",

"edit_pending_line": "✏️ Alterações: ⏳ em moderação",

"edit_menu": """
✏️ <b>O que deseja alterar no servidor «{name}»?</b>

As alterações só terão efeito após revisão de um administrador.
""",

"btn_edit_name": "📛 Nome",

"btn_edit_description": "📝 Descrição",

"btn_edit_ip": "🌐 Endereço IP",

"edit_already_pending": "⏳ O servidor já tem alterações em moderação. Aguarde a decisão do administrador.",

"edit_prompt_name": """
📛 Digite o novo <b>nome</b> do servidor (máx. 64 caracteres):

<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"edit_prompt_description": """
📝 Digite a nova <b>descrição</b> do servidor (máx. 512 caracteres):

<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"edit_prompt_ip": """
🌐 Digite o novo <b>endereço IP</b> do servidor:

<i>Para cancelar, toque em ❌ Cancelar ou digite /cancel</i>
""",

"log_edit_requested": "@{username} propôs um novo valor para o campo «{field}» do servidor «{name}»",

"edit_submitted": """
📨 <b>Alteração enviada para moderação!</b>

Após a aprovação do administrador, o novo valor aparecerá na ficha do servidor.
""",

"admin_new_edit": """
✏️ <b>Nova edição em moderação!</b>

🖥 Servidor: <b>{name}</b>
👤 Dono: <code>{owner_id}</code>

{diff}

Use /admin para revisar.
""",

"edit_diff_line": "<b>{field}:</b>\n  antes: {old}\n  agora: {new}",

"field_name": "Nome",

"field_description": "Descrição",

"field_ip": "Endereço IP",

"pending_edits_count": "✏️ <b>Edições em moderação: {count}</b>",

"admin_edit_card": """
✏️ <b>Edição do servidor «{name}»</b>
👤 Dono: <code>{owner_id}</code>

{diff}
""",

"edit_already_processed": "A alteração já foi processada ou não existe.",

"edit_approved_edit": "✅ As alterações do servidor <b>«{name}»</b> foram aprovadas.",

"edit_approved_alert": "✅ Alterações aprovadas.",

"edit_approved_notify": """
✅ <b>As alterações do seu servidor foram aprovadas!</b>

🖥 Servidor: <b>{name}</b>
Os novos dados já estão sendo exibidos na ficha.
""",

"edit_rejected_edit": "❌ As alterações do servidor <b>«{name}»</b> foram rejeitadas.",

"edit_rejected_alert": "❌ Alterações rejeitadas.",

"edit_rejected_notify": """
❌ <b>As alterações do seu servidor foram rejeitadas.</b>

🖥 Servidor: <b>{name}</b>
Os dados anteriores continuam válidos. Você pode propor uma nova edição pelo /my_server.
""",

}
