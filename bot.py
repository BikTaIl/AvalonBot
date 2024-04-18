import random
import math
import asyncio
import bot_data as bd
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import executor

bot = Bot(token=bd.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class TestStates(Helper):
    mode = HelperMode.snake_case
    WAIT_LOBBY = ListItem()
    WAIT_NAME = ListItem()
    FLUDD = ListItem()
    IN_GAME = ListItem()
    WAIT_SETTINGS = ListItem()
    WAIT__BAN = ListItem()


async def struc(message: int):
    lobby_id = bd.id_to_lobby[message]
    lobby_settings = bd.lobby_to_settings[lobby_id]
    roles = lobby_settings['roles']

    role_str = ', '.join(roles)
    roles_message = f'Роли, участвующие в игре: {role_str}'
    roles_msg = await bot.send_message(message, roles_message)

    if message not in bd.id_to_delete1:
        bd.id_to_delete1[message] = []
    bd.id_to_delete1[message].append(roles_msg)

    lake_lady_enabled = lobby_settings['Lake_lady']
    eskalibur_enabled = lobby_settings['Eskalibur']

    options_message = f'Опциональные механики: Леди Озера - {"" if lake_lady_enabled else "не"}включена, Эскалибур - {"" if eskalibur_enabled else "не"}включен'
    options_msg = await bot.send_message(message, options_message)

    bd.id_to_delete1[message].append(options_msg)


async def delete_mes(message: int):
    if message in bd.id_to_delete:
        while bd.id_to_delete[message]:
            await bd.id_to_delete[message][0].delete()
            bd.id_to_delete[message] = bd.id_to_delete[message][1:]


async def delete1_mes(message: int):
    if message in bd.id_to_delete1:
        while bd.id_to_delete1[message]:
            await bd.id_to_delete1[message][0].delete()
            bd.id_to_delete1[message].pop(0)


async def check_user(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if message.from_user.id in bd.ban or message.from_user.id in bd.id_in_game:
        return True
    return False


async def check_user1(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    return message.from_user.id in bd.ban


async def missions(message: str):
    arr_players = bd.lobby_to_info[message]['round']
    kb1 = InlineKeyboardMarkup()
    kb2 = InlineKeyboardMarkup()
    butt = InlineKeyboardButton('Собрать поход', callback_data='start_mis')
    kb2.add(butt)
    lanc = False
    lobby_info = bd.lobby_to_info[message]
    red_players = lobby_info['red']
    blue_players = lobby_info['blue']
    R_Lancelot = lobby_info['R_Lancelot']
    B_Lancelot = lobby_info['B_Lancelot']
    changes = lobby_info['changes']
    id_to_role = bd.id_to_role
    id_to_name = bd.id_to_name
    missions = bd.missions
    cnt = lobby_info['cnt']

    if R_Lancelot != -1 and red_players + blue_players >= 2 and changes[red_players + blue_players - 2]:
        lanc = True
        id_to_role[B_Lancelot], id_to_role[R_Lancelot] = id_to_role[R_Lancelot], id_to_role[B_Lancelot]
        await bot.send_message(B_Lancelot, 'Теперь ваша роль - 🟥Ланселот')
        await bot.send_message(B_Lancelot, 'Теперь ваша цель, вычислить 🟦Мерлина, или провалить 3 похода')
        await bot.send_message(R_Lancelot, 'Теперь ваша роль - 🟦Ланселот')
        await bot.send_message(R_Lancelot, 'Теперь ваша цель собрать 3 успешных похода 3 похода')
        lobby_info['B_Lancelot'], lobby_info['R_Lancelot'] = R_Lancelot, B_Lancelot
    for k in range(len(arr_players)):
        i = arr_players[k]
        butt = InlineKeyboardButton(id_to_name[i], callback_data=('button' + str(k)))
        kb1.add(butt)
        await bot.send_message(int(i), bd.makar_str)
        if lanc:
            await bot.send_message(int(i), 'Ланселоты поменялись ролями')
        await bot.send_message(int(i), 'Поход собирает - ' + id_to_name[arr_players[cnt]] + ' из ' + str(
            missions[len(arr_players) - 5][red_players + blue_players]) + ' человек')
        if len(arr_players) >= 7 and missions[len(arr_players) - 5][red_players + blue_players] == 3:
            await bot.send_message(int(i), 'В этом походе нужно 2 провала, чтобы поход был провален')
        if lobby_info['skip'] == 4:
            await bot.send_message(int(i), 'Осторожнее, если вы пропустите этот поход, то красные выиграют')
    lobby_info['mission'] = []
    msg1 = await bot.send_message(arr_players[cnt], text='Выберите людей, которых возьмете в поход', reply_markup=kb1)
    msg2 = await bot.send_message(arr_players[cnt], text='Нажмите, чтобы собрать поход', reply_markup=kb2)
    bd.id_to_delete[arr_players[cnt]].append(msg1)
    bd.id_to_delete[arr_players[cnt]].append(msg2)


async def make_mission(message: str):
    bd.lobby_to_info[message]['skip'] = 0
    kb1 = InlineKeyboardMarkup()
    kb2 = InlineKeyboardMarkup()
    blue = InlineKeyboardButton('Успех', callback_data='success')
    red = InlineKeyboardButton('Провал', callback_data='fail')
    bd.lobby_to_info[message]['success'] = 0
    bd.lobby_to_info[message]['fail'] = 0
    kb1.add(red)
    kb1.add(blue)
    kb2.add(blue)

    for i in bd.lobby_to_info[message]['mission']:
        if bd.id_to_role[i][0] == '🟦':
            msg_text = 'Определите исход похода'
            reply_markup = kb2
        else:
            msg_text = 'Определите исход похода'
            reply_markup = kb1

        msg = await bot.send_message(i, text=msg_text, reply_markup=reply_markup)
        bd.id_to_delete[i].append(msg)


async def end_game(message: str):
    arr_players = bd.lobby_to_info[message]['round']
    if bd.lobby_to_info[message]['skip'] == 5 or bd.lobby_to_info[message]['red'] == 3:
        for i in arr_players:
            await bot.send_message(i, 'Красные победили')
            bd.id_in_game.remove(i)
        for i in arr_players:
            state = dp.current_state(user=i)
            await state.set_state(TestStates.all()[0])
            await bot.send_message(i, 'Роли:')
            for j in arr_players:
                await bot.send_message(i, f"{bd.id_to_name[j]} - {bd.id_to_role[j]}")
    else:
        kb1 = InlineKeyboardMarkup()
        rd = []
        for k, i in enumerate(arr_players):
            if bd.id_to_role[i][0] == '🟦':
                butt = InlineKeyboardButton(bd.id_to_name[i], callback_data=f'button1{k}')
                kb1.add(butt)
            else:
                rd.append(bd.id_to_name[i])
        ans = 'Красные - '
        for i, name in enumerate(rd):
            ans += name
            if i < len(rd) - 1:
                ans += ', '
        for i in arr_players:
            await bot.send_message(i, 'Красные стреляют')
            await bot.send_message(i, ans)
            if bd.id_to_role[i][1] == 'А':
                msg = await bot.send_message(i, text='Выберите игрока в которого вы выстрелите', reply_markup=kb1)
                bd.id_to_delete[i].append(msg)
    bd.lobby_in_game.remove(message)


async def lake_lady(message: str):
    kb1 = InlineKeyboardMarkup()
    bd.lobby_to_info[message]['WhoWasLady'].append(bd.lobby_to_info[message]['WhoLady'])
    arr_players = bd.lobby_to_info[message]['round']
    for i in arr_players:
        if i not in bd.lobby_to_info[message]['WhoWasLady']:
            butt = InlineKeyboardButton(i, callback_data='button2' + str(arr_players.index(i)))
            kb1.add(butt)
    msg = await bot.send_message(bd.lobby_to_info[message]['WhoLady'], 'Выберите роль, цвет которой хотите узнать',
                                 reply_markup=kb1)
    bd.id_to_delete[bd.lobby_to_info[message]['WhoLady']].append(msg)


@dp.message_handler(state='*', commands=['ban'])
async def ban(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    user_id = str(message.from_user.id)

    if user_id in (bd.my_id, bd.makar_id):
        await message.answer('Напишите ник пользователя, которому уготована кара')
        await state.set_state(TestStates.all()[5])
    else:
        await message.answer('Ха, хорошая попытка, но у вас недостаточно прав')


@dp.message_handler(state=TestStates.WAIT__BAN)
async def wait_ban(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if message.text in bd.name_to_id:
        if bd.name_to_id[message.text] == message.from_id:
            await message.answer('Что посеешь, то и пожнешь')
        else:
            user_id = bd.name_to_id[message.text]
            if user_id in bd.ban:
                await message.answer('Ок, я разбанил данного пользователя')
                await bot.send_message(user_id, 'Вы были разбанены')
                bd.ban.remove(user_id)
            else:
                if user_id == bd.my_id:
                    bd.ban.append(message.from_id)
                    await bot.send_message(message.from_id, 'Вы были забанены')
                else:
                    bd.ban.append(user_id)
                    await bot.send_message(user_id, 'Вы были забанены')
                await message.answer('Ок, я забанил данного пользователя')
    else:
        await message.answer('Такого пользователя не существует')
    await state.set_state(TestStates.all()[0])


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if await check_user(message):
        return

    bd.id_to_delete.setdefault(message.from_user.id, [])
    bd.id_to_delete1.setdefault(message.from_user.id, [])

    await message.answer('Привет, этот бот умеет проводить игру Авалон. Для начала напишите свое имя')
    await state.set_state(TestStates.all()[3])


@dp.message_handler(state=TestStates.WAIT_NAME)
async def give_name(mes1: types.Message):
    if await check_user(mes1):
        return
    state = dp.current_state(user=mes1.from_user.id)

    text = mes1.text.strip()
    words = text.split()
    if len(words) == 1 and text[0] != '/' and len(text) <= 15:
        name = words[0]
        if name not in bd.name_to_id:
            if mes1.from_id in bd.id_to_name:
                bd.name_to_id.pop(bd.id_to_name[mes1.from_id])
                bd.id_to_name.pop(mes1.from_id)
            bd.id_to_name[mes1.from_id] = name
            bd.name_to_id[name] = mes1.from_id
            await mes1.answer('Ок, вас зовут ' + name)
            await state.set_state(TestStates.all()[0])
        else:
            await mes1.answer('Это имя уже занято')
    else:
        await mes1.answer('Вы неправильно ввели имя')


@dp.message_handler(state=TestStates.WAIT_LOBBY)
async def set_lobby(message: types.Message):
    if await check_user(message):
        return

    lobby = message.text
    if lobby in bd.lobbys:
        if lobby in bd.lobby_in_game:
            await message.answer('В данное лобби нельзя сейчас присоединиться, потому что в нем идет игра')
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(TestStates.all()[0])
        else:
            user_id = message.from_user.id
            if user_id in bd.id_to_lobby:
                lobby_id = bd.id_to_lobby[user_id]
                bd.lobby_to_info[lobby_id]['round'] = []
                bd.lobbys[lobby_id].remove(user_id)
                if len(bd.lobbys[lobby_id]) >= 1:
                    await bot.send_message(bd.lobbys[lobby_id][0],
                                           f'Ваше лобби покинул {bd.id_to_name[user_id]}, в вашем лобби {len(bd.lobbys[lobby_id])} человек')
            state = dp.current_state(user=user_id)
            await message.answer(f"Вы присоеденились в лобби {lobby}")
            if len(bd.lobbys[lobby]) == 0:
                await message.answer("Вы являетесь админом данного лобби")
            else:
                await bot.send_message(bd.lobbys[lobby][0],
                                       f'В ваше лобби присоединился {bd.id_to_name[user_id]}, в вашем лобби {len(bd.lobbys[lobby]) + 1} человек')
            bd.lobbys[lobby].append(user_id)
            bd.id_to_lobby[user_id] = lobby
            await state.set_state(TestStates.all()[0])
    else:
        await message.answer(f"Вы присоеденились в лобби {lobby}")
        await message.answer("Вы являетесь админом данного лобби")
        bd.lobbys[lobby] = [message.from_user.id]
        bd.id_to_lobby[message.from_user.id] = lobby
        state = dp.current_state(user=message.from_user.id)
        bd.lobby_to_sem[bd.id_to_lobby[message.from_user.id]] = asyncio.Lock()
        bd.lobby_to_info[bd.id_to_lobby[message.from_user.id]] = {}
        await state.set_state(TestStates.all()[0])
    bd.lobby_to_info[bd.id_to_lobby[message.from_user.id]]['round'] = []


@dp.message_handler(state=TestStates.FLUDD, commands=['join'])
async def join(message: types.Message):
    if await check_user(message):
        return
    state = dp.current_state(user=message.from_user.id)
    await message.answer('Enter the lobby name')  # Description: Changed the message text to be more descriptive
    await state.set_state(TestStates.all()[2])


@dp.message_handler(state=TestStates.FLUDD, commands=['info'])
async def info(message: types.Message):
    if await check_user(message):
        return

    state = dp.current_state(user=message.from_user.id)

    lobby_id = bd.id_to_lobby.get(message.from_user.id)
    if lobby_id:
        lobby_members = bd.lobbys[lobby_id]
        num_members = len(lobby_members)
        members = ' '.join(str(bd.id_to_name[i]) for i in lobby_members)
        admin = bd.id_to_name[lobby_members[0]]

        await message.answer(f'В вашем лобби {num_members} человек: {members}')
        await message.answer(f'Админом является {admin}')
    else:
        await message.answer('Вы не находитесь в лобби')


@dp.message_handler(state=TestStates.FLUDD, commands=['start_game'])
async def start_game(message: types.Message):
    if await check_user(message):
        return
    if message.from_user.id in bd.id_to_lobby:
        if len(bd.lobbys[bd.id_to_lobby[message.from_user.id]]) < 5:
            await message.answer('Вас слишком мало, чтобы начать игру')
        elif len(bd.lobbys[bd.id_to_lobby[message.from_user.id]]) > 10:
            await message.answer('Вас слишком много, чтобы начать игру')
        else:
            if bd.lobbys[bd.id_to_lobby[message.from_user.id]][0] == message.from_user.id:
                msg0 = await message.answer('Ок, вы можете изменить настройки игры')
                kb1 = InlineKeyboardMarkup()
                kb2 = InlineKeyboardMarkup()
                kb3 = InlineKeyboardMarkup()
                bt1 = InlineKeyboardButton('🟦Персиваль', callback_data='pers')
                bt2 = InlineKeyboardButton('🟥Моргана', callback_data='morg')
                bt3 = InlineKeyboardButton('🟥Оберон', callback_data='ober')
                bt4 = InlineKeyboardButton('🟥Мордред', callback_data='mord')
                bt5 = InlineKeyboardButton('🟦🟥Ланселот', callback_data='lanc')
                # bt6 = InlineKeyboardButton('Леди Озера', callback_data='lo')
                # bt7 = InlineKeyboardButton('Эскалибур', callback_data='esk')
                bt8 = InlineKeyboardButton('Начать игру', callback_data='start')
                bt9 = InlineKeyboardButton('Ланселоты видят друг друга', callback_data='los')
                bt10 = InlineKeyboardButton('Закрытое голосование', callback_data='vote')
                kb1.add(bt1)
                kb1.add(bt2)
                kb1.add(bt3)
                kb1.add(bt4)
                kb1.add(bt5)
                # kb2.add(bt6)
                # kb2.add(bt7)
                kb2.add(bt9)
                kb2.add(bt10)
                kb3.add(bt8)
                if not bd.id_to_lobby[message.from_user.id] in bd.lobby_to_settings:
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]] = {}
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'] = []
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['Lake_lady'] = False
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['Eskalibur'] = False
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['Lancelots'] = False
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['CloseVote'] = False
                x = math.floor(len(bd.lobbys[bd.id_to_lobby[message.from_user.id]]) / 2.3) - 1
                bd.lobby_to_info[bd.id_to_lobby[message.from_user.id]]['changes'] = [True, True, False, False, False]
                if len(bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles']) != len(
                        bd.lobbys[bd.id_to_lobby[message.from_id]]):
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'] = []
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'].append('🟦Мерлин')
                    bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'].append('🟥Ассасин')
                    for i in range(x):
                        bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'].append('🟥Приспешник зла')
                    x = len(bd.lobbys[bd.id_to_lobby[message.from_user.id]]) - x - 2
                    for i in range(x):
                        bd.lobby_to_settings[bd.id_to_lobby[message.from_user.id]]['roles'].append('🟦Рыцарь')
                msg1 = await message.answer('Роли:', reply_markup=kb1)
                msg2 = await message.answer('Опциональные механики:', reply_markup=kb2)
                msg3 = await message.answer('Нажмите, чтобы начать игру:', reply_markup=kb3)
                bd.id_to_delete[message.from_user.id].append(msg1)
                bd.id_to_delete[message.from_user.id].append(msg2)
                bd.id_to_delete[message.from_user.id].append(msg3)
                bd.id_to_delete[message.from_user.id].append(msg0)
                state = dp.current_state(user=message.from_user.id)
                await state.set_state(TestStates.all()[4])
                await struc(message.from_user.id)
            else:
                await message.answer('Вы не являетесь админом данного лобби и не можете начать игру')
    else:
        await message.answer('Вы не находитесь в лобби')


@dp.message_handler(state='*', commands=['rules'])
async def start_game(message: types.Message):
    if await check_user1(message):
        return
    await message.answer('В игре есть синие и красные, красных 1/3 от кол-ва человек округленное вверх. Среди синих есть главный – Мерлин. Среди красных – Ассасин. Остальные роли опциональны. Вначале каждому присылается набор имен, которые видит ваша роль. У каждой роли свой набор. Чтобы увидеть, кто кого видит, напишите /rules_night.\n Затем происходят походы. Цель синих собрать три синих похода, красных – три красных. Поход собирает лидер, лидерство передается по кругу. Собирается определённое количество человек, зависящее от общего количества человек и номера похода, чтобы узнать конкретнее напишите /rules_missions.\n    После того, как поход был предложен, происходит голосование за этот поход. Каждый голосует За или Против.\n Далее происходит сам поход. В нем каждый участник этого похода выбирает, Успешным будет этот поход или Провальным. У синих выбора нет, они выбирают только Успех, а красные могут выбрать из двух вариантов. Если в походе хотя бы один красный (или два в некоторых походах, в каких именно можно узнать, написав /rules_missions), то поход красный, иначе синий.\n    Если собирается три красных похода, то красные сразу выигрывают. Если три синих похода, то у красных есть возможность произвести один выстрел. Попав в Мерлина, они выигрывают, не попав, выигрывают синие.')


@dp.message_handler(state='*', commands=['rules_missions'])
async def start_game(message: types.Message):
    if await check_user1(message):
        return
    await message.answer(
        '5 человек - 2|3|2|3|3\n6 человек - 2|3|4|3|4\n7 человек - 2|3|3|4|4\n8 человек - 3|4|4|5|5\n9 человек - 3|4|4|5|5\n10 человек - 3|4|4|5|5\nПри игре с >=7 человек в четвертом походе нужно 2 провала, чтобы поход был провален')


@dp.message_handler(state='*', commands=['rules_night'])
async def start_game(message: types.Message):
    if await check_user1(message):
        return
    await message.answer(
        '🟥Моргана - 🟥Ассасин, 🟥Мордред, 🟥Ланселот, 🟥Приспешник зла\n🟥Ассасин - 🟥Моргана, 🟥Мордред, 🟥Ланселот, 🟥Приспешник зла\n🟥Приспешник зла - 🟥Ассасин, 🟥Моргана, 🟥Мордред, 🟥Ланселот\n🟥Мордред - 🟥Ассасин, 🟥Моргана, 🟥Ланселот, 🟥Приспешник зла\n🟥Ланселот - Никого не видит\n🟥Оберон - Никого не видит\n🟦Мерлин - 🟥Ассасин, 🟥Моргана, 🟥Ланселот, 🟥Приспешник зла\n🟦Персиваль - 🟦Мерлин, 🟥Моргана\n🟦Ланселот - Никого не видит\n🟦Рыцарь - Никого не видит')


@dp.message_handler(state='*', commands=['roles'])
async def start_game(message: types.Message):
    if await check_user1(message):
        return
    await message.answer(
        '🟦Мерлин. Ты синий.\nТы видишь: 🟥Ассасин, 🟥Оберон, 🟥Моргана, 🟥Ланселот, 🟥Приспешник зла.\nТвоя цель – помочь мирным собирать синие походы, однако нужно не спалиться перед красными, так как их цель вычислить и убить тебя.\n\n🟦Персиваль. Ты синий.\nТы видишь: 🟦Мерлин, 🟥Моргана.\nТвоя цель – понять, кто Мерлин, и помочь мирным собрать синие походы. \n\n🟥Ассасин. Ты красный.\nТы видишь: 🟥Моргана, 🟥Мордред, 🟥Ланселот, 🟥Приспешник зла.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода.\n\n🟥Моргана. Ты красный.\nТы видишь  🟥Ассасин, 🟥Мордред, 🟥Ланселот, 🟥Приспешник зла.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода. \n\n🟥Оберон. Ты красный.\nТы никого не видишь.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода. \n\n🟥Мордред. Ты красный.\nТы видишь: 🟥Ассасин, 🟥Моргана, 🟥Ланселот, 🟥Приспешник зла. \nТы единственный красный, которого не видит Мерлин.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода.\n\n🟦Рыцарь. Ты синий.\nТы никого не видишь, и тебя никто не видит.\nТебе нужно постараться вычислить всех и собирать/голосовать за нужные походы.\n\n🟥Приспешник зла. Ты красный.\nТы видишь: 🟥Ассасин, 🟥Моргана, 🟥Мордред, 🟥Ланселот.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода.\n\n🟥Ланселот. Ты красный.\nТы никого не видишь, но красные и 🟦Мерлин видят тебя.\nТвоя цель – вычислить Мерлина и убить его или просто собрать 3 красных похода, перед 3, 4 и 5 походами ты можешь поменяться ролью с 🟦Ланселотом, твоя цель игры также меняется.\n\n🟦Ланселот. Ты синий.\nТы никого не видишь, и тебя никто не видит.\nТебе нужно постараться вычислить всех и собирать/голосовать за нужные походы, перед 3, 4 и 5 походами ты можешь поменяться ролью с 🟥Ланселотом, твоя цель игры также меняется.\n')


@dp.callback_query_handler(text='morg', state='*')
async def Morgana_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if not '🟥Моргана' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
        if '🟥Приспешник зла' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Моргана')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Приспешник зла')
            msg = await bot.send_message(callback_query.from_user.id, 'Ок, я добавил роль 🟥Моргана в игру')
        else:
            msg = await bot.send_message(callback_query.from_user.id,
                                         'Красных ролей слишком много, я не могу добавить 🟥Моргану')
    else:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Моргана')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Приспешник зла')
        msg = await bot.send_message(callback_query.from_user.id, "Ок, я удалил роль 🟥Моргана из игры")
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='ober', state='*')
async def Oberon_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if not '🟥Оберон' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
        if '🟥Приспешник зла' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Оберон')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Приспешник зла')
            msg = await bot.send_message(callback_query.from_user.id, 'Ок, я добавил роль 🟥Оберон в игру')
        else:
            msg = await bot.send_message(callback_query.from_user.id,
                                         'Красных ролей слишком много, я не могу добавить 🟥Оберона')
    else:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Оберон')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Приспешник зла')
        msg = await bot.send_message(callback_query.from_user.id, "Ок, я удалил роль 🟥Оберон из игры")
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='mord', state='*')
async def Mordred_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if not '🟥Мордред' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
        if '🟥Приспешник зла' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Мордред')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Приспешник зла')
            msg = await bot.send_message(callback_query.from_user.id, 'Ок, я добавил роль 🟥Мордред в игру')
        else:
            msg = await bot.send_message(callback_query.from_user.id,
                                         'Красных ролей слишком много, я не могу добавить 🟥Мордреда')
    else:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Мордред')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Приспешник зла')
        msg = await bot.send_message(callback_query.from_user.id, "Ок, я удалил роль 🟥Мордред из игры")
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='pers', state='*')
async def Persival_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if not '🟦Персиваль' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟦Персиваль')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟦Рыцарь')
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, я добавил роль 🟦Персиваль в игру')
    else:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟦Персиваль')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟦Рыцарь')
        msg = await bot.send_message(callback_query.from_user.id, "Ок, я удалил роль 🟦Персиваль из игры")
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='lanc', state='*')
async def Lancelot_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if not '🟥Ланселот' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
        if '🟥Приспешник зла' in bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles']:
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Ланселот')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Приспешник зла')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟦Ланселот')
            bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟦Рыцарь')
            msg = await bot.send_message(callback_query.from_user.id, 'Ок, я добавил роль 🟦🟥Ланселот в игру')
        else:
            msg = await bot.send_message(callback_query.from_user.id,
                                         'Красных ролей слишком много, я не могу добавить 🟦🟥Ланселота')
    else:
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟦Ланселот')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟥Приспешник зла')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].remove('🟥Ланселот')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['roles'].append('🟦Рыцарь')
        msg = await bot.send_message(callback_query.from_user.id, "Ок, я удалил роль 🟦🟥Ланселот из игры")
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='lo', state='*')
async def Lake_Lady_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lake_lady']:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, я выключил механику Леди Озера')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lake_lady'] = False
    else:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, я включил механику Леди Озера')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lake_lady'] = True
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='esk', state='*')
async def Esk_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Eskalibur']:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, я выключил механику Эскалибур')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Eskalibur'] = False
    else:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, я включил механику Эскалибур')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Eskalibur'] = True
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='los', state='*')
async def Lanc_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lancelots']:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, Ланселоты не будут знать друг друга')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lancelots'] = False
    else:
        msg = await bot.send_message(callback_query.from_user.id, 'Ок, Ланселоты будут знать друг друга')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['Lancelots'] = True
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='vote', state='*')
async def Vote_button(callback_query: types.CallbackQuery):
    if await check_user(callback_query):
        return
    await bot.answer_callback_query(callback_query.id)
    await delete1_mes(callback_query.from_user.id)
    msg = types.Message
    if bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['CloseVote']:
        msg = await bot.send_message(callback_query.from_user.id, 'Я включил открытое голосование')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['CloseVote'] = False
    else:
        msg = await bot.send_message(callback_query.from_user.id, 'Я включил закрытое голосование')
        bd.lobby_to_settings[bd.id_to_lobby[callback_query.from_user.id]]['CloseVote'] = True
    await struc(callback_query.from_user.id)
    bd.id_to_delete1[callback_query.from_user.id].append(msg)


