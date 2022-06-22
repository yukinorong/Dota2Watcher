from nonebot import on_command, CommandSession
import common_conf

# on_command 装饰器将函数声明为一个命令处理器
@on_command('get', aliases=('整点', '来点'))
async def ghs(session: CommandSession):
    if common_conf.OPEN_GROUP == session.event.group_id :
        # 取得消息的内容，并且去掉首尾的空白符
        data = session.current_arg_text.strip()

        if not data:
            data = (await session.aget(prompt='你想要啥？')).strip()
            # 如果用户只发送空白符，则继续询问
            while not data:
                data = (await session.aget(prompt='你想要啥？？？')).strip()

        answer = await get_answer_from_data(data)
        # 向用户发送天气预报
        await session.send(answer)

async def get_answer_from_data(data) :
    answer = ""
    if data == "色图" :
        answer = get_pic()
    elif data == "段子" :
        answer = get_joke()
    else :
        answer = "爷看不懂"
    return answer

def get_pic() :
    return "pic"

def get_joke():
    return "joke"
