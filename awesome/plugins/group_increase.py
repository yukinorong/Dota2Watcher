from nonebot import on_notice, NoticeSession
import common_conf

# 将函数注册为群成员增加通知处理器
@on_notice('group_increase')
async def _(session: NoticeSession):
    if common_conf.OPEN_GROUP == session.event.group_id:
        # 发送欢迎消息
        await session.send('欢迎新来的max老哥～')