from aiogram import  Router, F , Bot
from aiogram.filters import Command
from aiogram.types import (Message, 
                           ReplyKeyboardMarkup, 
                           KeyboardButton,
                           InlineKeyboardMarkup,
                           InlineKeyboardButton,
                           CallbackQuery,
                           FSInputFile

                           )
from aiogram.fsm.context import FSMContext
from forms.user import Form
import aiohttp, aiosqlite ,os, asyncio


#===================================================================
router = Router()
subscribers = set()

DB_NAME = "myapp.sql"

async def notifier(bot :Bot):
    while True:
        if subscribers:
            for user_id in list(subscribers):
                try:
                    await bot.send_message(user_id, "you got new notification")
                except Exception:
                    pass
        await asyncio.sleep(10)
                    
                    

async def init_db():
    print(f"Инициализация базы данных по пути: {DB_NAME}") # Добавим принты для проверки
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, 
            full_name TEXT,
            age INTEGER,
            email TEXT,
            user_id INTEGER
        )
        """)
        await db.commit()
    print("Таблица users проверена/создана.")

async def add_user(name, age, email, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users(full_name, age, email, user_id) VALUES(?,?,?,?)", (name, age, email, user_id))
        await db.commit()

async def get_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT full_name, age, email, user_id FROM users")
        result = await cursor.fetchall()
        return result
    





async def get_product(product_id):
    print("Fetching product data...")
    url = f"https://fakestoreapi.com//products/{product_id}"
    print("Fetching product data2...")
    async with aiohttp.ClientSession() as session:
        print("Fetching product data3...")
        async with session.get(url) as resp:
            print("Fetching product data4...")
            if resp.status == 404:
                print("Fetching product data5...")
                return None
            else:
                print("Fetching product data6...")
                print(f"Response status: {resp.status}")
                print(resp)
                data = await resp.json()
                print(f"Product data received: {data}")
            return data

#===================================================================
@router.message(F.text.lower() == "start")    
@router.message(Command("start"))
async def start(message : Message, state : FSMContext):
    await init_db()
    print("DB Created")
    await message.answer("Lets start! \nEnter your name:")
    print(f"form started by user: {message.from_user.id}")
    await state.set_state(Form.name)

@router.message(Command("help"))
@router.message(F.text.lower() == "help")
async def help(message : Message):
    await message.answer(
        "Comands:\n/start - start bot(form)\n/help - comands list\n/about - information about bot \n"
        "/cancel - cancel form\n/mydata - show your data\n/file - get interesting file" 
        "\n/productNum - choose product id\n/product [id] - get information about product with this id\n"
        "/reg [age] - register in DB with your age\n/users - get all users from DB\n"
        "/subscribe - subscribe to notifications\n/unsubscribe - unsubscribe from notifications\n/subs - subscribers list", 

        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard())

@router.message(Command("subscribe"))
async def subscribe(message : Message):
    user_id = message.from_user.id
    subscribers.add(user_id)
    await message.answer("You subscribed!!!")

@router.message(Command("unsubscribe"))
async def unsubscribe(message : Message):
    user_id = message.from_user.id
    subscribers.discard(user_id)
    await message.answer("You unsubscribed:()")

@router.message(Command("subs"))
async def subs(message : Message):
    if not subscribers:
        await message.answer("No subscribers yet!")
        return
    text = "SUbscribers:\n\n"
    for users in subscribers:
        text += f"{users}\n"
    await message.answer(text)

@router.message(Command("reg"))
async def register(message : Message):
    parts = message.text.strip().split()
    if len(parts) !=3 or not parts[1].isdigit() or "@" not in parts[2] or "." not in parts[2]:
        await message.answer("Invalid format! \nTry again (for example: /reg 21(your age) youremail@example.com)")
        return
    await add_user(message.from_user.full_name, int(parts[1]), parts[2], message.from_user.id)
    await message.answer("you registered successfully!")

@router.message(Command("users"))
async def users(message : Message):
    usersd = await get_users()
    print("users received")
    if not usersd:
        await message.answer("No users in DB")
        return
    text = "Users in DB:\n\n"
    for full_name, age, email, user_id in usersd:
        text += f"Name: {full_name} - <code>{age}</code>\n<b>{email}</b> - user id: <code>{user_id}</code>\n\n"

    await message.answer(text , parse_mode="HTML")

    

@router.message(Command("productNum"))
async def get_product_num(message : Message):
    await message.answer("Enter product ID \nFor example: /product 1")

@router.message(Command("product"))
async def get_product_info(message : Message):
    text = message.text.strip()
    message_parts = text.split(" ")
    if len(message_parts) != 2 or not message_parts[1].isdigit():
        await message.answer("inwalid format! \n Try again( for example: /product 1): ")
        return
    product_id = message_parts[1]
    if not product_id.isdigit():
        await message.answer("Product ID must be a number! \nTry again( for example: /product 1): ")
        return
    await message.answer(f"Serching for product {product_id}...")

    try:
        product = await get_product(int(product_id))
        print("Product data fetched successfully")
    except Exception:
        await message.answer("An error occurred while connecting to srver")
        print(Exception)
        return
    if product is None:
        await message.answer("Product not found! \nTry again( for example: /product 1): ")
        return

    title = product.get("title", "No title")
    price = product.get("price", " - ")
    desc = product.get("description", "No description")
    category =  product.get("category", "No category")
    image_url = product.get("image")
    photo = FSInputFile("backgroundgreen.jpg")

    product_info = f"<b>{title}</b>\nPrice: ${price}\nCategory: {category}\n{desc}"  

    ##if image_url:
    ##    await message.answer_photo(image_url, caption=product_info, parse_mode="HTML")
    ##else:
    await message.answer_photo(photo = photo, caption=product_info, parse_mode="HTML")




    
@router.message(Command("cancel"))
async def cancel(message : Message, state : FSMContext):
    await state.clear()
    await message.answer("Form canceled! \nIf you want to start again, use /start")



    
@router.message(Command("about"))
@router.message(F.text.lower() == "about")
async def about(message : Message):
    await message.answer(f"this just chill bot brither, dont care, {message.from_user.first_name}", reply_markup = get_main_inline_keyboard())
    print("inline keyboard sent")

@router.message(Command("mydata"))
async def mydata(message : Message, state : FSMContext):
    users = await get_users()
    text = "your data:\n"
    for full_name, age, email, user_id in users:
        if user_id == message.from_user.id:
            text += f"Name: {full_name} - <code>{age}</code>\n<b>{email}</b> - user id: <code>{user_id}</code>"
    await message.answer(text, parse_mode="HTML")


@router.message(Form.name, F.text)
async def process_name(message : Message, state : FSMContext):
    await state.update_data(name = message.text)

    await message.answer("Nice! \nNow enter your age:")
    await state.set_state(Form.age)

@router.message(Form.age, F.text)
async def process_age(message : Message, state : FSMContext):
    if not message.text.isdigit():
        await message.answer("Age must be a number! \nTry again:")
        return
    if int(message.text) < 0 or int(message.text) > 130:
        await message.answer("Age must be a positive number! \nTry again:")
        return
    
    await state.update_data(age = int(message.text))

    await message.answer("Very good! \nNow enter your email:")
    await state.set_state(Form.email)

@router.message(Form.email, F.text)
async def process_email(message : Message, state : FSMContext):
    email_text = message.text
    if "@" and "." not in email_text:
        await message.answer("Invalid email format! \nTry again:")
        return
    await state.update_data(email = email_text)

    await message.answer("Very good! \nNow enter your ID:")
    await state.set_state(Form.id)

@router.message(Form.id, F.text)
async def process_id(message : Message, state : FSMContext):
    if not message.text.isdigit():
        await message.answer("ID must be a number! \nTry again:")
        return
    print("digit check passed")
    if len(message.text) != 9:
        await message.answer("Id must include 9 digits! \nTry again:")
        return
    print("9 check passed")

    await state.update_data(id = message.text)
    print("id save passed")

    
    data = await state.get_data()
    name = data["name"]
    id = data["id"]
    age = data["age"]
    email = data["email"]

    await add_user( message.from_user.full_name, age, email, message.from_user.id)
    
    await message.answer(f"Perfect! \nYou finish the form! \nYour name: {name}\nYour age: {age}\nYour email: {email}\nYour ID: {id}")
    await state.clear()
    print(f"form finished by user: {message.from_user.id}")
    

def get_main_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="About")],
            [KeyboardButton(text="Help"), KeyboardButton(text="Start")]
            ],
            resize_keyboard=True
    )
    return keyboard

def get_main_inline_keyboard():
    keyboard2 = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="Open site", url="https://docs.google.com/document/d/1rl5vfZboKApL1CNuQnG78xen7TDdhWAkEfSJM7QrC0E/edit?tab=t.0")],
            [InlineKeyboardButton(text="Help", callback_data="help"), InlineKeyboardButton(text="More", callback_data="more")]
        ]
    )
    return keyboard2
    

@router.callback_query(lambda c: c.data == "more")
async def Proccess_more(callback : CallbackQuery):
    await callback.message.answer("to be honest, i dont know what to write here, so just chill and wait for updates")
    await callback.answer() # чтобы убрать "часики" на кнопке после нажатия

@router.callback_query(lambda c: c.data == "help")
async def Proccess_help(callback : CallbackQuery):
    await callback.message.answer("i will help you next time)")
    await callback.answer() # чтобы убрать "часики" на кнопке после нажатия




@router.message(F.photo)
async def proccess_photo(message : Message):
    photo2 = message.photo[-1]
    file_id = photo2.file_id
    print("photo received")

    await message.answer(
        f"Nice photo! \n File ID: <code>{file_id}</code>",
        parse_mode="HTML"
    )

    await message.answer_photo(file_id , caption = "Here is your photo back!")
    print("photo sent back")


@router.message(F.video)
async def proccess_video(message : Message):
    video2 = message.video
    file_id = video2.file_id
    duration = video2.duration
    print("video received")

    await message.answer(
        f"Nice video! \nFile ID: <code>{file_id}</code>\nDuration: {duration}s",
        parse_mode="HTML"
    )

    await message.answer_video(file_id , caption = "Here is your video back!")
    print("video sent back")

@router.message(F.animation)
async def proccess_anim(message : Message):
    animation2 = message.animation
    print("anim received")

    await message.answer(
        f"Nice animation! \nFile ID: <code>{animation2.file_id}</code>",
        parse_mode="HTML"
    )

    await message.answer_animation(animation2.file_id , caption = "Here is your animation back!")
    print("anim sent back")

@router.message(F.document)
async def proccess_doc(message : Message, bot : Bot):
    document2 = message.document
    file_id = document2.file_id

    file =  await bot.get_file(file_id)
    file_path = file.file_path
    local_path = f'downloads/{document2.file_name}'
    print("document received")

    await bot.download_file(file_path=file_path, destination=local_path)

    await message.answer(f"Your document {document2.file_name} has been downloaded ")
    print(f"document {document2.file_name} downloaded")


@router.message(Command("file"))
async def send_file( message : Message):
    file = FSInputFile('files/example.txt')
    await message.answer_document(file, caption="Here is your file!")
    print("file sent")














@router.message()
async def nocomand(message : Message):
    await message.answer(
        f"<b>{message.from_user.full_name}</b>?\n there is no such command: {message.text} <i>here</i>,\ntry /help",
        parse_mode="HTML"
         )

