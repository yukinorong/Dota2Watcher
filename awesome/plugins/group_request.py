from nonebot import on_request, RequestSession
import common_conf

# 将函数注册为群请求处理器
@on_request('group')
async def _(session: RequestSession):
    # 判断验证信息是否符合要求
    if 'max' in session.event.comment and common_conf.OPEN_GROUP == session.event.group_id:
        # 验证信息正确，同意入群
        await session.approve()
        return
    # 验证信息错误，拒绝入群
    await session.reject('请说暗号')

# 将函数注册为群请求处理器
@on_request('friend')
async def _(session: RequestSession):
    # 判断验证信息是否符合要求
    if 'max' in session.event.comment:
        # 验证信息正确，同意入群
        await session.approve()
        return
    # 验证信息错误，拒绝入群
    await session.reject('请说暗号')