from aiohttp import ClientSession
from request_db import create_person
import asyncio
from models import engine, Session, Person_SW, Base
from more_itertools import chunked

S_PERSON = 1
E_PERSON = 90
CHUNK_SIZE = 10
Q_BUFFER = 10
BASE_URL = "https://swapi.dev/api/people/"

# функция для запроса данных по конкретному URL
async def get_person(person_id):
    print('get person:', person_id)
    session = ClientSession()
    response = await session.get(BASE_URL + str(person_id))
    person = await response.json()
    print('ready:', person_id)
    await session.close()
    return [person_id, person]

# Генератор для выгрузки данных по определённому кол-ву запросов начиная с 1
async def get_people():
    for id_chunk in chunked(range(S_PERSON, E_PERSON+1), CHUNK_SIZE):
        coroutines = [get_person(i) for i in id_chunk]
        people = await asyncio.gather(*coroutines)
        for person in people:
            yield person

async def get_request_name(url):
    async with ClientSession() as session:
        response = await session.get(url)
        data_json = await response.json()
    return data_json

async def get_list_title(*list_url):
    corutines = [get_request_name(url) for url in list_url]
    list_data = await asyncio.gather(*corutines)
    list_title = [data['title'] for data in list_data]
    list_title = ", ".join(list_title)
    return list_title

async def get_list_name(*list_url):
    corutines = [get_request_name(url) for url in list_url]
    list_data = await asyncio.gather(*corutines)
    list_name = [data['name'] for data in list_data]
    list_name = ", ".join(list_name)
    return list_name

# Загрузка в БД данных персонажей
async def paste_people(*people_data):
    # запуск сессии БД
    async with Session() as session:
        people_list = []
        for person in people_data:
            try:  # добавил возможность ошибки если персонаж с ID не найден
                print('id=', person[0], type(person[0]), 'name=', person[1]['name'])
                films = await get_list_title(*person[1]['films'])
                species = await get_list_name(*person[1]['species'])
                starships = await get_list_name(*person[1]['starships'])
                vehicles = await get_list_name(*person[1]['vehicles'])
                # print(films)
                # print("species", species)
                # print('starships', starships)
                # print('vehicles', vehicles)
                new_person = Person_SW(id=person[0],
                                       birth_year=person[1]['birth_year'],
                                       eye_color=person[1]['eye_color'],
                                       films=films,
                                       gender=person[1]['gender'],
                                       hair_color=person[1]['hair_color'],
                                       height=person[1]['height'],
                                       homeworld=person[1]['homeworld'],
                                       mass=person[1]['mass'],
                                       name=person[1]['name'],
                                       skin_color=person[1]['skin_color'],
                                       species=species,
                                       starships=starships,
                                       vehicles=vehicles
                                       )
                people_list.append(new_person)
            except:
                print("Ошибка загрузки персонажа с ID:", person[0])

        session.add_all(people_list)
        await session.commit()


async def main_func():
    # Миграция в ассинхронную БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    # Создаём буфер для загрузки разом нескольких объектов в базу
    person_data_buffer = []
    async for person in get_people():
        person_data_buffer.append(person)
        if len(person_data_buffer) >= Q_BUFFER:
            asyncio.create_task(paste_people(*person_data_buffer)) # выполнение функции параллельно с другими работами
            # await paste_people(*person_data_buffer)
            person_data_buffer = []
    # Для случаев когда кратность буфера больше остатка, проверка если буфер не пустой то запустить процесс
    if person_data_buffer:
        await paste_people(*person_data_buffer)

    # Завершение задач
    tasks = set(asyncio.all_tasks())
    tasks = tasks - {asyncio.current_task()}
    for task in tasks:
        await task
    # Завершение работы с БД
    await engine.dispose()












