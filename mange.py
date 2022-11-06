from telethon import functions
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.types import Channel, Chat, User
from sbb_b import sbb_b
from sbb_b.core.managers import edit_delete, edit_or_reply
from sbb_b.helpers.utils import mentionuser


async def get_group_call(chat):
    if isinstance(chat, Channel):
        result = await catub(functions.channels.GetFullChannelRequest(channel=chat))
    elif isinstance(chat, Chat):
        result = await catub(functions.messages.GetFullChatRequest(chat_id=chat.id))
    return result.full_chat.call


async def chat_vc_checker(event, chat, edits=True):
    if isinstance(chat, User):
        await edit_delete(event, "- المكالمة الصوتية غير متاحة في المجموعة الخاصة")
        return None
    result = await get_group_call(chat)
    if not result:
        if edits:
            await edit_delete(event, "**- لا توجد دردشة صوتية في هذه المجموعة**")
        return None
    return result


async def parse_entity(entity):
    if entity.isnumeric():
        entity = int(entity)
    return await catub.get_entity(entity)


@sbb_b.ar_cmd(pattern="تشغيل المكالمة")
async def start_vc(event):
    vc_chat = await sbb_b.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat, False)
    if gc_call:
        return await edit_delete(event, "**- المكالمة الصوتية بالأصل موجودة**")
    try:
        await sbb_b(
            functions.phone.CreateGroupCallRequest(
                peer=vc_chat,
                title="مكالمة جمثون",
            )
        )
        await edit_delete(event, "**- تم بنجاح تشغيل المكالمة الصوتية**")
    except ChatAdminRequiredError:
        await edit_delete(event, "- عليك أن تكون مشرف اولا", time=20)


@sbb_b.ar_cmd(pattern="انهاء المكالمة")
async def end_vc(event):
    vc_chat = await sbb_b.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    try:
        await sbb_b(functions.phone.DiscardGroupCallRequest(call=gc_call))
        await edit_delete(event, "**- تم بنجاح الغاء المكالمة الصوتية**")
    except ChatAdminRequiredError:
        await edit_delete(event, "- عليك أن تكون مشرف اولا", time=20)


@sbb_b.ar_cmd(pattern="دعوة ?(.*)?")
async def inv_vc(event):
    users = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    vc_chat = await sbb_b.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not users:
        if not reply:
            return await edit_delete("**يجب عليك الرد على المستخدم او وضع معرفه مع الامر**")
        users = reply.from_id
    await edit_or_reply(event, "**- تم دعوة المستخدم الى المكالمة**")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)
    try:
        await sbb_b(
            functions.phone.InviteToGroupCallRequest(call=gc_call, users=user_list)
        )
        await edit_delete(event, "**- تم دعوة المستخدمين الى المكالمة**")
    except UserAlreadyInvitedError:
        return await edit_delete(event, "**- المستحدم بالأصل مدعو لهذه المكالمة**", time=20)


@sbb_b.ar_cmd(pattern="معلومات المكالمة")
async def info_vc(event):
    vc_chat = await sbb_b.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    await edit_or_reply(event, "**- جار الحصول على معلومات المكالمة**")
    call_details = await sbb_b(
        functions.phone.GetGroupCallRequest(call=gc_call, limit=1)
    )
    grp_call = "**معلومات المكالمة الصوتية:**\n\n"
    grp_call += f"**العنوان :** {call_details.call.title}\n"
    grp_call += f"**عدد المشاركين :** {call_details.call.participants_count}\n\n"

    if call_details.call.participants_count > 0:
        grp_call += "**المشاركين**\n"
        for user in call_details.users:
            nam = f"{user.first_name or ''} {user.last_name or ''}"
            grp_call += f"  ● {mentionuser(nam,user.id)} - `{user.id}`\n"
    await edit_or_reply(event, grp_call)


@sbb_b.ar_cmd(pattern="عنوان?(.*)?")
async def title_vc(event):
    title = event.pattern_match.group(1)
    vc_chat = await sbb_b.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not title:
        return await edit_delete("**- عليك وضع اسم مع الامر اولا**")
    await sbb_b(functions.phone.EditGroupCallTitleRequest(call=gc_call, title=title))
    await edit_delete(event, f"-تم بنجاح تغيير اسم المكالمة الصوتية الى **{title}**")