@dp.callback_query_handler(text='start', state='*')
async def real_start_game(message: types.CallbackQuery):
    if await check_user(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    bd.lobby_in_game.append(bd.id_to_lobby[message.from_user.id])
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_roles = bd.lobbys[game_lobby].copy()
    bd.lobby_to_info[game_lobby]['R_Lancelot'] = -1
    bd.lobby_to_info[game_lobby]['B_Lancelot'] = -1
    random.shuffle(arr_roles)
    random.shuffle(bd.lobby_to_info[bd.id_to_lobby[message.from_user.id]]['changes'])
    if len(bd.lobby_to_info[game_lobby]['round']) != len(arr_roles):
        bd.lobby_to_info[game_lobby]['round'] = arr_roles.copy()
        random.shuffle(bd.lobby_to_info[game_lobby]['round'])
        bd.lobby_to_info[game_lobby]['cnt'] = 0
    bd.lobby_to_info[game_lobby]['skip'] = 0
    bd.lobby_to_info[game_lobby]['red'] = 0
    bd.lobby_to_info[game_lobby]['blue'] = 0
    bd.lobby_to_info[game_lobby]['colors'] = ''
    bd.lobby_to_info[game_lobby]['WhoLady'] = bd.lobby_to_info[game_lobby]['round'][
        (bd.lobby_to_info[game_lobby]['cnt'] - 1 + len(arr_roles)) % len(arr_roles)]
    bd.lobby_to_info[game_lobby]['WhoWasLady'] = []
    ans = 'Роли, участвующие в игре - \n'
    ans1 = 'Порядок игроков по кругу - '
    for j in range(len(bd.lobby_to_info[game_lobby]['round'])):
        ans1 += bd.id_to_name[bd.lobby_to_info[game_lobby]['round'][j]]
        if j < len(bd.lobby_to_info[game_lobby]['round']):
            ans1 += ', '
    for j in range(len(bd.lobby_to_settings[game_lobby]['roles'])):
        ans += bd.lobby_to_settings[game_lobby]['roles'][j]
        if j < len(bd.lobby_to_settings[game_lobby]['roles']) - 1:
            ans += ', '
            ans += '\n'
    for i in range(len(arr_roles)):
        await bot.send_message(arr_roles[i], 'Игра начинается!')
        await bot.send_message(arr_roles[i], ans)
        await bot.send_message(arr_roles[i], ans1)
        await bot.send_message(arr_roles[i], 'Твоя роль - ' + bd.lobby_to_settings[game_lobby]['roles'][i])
        await bot.send_message(arr_roles[i], bd.role_to_info[bd.lobby_to_settings[game_lobby]['roles'][i]])
        bd.id_to_role[arr_roles[i]] = bd.lobby_to_settings[game_lobby]['roles'][i]
        bd.id_in_game.append(arr_roles[i])
        bd.id_to_info[arr_roles[i]] = []
        if bd.id_to_role[arr_roles[i]][1] == 'Л' and bd.id_to_role[arr_roles[i]][0] == '🟥':
            bd.lobby_to_info[game_lobby]['R_Lancelot'] = arr_roles[i]
        if bd.id_to_role[arr_roles[i]][1] == 'Л' and bd.id_to_role[arr_roles[i]][0] == '🟦':
            bd.lobby_to_info[game_lobby]['B_Lancelot'] = arr_roles[i]
    for i in range(len(arr_roles)):
        for j in range(len(arr_roles)):
            if i != j:
                edge = bd.id_to_role[arr_roles[i]] + bd.id_to_role[arr_roles[j]]
                if edge in bd.first_night:
                    bd.id_to_info[arr_roles[i]].append(arr_roles[j])
    for i in range(len(arr_roles)):
        random.shuffle(bd.id_to_info[arr_roles[i]])
        ans = 'Ты видел - '
        for j in range(len(bd.id_to_info[arr_roles[i]])):
            ans += bd.id_to_name[bd.id_to_info[arr_roles[i]][j]]
            if j < len(bd.id_to_info[arr_roles[i]]) - 1:
                ans += ', '
        if len(bd.id_to_info[arr_roles[i]]) > 0:
            await bot.send_message(arr_roles[i], ans)
        else:
            await bot.send_message(arr_roles[i], 'Ты никого не видел')
        if bd.id_to_role[arr_roles[i]][0] == '🟥' and bd.id_to_role[arr_roles[i]][1] != 'О' and \
                bd.lobby_to_info[game_lobby]['R_Lancelot'] != -1:
            await bot.send_message(arr_roles[i],
                                   '🟥Ланселот - ' + bd.id_to_name[bd.lobby_to_info[game_lobby]['R_Lancelot']])
    if bd.lobby_to_info[game_lobby]['R_Lancelot'] != -1 and bd.lobby_to_settings[game_lobby]['Lancelots']:
        await bot.send_message(bd.lobby_to_info[game_lobby]['B_Lancelot'],
                               '🟥Ланселот - ' + bd.id_to_name[bd.lobby_to_info[game_lobby]['R_Lancelot']])
        await bot.send_message(bd.lobby_to_info[game_lobby]['R_Lancelot'],
                               '🟦Ланселот - ' + bd.id_to_name[bd.lobby_to_info[game_lobby]['B_Lancelot']])
    await missions(game_lobby)


@dp.callback_query_handler(text='button0', state='*')
async def button0(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][0] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][0])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][0])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button1', state='*')
async def button1(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][1] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][1])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][1])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button2', state='*')
async def button2(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][2] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][2])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][2])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button3', state='*')
async def button3(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][3] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][3])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][3])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button4', state='*')
async def button4(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][4] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][4])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][4])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button5', state='*')
async def button5(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][5] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][5])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][5])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button6', state='*')
async def button6(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][6] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][6])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][6])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button7', state='*')
async def button7(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][7] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][7])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][7])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button8', state='*')
async def button8(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][8] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][8])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][8])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='button9', state='*')
async def button9(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if bd.lobby_to_info[game_lobby]['round'][9] in bd.lobby_to_info[game_lobby]['mission']:
        await message.answer('Ок, я удалил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].remove(bd.lobby_to_info[game_lobby]['round'][9])
    else:
        await message.answer('Ок, я добавил этого игрока из похода')
        bd.lobby_to_info[game_lobby]['mission'].append(bd.lobby_to_info[game_lobby]['round'][9])
    ans = 'Текущий состав похода - '
    for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
        ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
        if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
            ans += ', '
    if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
        msg = await bot.send_message(message.from_user.id, 'Состав похода пуст')
        bd.id_to_delete[message.from_user.id].append(msg)
    else:
        msg = await bot.send_message(message.from_user.id, ans)
        bd.id_to_delete[message.from_user.id].append(msg)


@dp.callback_query_handler(text='start_mis', state='*')
async def start_mis(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if (len(bd.lobby_to_info[game_lobby]['mission']) == bd.missions[len(arr_players) - 5][
        bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue']]):
        await delete_mes(message.from_user.id)
        await delete1_mes(message.from_user.id)
        ans = 'Игроки, участвующие в походе - '
        for i in range(len(bd.lobby_to_info[game_lobby]['mission'])):
            ans += str(bd.id_to_name[bd.lobby_to_info[game_lobby]['mission'][i]])
            if i < len(bd.lobby_to_info[game_lobby]['mission']) - 1:
                ans += ', '
        kb1 = InlineKeyboardMarkup()
        aye = InlineKeyboardButton('За', callback_data='aye')
        con = InlineKeyboardButton('Против', callback_data='con')
        kb1.add(aye)
        kb1.add(con)
        for i in range(len(arr_players)):
            await bot.send_message(arr_players[i], ans)
            bd.id_to_vote[arr_players[i]] = -100
            msg = await bot.send_message(arr_players[i], text='Проголосуйте за данный состав похода', reply_markup=kb1)
            bd.vote.append(arr_players[i])
            bd.id_to_delete[arr_players[i]].append(msg)
    else:
        await bot.send_message(message.from_user.id, 'Вы выбрали ' + str(
            len(bd.lobby_to_info[game_lobby]['mission'])) + ' человек, а в походе должно быть ' + str(
            bd.missions[len(arr_players) - 5][
                bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue']]) + ' человек')


@dp.callback_query_handler(text='aye', state='*')
async def aye(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if message.from_user.id in bd.vote:
        bd.vote.remove(message.from_user.id)
        await bd.lobby_to_sem[game_lobby].acquire()
        await delete_mes(message.from_user.id)
        arr_players = bd.lobby_to_info[game_lobby]['round']
        bd.id_to_vote[message.from_user.id] = 1
        sm = 0
        for i in arr_players:
            if i != message.from_user.id:
                msg = await bot.send_message(i, bd.id_to_name[message.from_user.id] + ' проголосовал')
                bd.id_to_delete1[i].append(msg)
            sm += bd.id_to_vote[i]
        bd.lobby_to_sem[game_lobby].release()
        if sm > -50:
            ay = 0
            co = 0
            for j in arr_players:
                if bd.id_to_vote[j] == 1:
                    ay += 1
                else:
                    co += 1
            for i in arr_players:
                await delete1_mes(i)
                await bot.send_message(i, bd.makar_str)
                await bot.send_message(i, 'Голоса:')
                if not bd.lobby_to_settings[game_lobby]['CloseVote']:
                    for j in arr_players:
                        if bd.id_to_vote[j] == 1:
                            await bot.send_message(i, str(bd.id_to_name[j]) + ' - за')
                        else:
                            await bot.send_message(i, str(bd.id_to_name[j]) + ' - против')
                else:
                    await bot.send_message(i, 'За - ' + str(ay) + ' человек')
                    await bot.send_message(i, 'Против - ' + str(co) + ' человек')
            if sm > 0:
                for i in arr_players:
                    await bot.send_message(i, 'Поход состоялся')
                await make_mission(game_lobby)
            else:
                bd.lobby_to_info[game_lobby]['skip'] += 1
                bd.lobby_to_info[game_lobby]['cnt'] += 1
                bd.lobby_to_info[game_lobby]['cnt'] %= len(arr_players)
                for i in arr_players:
                    await bot.send_message(i, 'Поход был пропущен')
                if bd.lobby_to_info[game_lobby]['skip'] == 5:
                    await end_game(game_lobby)
                else:
                    await missions(game_lobby)


@dp.callback_query_handler(text='con', state='*')
async def con(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    if message.from_user.id in bd.vote:
        bd.vote.remove(message.from_user.id)
        await bd.lobby_to_sem[game_lobby].acquire()
        arr_players = bd.lobby_to_info[game_lobby]['round']
        await delete_mes(message.from_user.id)
        bd.id_to_vote[message.from_user.id] = -1
        sm = 0
        for i in arr_players:
            if i != message.from_user.id:
                msg = await bot.send_message(i, bd.id_to_name[message.from_user.id] + ' проголосовал')
                bd.id_to_delete1[i].append(msg)
            sm += bd.id_to_vote[i]
        bd.lobby_to_sem[game_lobby].release()
        if sm > -50:
            ay = 0
            co = 0
            for j in arr_players:
                if bd.id_to_vote[j] == 1:
                    ay += 1
                else:
                    co += 1
            for i in arr_players:
                await delete1_mes(i)
                await bot.send_message(i, bd.makar_str)
                await bot.send_message(i, 'Голоса:')
                if not bd.lobby_to_settings[game_lobby]['CloseVote']:
                    for j in arr_players:
                        if bd.id_to_vote[j] == 1:
                            await bot.send_message(i, str(bd.id_to_name[j]) + ' - за')
                        else:
                            await bot.send_message(i, str(bd.id_to_name[j]) + ' - против')
                else:
                    await bot.send_message(i, 'За - ' + str(ay) + ' человек')
                    await bot.send_message(i, 'Против - ' + str(co) + ' человек')
            if sm > 0:
                for i in arr_players:
                    await bot.send_message(i, 'Поход состоялся')
                await make_mission(game_lobby)
            else:
                bd.lobby_to_info[game_lobby]['skip'] += 1
                bd.lobby_to_info[game_lobby]['cnt'] += 1
                bd.lobby_to_info[game_lobby]['cnt'] %= len(arr_players)
                for i in arr_players:
                    await bot.send_message(i, 'Поход был пропущен')
                if bd.lobby_to_info[game_lobby]['skip'] == 5:
                    await end_game(game_lobby)
                else:
                    await missions(game_lobby)


@dp.callback_query_handler(text='success', state='*')
async def success(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    await delete_mes(message.from_user.id)
    await bd.lobby_to_sem[game_lobby].acquire()
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.lobby_to_info[game_lobby]['mission']:
        bd.lobby_to_info[game_lobby]['mission'].remove(message.from_user.id)
        bd.lobby_to_info[game_lobby]['success'] += 1
        for i in arr_players:
            if i != message.from_user.id:
                msg = await bot.send_message(i, bd.id_to_name[message.from_user.id] + ' сделал свой выбор')
                bd.id_to_delete1[i].append(msg)
        if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
            bd.lobby_to_info[game_lobby]['cnt'] += 1
            bd.lobby_to_info[game_lobby]['cnt'] %= len(arr_players)
            for i in arr_players:
                await delete1_mes(i)
                await bot.send_message(i, bd.makar_str)
                await bot.send_message(i, 'Успехов - ' + str(bd.lobby_to_info[game_lobby]['success']))
                await bot.send_message(i, 'Провалов - ' + str(bd.lobby_to_info[game_lobby]['fail']))
            if bd.lobby_to_info[game_lobby]['fail'] > 1:
                bd.lobby_to_info[game_lobby]['colors'] += '🟥'
                for i in arr_players:
                    await bot.send_message(i, 'Поход провален')
                    await bot.send_message(i, 'Результаты походов: ' + str(bd.lobby_to_info[game_lobby]['colors']))
                bd.lobby_to_info[game_lobby]['red'] += 1
                if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                        bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                        bd.lobby_to_settings[game_lobby]['Lake_lady']:
                    await lake_lady(game_lobby)
                    return
                if bd.lobby_to_info[game_lobby]['red'] == 3:
                    bd.lobby_to_sem[game_lobby].release()
                    await end_game(game_lobby)
                else:
                    bd.lobby_to_sem[game_lobby].release()
                    await missions(game_lobby)
            elif bd.lobby_to_info[game_lobby]['fail'] == 0:
                bd.lobby_to_info[game_lobby]['colors'] += '🟦'
                for i in arr_players:
                    await bot.send_message(i, 'Поход успешен')
                    await bot.send_message(i, 'Результаты походов: ' + str(bd.lobby_to_info[game_lobby]['colors']))
                bd.lobby_to_info[game_lobby]['blue'] += 1
                if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                        bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                        bd.lobby_to_settings[game_lobby]['Lake_lady']:
                    await lake_lady(game_lobby)
                    return
                if bd.lobby_to_info[game_lobby]['blue'] == 3:
                    bd.lobby_to_sem[game_lobby].release()
                    await end_game(game_lobby)
                else:
                    bd.lobby_to_sem[game_lobby].release()
                    await missions(game_lobby)
            else:
                if len(arr_players) >= 7 and bd.lobby_to_info[game_lobby]['blue'] + bd.lobby_to_info[game_lobby][
                    'red'] == 3:
                    bd.lobby_to_info[game_lobby]['colors'] += '🟦'
                    for i in arr_players:
                        await bot.send_message(i, 'Поход успешен')
                        await bot.send_message(i, 'Результаты походов: ' + bd.lobby_to_info[game_lobby]['colors'])
                    bd.lobby_to_info[game_lobby]['blue'] += 1
                    if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                            bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                            bd.lobby_to_settings[game_lobby]['Lake_lady']:
                        await lake_lady(game_lobby)
                        return
                    if bd.lobby_to_info[game_lobby]['blue'] == 3:
                        bd.lobby_to_sem[game_lobby].release()
                        await end_game(game_lobby)
                    else:
                        bd.lobby_to_sem[game_lobby].release()
                        await missions(game_lobby)
                else:
                    bd.lobby_to_info[game_lobby]['colors'] += '🟥'
                    for i in arr_players:
                        await bot.send_message(i, 'Поход провален')
                        await bot.send_message(i, 'Результаты походов: ' + bd.lobby_to_info[game_lobby]['colors'])
                    bd.lobby_to_info[game_lobby]['red'] += 1
                    if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                            bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                            bd.lobby_to_settings[game_lobby]['Lake_lady']:
                        await lake_lady(game_lobby)
                        return
                    if bd.lobby_to_info[game_lobby]['red'] == 3:
                        bd.lobby_to_sem[game_lobby].release()
                        await end_game(game_lobby)
                    else:
                        bd.lobby_to_sem[game_lobby].release()
                        await missions(game_lobby)
        else:
            bd.lobby_to_sem[game_lobby].release()
    else:
        bd.lobby_to_sem[game_lobby].release()


@dp.callback_query_handler(text='fail', state='*')
async def fail(message: types.CallbackQuery):
    if await check_user1(message):
        return
    game_lobby = bd.id_to_lobby[message.from_user.id]
    await delete_mes(message.from_user.id)
    arr_players = bd.lobby_to_info[game_lobby]['round']
    await bd.lobby_to_sem[game_lobby].acquire()
    if message.from_user.id in bd.lobby_to_info[game_lobby]['mission']:
        bd.lobby_to_info[game_lobby]['mission'].remove(message.from_user.id)
        bd.lobby_to_info[game_lobby]['fail'] += 1
        for i in arr_players:
            if i != message.from_user.id:
                msg = await bot.send_message(i, bd.id_to_name[message.from_user.id] + ' сделал свой выбор')
                bd.id_to_delete1[i].append(msg)
        if len(bd.lobby_to_info[game_lobby]['mission']) == 0:
            bd.lobby_to_info[game_lobby]['cnt'] += 1
            bd.lobby_to_info[game_lobby]['cnt'] %= len(arr_players)
            for i in arr_players:
                await delete1_mes(i)
                await bot.send_message(i, bd.makar_str)
                await bot.send_message(i, 'Успехов - ' + str(bd.lobby_to_info[game_lobby]['success']))
                await bot.send_message(i, 'Провалов - ' + str(bd.lobby_to_info[game_lobby]['fail']))
            if bd.lobby_to_info[game_lobby]['fail'] > 1:
                bd.lobby_to_info[game_lobby]['colors'] += '🟥'
                for i in arr_players:
                    await bot.send_message(i, 'Поход провален')
                    await bot.send_message(i, 'Результаты походов: ' + str(bd.lobby_to_info[game_lobby]['colors']))
                bd.lobby_to_info[game_lobby]['red'] += 1
                if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                        bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                        bd.lobby_to_settings[game_lobby]['Lake_lady']:
                    await lake_lady(game_lobby)
                    return
                if bd.lobby_to_info[game_lobby]['red'] == 3:
                    bd.lobby_to_sem[game_lobby].release()
                    await end_game(game_lobby)
                else:
                    bd.lobby_to_sem[game_lobby].release()
                    await missions(game_lobby)
            elif bd.lobby_to_info[game_lobby]['fail'] == 0:
                bd.lobby_to_info[game_lobby]['colors'] += '🟦'
                for i in arr_players:
                    await bot.send_message(i, 'Поход успешен')
                    await bot.send_message(i, 'Результаты походов: ' + str(bd.lobby_to_info[game_lobby]['colors']))
                bd.lobby_to_info[game_lobby]['blue'] += 1
                if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                        bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                        bd.lobby_to_settings[game_lobby]['Lake_lady']:
                    await lake_lady(game_lobby)
                    return
                if bd.lobby_to_info[game_lobby]['blue'] == 3:
                    bd.lobby_to_sem[game_lobby].release()
                    await end_game(game_lobby)
                else:
                    bd.lobby_to_sem[game_lobby].release()
                    await missions(game_lobby)
            else:
                if len(arr_players) >= 7 and bd.lobby_to_info[game_lobby]['blue'] + bd.lobby_to_info[game_lobby][
                    'red'] == 3:
                    bd.lobby_to_info[game_lobby]['colors'] += '🟦'
                    for i in arr_players:
                        await bot.send_message(i, 'Поход успешен')
                        await bot.send_message(i, 'Результаты походов: ' + bd.lobby_to_info[game_lobby]['colors'])
                    bd.lobby_to_info[game_lobby]['blue'] += 1
                    if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                            bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                            bd.lobby_to_settings[game_lobby]['Lake_lady']:
                        await lake_lady(game_lobby)
                        return
                    if bd.lobby_to_info[game_lobby]['blue'] == 3:
                        bd.lobby_to_sem[game_lobby].release()
                        await end_game(game_lobby)
                    else:
                        bd.lobby_to_sem[game_lobby].release()
                        await missions(game_lobby)
                else:
                    bd.lobby_to_info[game_lobby]['colors'] += '🟥'
                    for i in arr_players:
                        await bot.send_message(i, 'Поход провален')
                        await bot.send_message(i, 'Результаты походов: ' + bd.lobby_to_info[game_lobby]['colors'])
                    bd.lobby_to_info[game_lobby]['red'] += 1
                    if bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] > 1 and \
                            bd.lobby_to_info[game_lobby]['red'] + bd.lobby_to_info[game_lobby]['blue'] < 5 and \
                            bd.lobby_to_settings[game_lobby]['Lake_lady']:
                        await lake_lady(game_lobby)
                        return
                    if bd.lobby_to_info[game_lobby]['red'] == 3:
                        bd.lobby_to_sem[game_lobby].release()
                        await end_game(game_lobby)
                    else:
                        bd.lobby_to_sem[game_lobby].release()
                        await missions(game_lobby)
        else:
            bd.lobby_to_sem[game_lobby].release()
    else:
        bd.lobby_to_sem[game_lobby].release()


@dp.callback_query_handler(text='button10', state='*')
async def button10(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[0]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[0]])
        if bd.id_to_role[arr_players[0]][1] == 'М' and bd.id_to_role[arr_players[0]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button11', state='*')
async def button11(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[1]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[1]])
        if bd.id_to_role[arr_players[1]][1] == 'М' and bd.id_to_role[arr_players[1]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button12', state='*')
async def button12(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[2]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[2]])
        if bd.id_to_role[arr_players[2]][1] == 'М' and bd.id_to_role[arr_players[2]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button13', state='*')
async def button13(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[3]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[3]])
        if bd.id_to_role[arr_players[3]][1] == 'М' and bd.id_to_role[arr_players[3]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button14', state='*')
async def button14(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[4]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[4]])
        if bd.id_to_role[arr_players[4]][1] == 'М' and bd.id_to_role[arr_players[4]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button15', state='*')
async def button15(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[5]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[5]])
        if bd.id_to_role[arr_players[5]][1] == 'М' and bd.id_to_role[arr_players[5]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button16', state='*')
async def button16(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[6]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[6]])
        if bd.id_to_role[arr_players[6]][1] == 'М' and bd.id_to_role[arr_players[6]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button17', state='*')
async def button17(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[7]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[7]])
        if bd.id_to_role[arr_players[7]][1] == 'М' and bd.id_to_role[arr_players[7]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button18', state='*')
async def button18(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[8]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[8]])
        if bd.id_to_role[arr_players[8]][1] == 'М' and bd.id_to_role[arr_players[8]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


@dp.callback_query_handler(text='button19', state='*')
async def button19(message: types.CallbackQuery):
    if await check_user1(message):
        return
    await delete_mes(message.from_user.id)
    await delete1_mes(message.from_user.id)
    game_lobby = bd.id_to_lobby[message.from_user.id]
    arr_players = bd.lobby_to_info[game_lobby]['round']
    if message.from_user.id in bd.id_in_game:
        for i in arr_players:
            await bot.send_message(i, 'Красные выстрелили в ' + bd.id_to_name[arr_players[9]] + ' и попали в ' +
                                   bd.id_to_role[arr_players[9]])
        if bd.id_to_role[arr_players[9]][1] == 'М' and bd.id_to_role[arr_players[9]][0] == '🟦':
            for i in arr_players:
                await bot.send_message(i, 'Красные победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])
        else:
            for i in arr_players:
                await bot.send_message(i, 'Синие победили')
                state = dp.current_state(user=i)
                await state.set_state(TestStates.all()[0])
                bd.id_in_game.remove(i)
            for i in arr_players:
                await bot.send_message(i, 'Роли:')
                for j in arr_players:
                    await bot.send_message(i, bd.id_to_name[j] + ' - ' + bd.id_to_role[j])


executor.start_polling(
    dp,
    skip_updates=True,
)
