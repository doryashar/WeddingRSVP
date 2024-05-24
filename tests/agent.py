from src.openroute_model import OpenRouteAgent as Agent
import asyncio, logging

async def main():
    import time
    logging.basicConfig(level=logging.INFO)
    agent = Agent('Ronit')
    
    # question = "Name the planets in the solar system?"
    # question = "translate to hebrew: 'i would like to thank you, mister. you are pretty horrible'"
    # question = "write a happy birthday wish to my father, his name is ohad and he is 64 years old. he has 2 boys and a girl: Dor, Omri and Ofir. he loves swimming and hang with his wife, Sari"
    questions = [
        '!reset_history',
        'Hi! are you single?',
        'because i dont like single people',
        'אתה חושב שאני בחור יפה?',
        'do you know my name?',
        'תעיר אותי בשעה 7 בבוקר בבקשה'
    ]

    # uid = agent.start_chat('Dor', 0)
    # logging.debug('chat started')
    for question in questions:
        res = await agent.chat('0', question)
        time.sleep(5)
        logging.info(f"\nQ: {question}\nResponse: {res}")
        # await agent.chat(uid, question2)
    
if __name__ == '__main__':
    asyncio.run(main())
    